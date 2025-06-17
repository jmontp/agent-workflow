# User Profile Context: Solo Engineer → Technical Orchestrator

## 1. Persona Snapshot
* **Name (alias):** Solo-Engineer-Manager (SEM)
* **Current Role:** Senior individual contributor owning several products across personal and client repos.
* **Aspired Role:** Technical orchestrator who delegates low-level implementation to specialist AI agents while focusing on architecture, product direction, and quality.
* **Daily Time Budget:** ≤ 2 hrs deep focus + adhoc reviews.
* **Preferred Communication:** Concise, decision-ready summaries; markdown tables over long prose; mermaid diagrams for flows.

---

## 2. Core Goals
1. **Strategic Alignment** – Spend ≥ 70 % of effort on roadmap definition, architecture, and cross-project coherence.
2. **Quality Gateway** – Establish rock-solid automated tests & CI so that merged code is production-ready with minimal manual QA.
3. **Throughput, not Tickets** – Keep WIP ≤ 2 concurrent initiatives per project; finish before starting new work.
4. **Knowledge Scaling** – Capture design decisions & ADRs once, reuse across projects.

---

## 3. Decision Boundaries (What the Agents Decide vs. What SEM Decides)
| Area | AI Agents Own | SEM Retains |
| --- | --- | --- |
| Task decomposition | Break story → tasks; propose PR titles | Approve sprint scope |
| Implementation | Write & refactor code/tests | Approve architecture-significant changes |
| Debug loop | ≤ 3 autonomous attempts | Guide after repeated failure |
| Documentation | Tech/User docs generation | Final voice & tone check |
| Release | Draft releases, changelogs | Hit publish button |

Agents should escalate when:
* CI fails 3× consecutively
* Architectural decision alters public contracts
* Security-sensitive code is touched

---

## 4. Workflow Principles
1. **Trunk-Based Development** with short-lived feature branches.
2. **TDD First**: tests precede production code.
3. **Continuous Deployment** gated by green CI.
4. **Automated Linters & Formatters** enforce style; no manual reviews for cosmetics.
5. **Backlog ≠ Dumping Ground**: every item must map to a quarterly objective.

---

## 5. Key Performance Indicators
* PR cycle time ≤ 1 day.
* Mean time-to-restore (failing main) < 30 min.
* Test coverage ≥ 90 % critical paths.
* Zero P1 bugs escaping to production per quarter.

---

## 6. Tooling & Integrations
* **Version Control:** GitHub.
* **CI/CD:** GitHub Actions.
* **Issue Tracking:** GitHub Projects, epics → features → stories.
* **Communication:** Discord bot (#orchestrator) for agent updates.
* **Observability:** Sentry + Prometheus (planned).

---

## 7. Preferred Output Formats for Agents
* Status updates: `📈 Sprint X – 3/5 tasks done, ETA: 2 days`.
* Decisions needed: `⚠️ Decision – PR #42 alters auth schema. Approve?`.
* Reports: Markdown bullet lists; diagrams in Mermaid.

---

_This profile should be loaded at orchestration start-up so every specialist agent inherits the same context & escalation rules._ 