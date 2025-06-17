#!/usr/bin/env python3
"""
scaffold_hybrid.py
Extend an existing agent-workflow repo with:
• Orchestrator algorithm (hybrid AI + HITL approvals)
• Four role agent stubs
• Slack & WhatsApp interface code
• CI extension + Makefile
"""
import os, subprocess, textwrap, json, yaml, sys
from pathlib import Path

ROOT = Path(".").resolve()
assert (ROOT / "agents").exists(), "Run inside agent-workflow repo root!"

def sh(cmd, **kw): subprocess.check_call(cmd, shell=True, **kw)
def write(file: Path, txt: str, mode="w"):
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(textwrap.dedent(txt).strip() + "\n")

# ------------------------------------------------------------------ #
# 1. Core orchestrator algorithm
# ------------------------------------------------------------------ #
write(ROOT/"orchestrator.py", r"""
import asyncio, json, yaml, os
from pathlib import Path
from datetime import datetime
from agents import registry          # simple import map
from interfaces.slack_bot import slack_notify, register_button_handler
from interfaces.whatsapp_bot import whatsapp_notify, register_whatsapp_handler

STATE_DIR = Path(".orch-state"); STATE_DIR.mkdir(exist_ok=True)

class Orchestrator:
    def __init__(self, cfg_path="config/projects.yaml"):
        self.cfg  = yaml.safe_load(open(cfg_path))
        self.agents = {name: cls() for name, cls in registry.items()}

    # ---------- public API ----------
    async def handle_human_msg(self, text, user, channel):
        """
        Slack @mention or WhatsApp DM lands here.
        Parse simple commands:
          status?          - summary
          plan <project>   - regenerate plan
          approve <id>     - unblock queued task
        """
        if text.startswith("approve"):
            tid = text.split(maxsplit=1)[1].strip()
            self._unblock_task(tid, approved=True, user=user)
            return f"Task {tid} approved ✅"
        if text.startswith("deny"):
            tid = text.split(maxsplit=1)[1].strip()
            self._unblock_task(tid, approved=False, user=user)
            return f"Task {tid} denied ❌"
        return self.status()

    async def run(self):
        """Main event loop - iterate over projects, dispatch tasks."""
        while True:
            for proj in self.cfg["projects"]:
                await self._reconcile_project(proj)
            await asyncio.sleep(5)  # crude scheduler; replace w/ APScheduler

    # ---------- internals ----------
    async def _reconcile_project(self, proj):
        path = Path("../")/proj["name"]
        state_file = path/".orch-state/status.json"
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
        # Example: one hard-coded task per project until you add planning
        if not state.get("hello-world"):
            task = {"id": "hello-world",
                    "role": "DesignAgent",
                    "cmd": "Write README skeleton",
                    "requires": proj["orchestration"]}
            await self._dispatch(task, proj, state_file, state)

    async def _dispatch(self, task, proj, state_file, state):
        role = task["role"]; agent = self.agents[role]
        needs = task["requires"]
        if needs == "blocking":
            tid = task["id"]; self._queue_blocker(tid, task, state_file, state)
            msg = f"*{proj['name']}* queued *{tid}* - waiting for approval."
            slack_notify(msg); whatsapp_notify(msg)
        elif needs == "partial":
            # run but quarantine output
            result = await agent.run(task["cmd"], dry=True)
            self._stash_result(task["id"], proj, result)
        else:
            await agent.run(task["cmd"])
            state[task["id"]] = {"done": True, "at": str(datetime.utcnow())}
            state_file.write_text(json.dumps(state, indent=2))

    def _queue_blocker(self, tid, task, state_file, state):
        state[tid] = {"queued": task, "done": False}
        state_file.write_text(json.dumps(state, indent=2))

    def _unblock_task(self, tid, approved, user):
        for proj in self.cfg["projects"]:
            sf = Path("../")/proj["name"]/".orch-state/status.json"
            if not sf.exists(): continue
            st = json.loads(sf.read_text())
            if tid in st and not st[tid]["done"]:
                if approved:
                    role = st[tid]["queued"]["role"]
                    agent = self.agents[role]
                    asyncio.create_task(agent.run(st[tid]["queued"]["cmd"]))
                    st[tid]["done"] = True; st[tid]["by"] = user
                    msg = f"{tid} approved by <@{user}>; executing."
                    slack_notify(msg); whatsapp_notify(msg)
                else:
                    st.pop(tid)
                sf.write_text(json.dumps(st, indent=2))

    def status(self):
        return "🔄 Orchestrator alive with agents: " + ", ".join(self.agents)
""")

