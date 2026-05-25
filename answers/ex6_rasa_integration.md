# Ex6 — Rasa structured half

## Your answer

The RasaStructuredHalf subclass overrides run() to POST a booking intent to Rasa's REST webhook and interpret the response. The input payload pipeline is tightly coupled across modules: the open loop half produces raw booking telemetry data, and the StructuredHalf immediately triggers normalise_booking_payload (via validator.py) to map variables into a Rasa-shaped message string with clean canonical types. This is dispatched via a urllib POST request to the live Rasa server, which is subsequently parsed for explicit custom response slots indicating either {action: committed} or {action: rejected}.

While the local offline grader spawns a lightweight standard library http.server thread mock on port :5905 that mirrors the REST webhook contract for automated test isolation, our tier-2 live integration validation verified the system under a true multi-process distributed architecture. This required orchestrating three explicit network entities side-by-side:
1. Terminal 1 (make rasa-actions): Running the custom Python Action Server on port :5055 to validate state boundaries.
2. Terminal 2 (make rasa-serve): Running the primary core Rasa CALM dialogue core engine on port :5005.
3. Terminal 3 (make ex6-real): Driving the client agent context.

Three critical design choices stabilize this architecture:
1. Boundary Exception Isolation: We explicitly raise ValidationFailed inside normalise_booking_payload and catch it gracefully within run() instead of letting it crash the runtime. The StructuredHalf contract demands a clean HalfResult return value.
2. Network Resilience: External network timeouts or connection drops capture a success=False state paired with an explicit SA_EXT_SERVICE_UNAVAILABLE error flag, passing control back to the caller to manage retry logic back-offs.
3. Consistent Conversational Memory: The sender_id tracking handle is dynamically established as a stable hash of (venue + date + time). This guarantees that the Rasa session tracker entity mapping remains perfectly consistent and continuous across multiple retries within a single execution session.

## Citations

- starter/rasa_half/validator.py — normalise_booking_payload field cleaning rules.
- starter/rasa_half/structured_half.py — RasaStructuredHalf.run code implementation + fallback handlers.
- sessions/sess_0d996a927d5e/logs/trace.jsonl — offline standard library mock response payload logs.
- sessions/sess_ac5c02aac0d6/logs/trace.jsonl — live distributed microservice network execution trace.