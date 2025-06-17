# HITL Commands – Research-Mode AI Agent Scrum

_Optimized for a solo product-owner/engineer who wants minimal ceremony and maximum momentum._

---

## Command Quick-Reference

| Verb Group | Syntax | Purpose |
| ---------- | ------ | ------- |
| **/epic** | `/epic "<description>"` | Define a new high-level initiative. |
| **/approve** | `/approve [ID ...]` | Approve proposed stories or epics so they can enter a sprint. |
| **/sprint** | `/sprint plan [ID ...]` – plan next sprint<br>`/sprint start` – kick off planned sprint<br>`/sprint status` – progress snapshot<br>`/sprint pause` – halt agent work<br>`/sprint resume` – continue paused sprint | Single verb for all sprint administration. |
| **/backlog** | `/backlog view product \| sprint` – list items<br>`/backlog view <ITEM_ID>` – show full item details<br>`/backlog add_story "<desc>" --feature <FEATURE_ID>` – create story<br>`/backlog remove <ITEM_ID>` – delete item<br>`/backlog prioritize <STORY_ID> <top|high|med|low>` | Manage product & sprint backlog without leaving GitHub Projects. |
| **/request_changes** | `/request_changes "<description>"` | Used on a PR to demand modifications. |
| **/suggest_fix** | `/suggest_fix "<description>"` | Give the Code Agent a hint when stuck. |
| **/skip_task** | `/skip_task` | Abandon the currently blocked task and move on. |
| **/feedback** | `/feedback "<description>"` | General improvement notes after a sprint. |

---

## Examples

### 1. Strategic Planning
```bash
/epic "Build a modular authentication system"
```
> Orchestrator returns proposed stories `AUTH-1`, `AUTH-2`.

```bash
/approve AUTH-1 AUTH-2
```

### 2. Sprint Lifecycle
```bash
/sprint plan AUTH-1 AUTH-2
/sprint start
```

At any time:
```bash
/sprint status
/sprint pause   # emergency halt
/sprint resume  # continue work
```

### 3. Backlog Grooming
```bash
/backlog view product
/backlog add_story "As a user I can reset my password" --feature AUTH
/backlog prioritize AUTH-3 high
```

### 4. Review & Debug
```bash
/request_changes "Add duplicate-email guard in registration API"
/suggest_fix "Database URL is wrong in config.py"
/skip_task   # after three failed CI attempts
```

---

## Escalation Policy (Research Mode)
1. The Orchestrator escalates after **three consecutive CI failures**.
2. Security-critical code requires explicit human approval.
3. Agents time-box tasks to **30 min**; longer tasks trigger a status ping.

_This lightweight command set keeps you focused on big-picture direction while agents handle the details._ 