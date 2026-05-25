# Ex5 — Edinburgh research loop scenario

## Your answer

The planner produced two specific subgoals: sg_1 (research venues near Haymarket for a party of 6, assigned to loop orchestration) and sg_2 (produce a customer flyer compiling the chosen venue data, weather parameters, and cost analysis, also assigned to loop). Both goals successfully executed within the context of a single unified executor session.

During Turn 1, the agent dispatched parallelized invocations of venue_search, get_weather, and calculate_cost. These are explicitly designated as parallel_safe=True in our `build_tool_registry` because they strictly read from isolated static fixtures via `_SAMPLE_DATA` and contain zero side effects. Turn 2 initiated generate_flyer via an internal `_flyer_adapter(event_details)` wrapper. This tool must be declared with parallel_safe=False because it executes a destructive file write operation directly onto the workspace filesystem. Finally, Turn 3 evaluated the accumulated context and safely terminated execution via complete_task.

The framework's dataflow integrity check proved critical during our local development lifecycle by highlighting two prominent failure points:
1. Dynamic Runtime Environments: Initially, our file-writing path inside generate_flyer was hardcoded to a local static 'workspace/' folder. The integrity checker caught an exit error because the test suite spins up isolated, transient directory structures. Correcting this required dynamically mapping paths from the passed framework Session instance checking for `session.workspace_dir` or falling back to `session.dir / 'workspace'`.
2. Mathematical Precision: In calculate_cost, values like total cost and service charges calculate as floats (e.g., £356.40 for Haymarket Tap). To satisfy strict commercial thresholds without rounding down and shortchanging minimum spends, we applied `math.ceil()` to force clean integer conversion (`total_gbp` and `deposit_required_gbp`), which seamlessly cleared the automated integrity checks.

By strictly enforcing that all numeric figures embedded in the final HTML layout cleanly align with records in `_TOOL_CALL_LOG` via `record_tool_call`, the dataflow integrity check effectively guarantees that the LLM engine cannot forge or hallucinate commercial terms or cost breakdowns.

## Citations

- starter/edinburgh_research/tools.py — tool registrations and `parallel_safe` configuration registry flags.
- sample_data/venues.json & sample_data/weather.json — immutable underlying data fixtures.
- sample_data/catering.json — financial multiplier thresholds fixture.
- sessions/sess_4bdf1107cb57/logs/trace.jsonl — authentic local tool execution record log.
- sessions/sess_4bdf1107cb57/workspace/flyer.html — the validated structural document card output.