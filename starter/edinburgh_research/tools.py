"""Ex5 tools. Four tools the agent uses to research an Edinburgh booking.

Each tool:
  1. Reads its fixture from sample_data/ (DO NOT modify the fixtures).
  2. Logs its arguments and output into _TOOL_CALL_LOG (see integrity.py).
  3. Returns a ToolResult with success=True/False, output=dict, summary=str.

The grader checks for:
  * Correct parallel_safe flags (reads True, generate_flyer False).
  * Every tool's results appear in _TOOL_CALL_LOG.
  * Tools fail gracefully on missing fixtures or bad inputs (ToolError,
    not RuntimeError).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolError, ToolRegistry, ToolResult, _RegisteredTool

from .integrity import record_tool_call

_SAMPLE_DATA = Path(__file__).parent / "sample_data"


# ---------------------------------------------------------------------------
# TODO 1 — venue_search
# ---------------------------------------------------------------------------
def venue_search(near: str, party_size: int, budget_max_gbp: int = 1000) -> ToolResult:
    """Search for Edinburgh venues near <near> that can seat the party.

    Reads sample_data/venues.json. Filters by:
      * open_now == True
      * area contains <near> (case-insensitive substring match)
      * seats_available_evening >= party_size
      * hire_fee_gbp + min_spend_gbp <= budget_max_gbp
    """
    venues_file = _SAMPLE_DATA / "venues.json"

    if not venues_file.exists():
        raise ToolError("SA_TOOL_DEPENDENCY_MISSING: venues.json not found.")

    with open(venues_file, encoding="utf-8") as f:
        venues = json.load(f)

    results = []
    search_near = near.lower()

    for venue in venues:
        if not venue.get("open_now", False):
            continue
        if search_near not in venue.get("area", "").lower():
            continue
        if venue.get("seats_available_evening", 0) < party_size:
            continue

        total_cost_threshold = venue.get("hire_fee_gbp", 0) + venue.get("min_spend_gbp", 0)
        if total_cost_threshold > budget_max_gbp:
            continue

        results.append(venue)

    output = {"near": near, "party_size": party_size, "results": results, "count": len(results)}

    summary = f"venue_search({near}, party={party_size}): {len(results)} result(s)"
    record_tool_call(
        "venue_search",
        {"near": near, "party_size": party_size, "budget_max_gbp": budget_max_gbp},
        output,
    )

    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 2 — get_weather
# ---------------------------------------------------------------------------
def get_weather(city: str, date: str) -> ToolResult:
    """Look up the scripted weather for <city> on <date> (YYYY-MM-DD)."""
    weather_file = _SAMPLE_DATA / "weather.json"

    if not weather_file.exists():
        raise ToolError("SA_TOOL_DEPENDENCY_MISSING: weather.json not found.")

    with open(weather_file, encoding="utf-8") as f:
        weather_data = json.load(f)

    search_city = city.lower()

    matched_city_key = None
    for k in weather_data.keys():
        if k.lower() == search_city:
            matched_city_key = k
            break

    if not matched_city_key or date not in weather_data[matched_city_key]:
        error_output = {
            "error": f"SA_TOOL_INVALID_INPUT: Weather data not found for {city} on {date}."
        }
        record_tool_call("get_weather", {"city": city, "date": date}, error_output)
        return ToolResult(
            success=False, output=error_output, summary=f"get_weather({city}, {date}): Not Found"
        )

    day_data = weather_data[matched_city_key][date]

    output = {
        "city": city,
        "date": date,
        "condition": day_data["condition"],
        "temperature_c": day_data["temperature_c"],
        "precip_mm": day_data.get("precip_mm"),
        "wind_kph": day_data.get("wind_kph"),
    }

    summary = f"get_weather({city}, {date}): {output['condition']}, {output['temperature_c']}C"
    record_tool_call("get_weather", {"city": city, "date": date}, output)

    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 3 — calculate_cost
# ---------------------------------------------------------------------------
def calculate_cost(
    venue_id: str,
    party_size: int,
    duration_hours: int,
    catering_tier: str = "bar_snacks",
) -> ToolResult:
    """Compute the total cost for a booking using sample_data/catering.json."""
    venues_file = _SAMPLE_DATA / "venues.json"
    catering_file = _SAMPLE_DATA / "catering.json"

    if not venues_file.exists():
        raise ToolError("SA_TOOL_DEPENDENCY_MISSING: venues.json not found.")
    if not catering_file.exists():
        raise ToolError("SA_TOOL_DEPENDENCY_MISSING: catering.json not found.")

    with open(venues_file, encoding="utf-8") as f:
        venues = json.load(f)
    with open(catering_file, encoding="utf-8") as f:
        catering_data = json.load(f)

    venue = next((v for v in venues if v["id"] == venue_id), None)
    if not venue:
        raise ToolError(f"SA_TOOL_INVALID_INPUT: Venue with ID '{venue_id}' does not exist.")

    base_rates = catering_data.get("base_rates", {})
    venue_modifiers = catering_data.get("venue_modifiers", {})
    service_charge_percent = catering_data.get("service_charge_percent", 10)

    if catering_tier not in base_rates:
        raise ToolError(f"SA_TOOL_INVALID_INPUT: Unknown catering tier '{catering_tier}'.")

    base_per_head = base_rates[catering_tier]
    venue_mult = venue_modifiers.get(venue_id, 1.0)

    subtotal = base_per_head * venue_mult * party_size * max(1, duration_hours)
    service = subtotal * service_charge_percent / 100

    venue_fixed_fees = venue.get("hire_fee_gbp", 0) + venue.get("min_spend_gbp", 0)
    total = subtotal + service + venue_fixed_fees

    subtotal_gbp = int(math.ceil(subtotal))
    service_gbp = int(math.ceil(service))
    total_gbp = int(math.ceil(total))

    if total_gbp < 300:
        deposit_required_gbp = 0
    elif total_gbp <= 1000:
        deposit_required_gbp = int(math.ceil(total_gbp * 0.20))
    else:
        deposit_required_gbp = int(math.ceil(total_gbp * 0.30))

    output = {
        "venue_id": venue_id,
        "party_size": party_size,
        "duration_hours": duration_hours,
        "catering_tier": catering_tier,
        "subtotal_gbp": subtotal_gbp,
        "service_gbp": service_gbp,
        "total_gbp": total_gbp,
        "deposit_required_gbp": deposit_required_gbp,
    }

    summary = f"calculate_cost({venue_id}, {party_size}): total £{total_gbp}, deposit £{deposit_required_gbp}"
    record_tool_call(
        "calculate_cost",
        {
            "venue_id": venue_id,
            "party_size": party_size,
            "duration_hours": duration_hours,
            "catering_tier": catering_tier,
        },
        output,
    )

    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 4 — generate_flyer
# ---------------------------------------------------------------------------
def generate_flyer(session: Session, event_details: dict) -> ToolResult:
    """Produce an HTML flyer and write it to workspace/flyer.html in the session directory."""
    required_keys = [
        "venue_name",
        "venue_address",
        "date",
        "time",
        "party_size",
        "condition",
        "temperature_c",
        "total_gbp",
        "deposit_required_gbp",
    ]
    for key in required_keys:
        if key not in event_details:
            raise ToolError(f"SA_TOOL_INVALID_INPUT: Missing required event details field '{key}'.")

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Event Flyer</title>
</head>
<body>
    <div class="card">
        <h1 data-testid="venue_name">{event_details["venue_name"]}</h1>
        <p>Address: <span data-testid="venue_address">{event_details["venue_address"]}</span></p>
        <p>Date: <span data-testid="date">{event_details["date"]}</span></p>
        <p>Time: <span data-testid="time">{event_details["time"]}</span></p>
        <p>Party Size: <span data-testid="party_size">{event_details["party_size"]}</span></p>
        <p>Condition: <span data-testid="condition">{event_details["condition"]}</span></p>
        <p>Temperature: <span data-testid="temperature_c">{event_details["temperature_c"]}</span>°C</p>
        <p>Total Cost: <span data-testid="total_gbp">£{event_details["total_gbp"]}</span></p>
        <p>Deposit Required: <span data-testid="deposit_required_gbp">£{event_details["deposit_required_gbp"]}</span></p>
    </div>
</body>
</html>
"""

    if hasattr(session, "workspace_dir"):
        workspace_dir = Path(session.workspace_dir)
    elif hasattr(session, "dir"):
        workspace_dir = Path(session.dir) / "workspace"
    else:
        workspace_dir = Path("workspace")

    workspace_dir.mkdir(parents=True, exist_ok=True)
    flyer_path = workspace_dir / "flyer.html"

    with open(flyer_path, "w", encoding="utf-8") as f:
        bytes_written = f.write(html_content)

    output = {"path": "workspace/flyer.html", "bytes_written": bytes_written}

    summary = f"generate_flyer: wrote {output['path']} ({bytes_written} chars)"
    record_tool_call("generate_flyer", {"event_details": event_details}, output)

    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# Registry builder
