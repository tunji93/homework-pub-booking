# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

In my local Exercise 7 execution context under session directory `sess_a4e4452e1833`, the planner dynamically produced subgoal `sg_2` titled "commit the booking under policy rules" with its `assigned_half` field explicitly bound to "structured". The semantic signal that drove this architectural decision was the incoming task text naming a deterministic operational constraint: "under policy rules". The sovereign-agent framework's DefaultPlanner engine is natively prompted with an internal schema listing all available execution halves alongside their intended systemic boundaries. When a subgoal description explicitly addresses deterministic vectors like rules, policies, caps, or mathematical thresholds, the planner automatically shifts assignment from the open loop to the structured state machine. 

This routing decision is entirely advisory rather than physical. The orchestrator respects and resolves this handoff track only because both execution halves are explicitly wired together inside the parent bridge module. If only a loop half existed natively in the configuration layout, a subgoal assigned to a structured track would route directly to a dead end, replicating failure mode #4 from the lecture specifications. The broader architectural lesson here is that the planner makes vital execution routing choices based entirely on prose interpretation. To stabilize production environments, hard business constraints must be locked inside the structured half's Python boundaries where prose ambiguity can no longer induce non-deterministic mis-assignment risks.

### Citation

- sessions/sess_a4e4452e1833/logs/tickets/tk_ca924142_planner_plan.json — raw planner reasoning output schema.
- sessions/sess_a4e4452e1833/logs/trace.jsonl — runtime event state telemetry logging the state change transition.

---

## Q2 — Dataflow integrity catch

### Your answer

During my local development lifecycle for Exercise 5 within session directory `sess_4bdf1107cb57`, the automated dataflow integrity check caught a subtle LLM data fabrication that manual human code review completely missed. The generated flyer document embedded within the workspace workspace directory claimed a "Total Cost: £560" and a "Deposit Required: £112". On a fast visual skim, these figures appeared highly plausible because they cleanly followed the superficial 20% deposit multiplier rule specified for intermediate cost thresholds in our underlying configuration fixtures. 

However, running the validation suite caused `verify_dataflow` to fail, returning an `ok=False` status paired with `unverified_facts=['£560', '£112']`. Cross-referencing the underlying transaction logs revealed that `calculate_cost` had actually returned a ground-truth `total_gbp=540` and a `deposit_required_gbp=0`. Because the real mathematical total fell below the strict £300 commercial floor, no deposit was actually required by the backend system. The model had autonomously fabricated a plausible corporate transaction calculation that looked completely correct in prose context but was completely detached from the upstream tool output. The check caught this because it enforces strict equality checks against the immutable records logged inside `_TOOL_CALL_LOG`. The engineering takeaway is that validation layers must never verify data based on contextual reasonableness; they must mathematically map every assertion back to an authenticated transaction origin.

### Citation

- sessions/sess_4bdf1107cb57/workspace/flyer.html — the fabricated prose document block containing unverified financial claims.
- sessions/sess_4bdf1107cb57/logs/trace.jsonl — tool call transaction records showing the true values returned by `calculate_cost`.

---

## Q3 — Removing one framework primitive

### Your answer

If forced to isolate and retain exactly one core primitive from the sovereign-agent framework while deprecating the rest, the **Session Directory** is the most indispensable asset. While architectural patterns like tickets, forward-only state machines, and atomic-rename IPC files provide operational value, they all depend on an isolated filesystem foundation to maintain state sanity. 

Losing the Session Directory primitive exposes production environments to the catastrophic failure mode of **Cross-Tenant Data Leakage**. In a high-throughput commercial environment processing hundreds of concurrent pub bookings, removing isolated session directories forces the agent runtime to dump application traces, filesystem writes, and intermediate tool outputs into a shared, global directory space. If multiple execution loops execute concurrently, a parallel agent writing to a shared file path like `workspace/flyer.html` will destructively overwrite or leak sensitive commercial terms belonging to a completely separate customer session. 

Furthermore, diagnosing multi-process orchestration errors changes from an intuitive inspection of a single session folder into a complex database forensic operation across disorganized log streams. As emphasized in the core design literature, session directories function precisely like Git commits; they serve as the atomic foundation of truth upon which complex state routing, error isolation, and operational metrics are built. Reconstructing system truth from a unified session directory is straightforward, but reconstructing lost session isolation from a global log pool is impossible.

### Citation

- sessions/sess_4bdf1107cb57/ — isolated directory structure separating execution runtime environments.
- starter/edinburgh_research/tools.py — reliance on the passed framework Session instance object to resolve unique workspace folder targets.