# ------------------------------------------------------------------ #
# 2. Agent registry & stubs
# ------------------------------------------------------------------ #
write(ROOT/"agents/__init__.py", r"""
class BaseAgent:
    async def run(self, cmd: str, dry=False):
        # TODO: replace with Anthropic client; for now, echo ↓
        print(f"[{self.__class__.__name__}] {cmd} (dry={dry})")
        return f"Result of: {cmd}"

from .design_agent   import DesignAgent
from .code_agent     import CodeAgent
from .data_agent     import DataAgent
from .qa_agent       import QAAgent

registry = {
    "DesignAgent": DesignAgent,
    "CodeAgent":   CodeAgent,
    "DataAgent":   DataAgent,
    "QAAgent":     QAAgent,
}
""")

for role in ["design_agent", "code_agent", "data_agent", "qa_agent"]:
    write(ROOT/f"agents/{role}.py", rf"""
from . import BaseAgent
class {''.join(part.title() for part in role.split('_')[:-1])}Agent(BaseAgent):
    \"\"\"{role.replace('_', ' ').title()} - specialised SOP from MetaGPT / ChatDev.\"\"\"
""")

# ------------------------------------------------------------------ #
# 3. Slack & WhatsApp bots
# ------------------------------------------------------------------ #
write(ROOT/"interfaces/slack_bot.py", r"""
import os, asyncio
from slack_bolt.async_app import AsyncApp
from orchestrator import Orchestrator

orch = Orchestrator()
app = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN"),
               app_token=os.getenv("SLACK_APP_TOKEN"))

@app.event("app_mention")
async def mention(ev, say):
    resp = await orch.handle_human_msg(ev["text"], ev["user"], ev["channel"])
    await say(resp)

def slack_notify(msg): asyncio.create_task(app.client.chat_postMessage(
        channel=os.getenv("SLACK_CHANNEL", "#general"), text=msg))

def register_button_handler(): pass   # TODO for Block Kit Approve / Deny
""")

write(ROOT/"interfaces/whatsapp_bot.py", r"""
import os, asyncio
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from orchestrator import Orchestrator

orch = Orchestrator(); app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.values.get("Body", "").strip()
    user = request.values.get("From", "")
    loop = asyncio.get_event_loop()
    resp_txt = loop.run_until_complete(orch.handle_human_msg(body, user, "whatsapp"))
    twiml = MessagingResponse(); twiml.message(resp_txt); return str(twiml)

def whatsapp_notify(msg): pass
def register_whatsapp_handler(): pass  # resolved in Flask route above
""")

# ------------------------------------------------------------------ #
# 4. CI / Makefile refresh
# ------------------------------------------------------------------ #
ci_content = Path(ROOT/".github/workflows/ci.yml").read_text()
ci_content += """
  deploy:
    runs-on: [self-hosted, orchestrator]
    steps:
      - uses: actions/checkout@v4
      - run: make run
"""
Path(ROOT/".github/workflows/ci.yml").write_text(ci_content)

write(ROOT/"Makefile", r"""
run:
\tpython -c "import asyncio, orchestrator; asyncio.run(orchestrator.Orchestrator().run())"
""")

# ------------------------------------------------------------------ #
# 5. Bump requirements & commit
# ------------------------------------------------------------------ #
req = Path("requirements.txt").read_text().splitlines()
for pkg in ("anthropic", "slack_bolt", "twilio", "pyyaml"):
    if pkg not in req: req.append(pkg)
Path("requirements.txt").write_text("\n".join(req)+"\n")

sh("git add .")
sh('git commit -m "scaffold hybrid AI orchestrator + HITL"', cwd=".")

if os.getenv("CREATE_REMOTE","").lower() in ("1","true"):
    sh("git push", cwd=".")
print("✅ Hybrid scaffolding done.  Run `make run` to start!")