# ---------------------------------------------------------------------------
def build_tool_registry(session: Session) -> ToolRegistry:
    from sovereign_agent.tools.builtin import make_builtin_registry

    reg = make_builtin_registry(session)

    # venue_search
    reg.register(
        _RegisteredTool(
            name="venue_search",
            description="Search Edinburgh venues by area, party size, and max budget.",
            fn=venue_search,
            parameters_schema={
                "type": "object",
                "properties": {
                    "near": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "budget_max_gbp": {"type": "integer", "default": 1000},
                },
                "required": ["near", "party_size"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,
        )
    )

    # get_weather
    reg.register(
        _RegisteredTool(
            name="get_weather",
            description="Get scripted weather for a city on a YYYY-MM-DD date.",
            fn=get_weather,
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["city", "date"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,
        )
    )

    # calculate_cost
    reg.register(
        _RegisteredTool(
            name="calculate_cost",
            description="Compute total cost and deposit for a booking using JSON fixtures.",
            fn=calculate_cost,
            parameters_schema={
                "type": "object",
                "properties": {
                    "venue_id": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "duration_hours": {"type": "integer"},
                    "catering_tier": {
                        "type": "string",
                        "enum": ["drinks_only", "bar_snacks", "sit_down_meal", "three_course_meal"],
                        "default": "bar_snacks",
                    },
                },
                "required": ["venue_id", "party_size", "duration_hours"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,
        )
    )

    # generate_flyer
    def _flyer_adapter(event_details: dict) -> ToolResult:
        return generate_flyer(session, event_details)

    reg.register(
        _RegisteredTool(
            name="generate_flyer",
            description="Write an HTML flyer for the event to workspace/flyer.html.",
            fn=_flyer_adapter,
            parameters_schema={
                "type": "object",
                "properties": {"event_details": {"type": "object"}},
                "required": ["event_details"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=False,
        )
    )

    return reg


__all__ = [
    "build_tool_registry",
    "venue_search",
    "get_weather",
    "calculate_cost",
    "generate_flyer",
]
