# Service 3 (function calling): three small local functions the model
# can call -- no external API needed, just plain Python.

from datetime import datetime, timedelta

# --- Tool 1: unit conversion ---

LENGTH_TO_M = {"cm": 0.01, "m": 1.0, "in": 0.0254, "ft": 0.3048}
WEIGHT_TO_KG = {"kg": 1.0, "g": 0.001, "lb": 0.45359237, "oz": 0.0283495231}


def convert_measurement(value, from_unit, to_unit):
    from_unit = (from_unit or "").strip().lower()
    to_unit = (to_unit or "").strip().lower()

    if from_unit in WEIGHT_TO_KG and to_unit in WEIGHT_TO_KG:
        kg = value * WEIGHT_TO_KG[from_unit]
        result = kg / WEIGHT_TO_KG[to_unit]
        kind = "weight"
    elif from_unit in LENGTH_TO_M and to_unit in LENGTH_TO_M:
        meters = value * LENGTH_TO_M[from_unit]
        result = meters / LENGTH_TO_M[to_unit]
        kind = "length"
    else:
        return {
            "error": "Can't convert between '" + from_unit + "' and '" + to_unit + "'. "
            + "Weight units: " + str(sorted(WEIGHT_TO_KG)) + ". "
            + "Length units: " + str(sorted(LENGTH_TO_M)) + "."
        }

    return {
        "kind": kind,
        "input_value": value,
        "from_unit": from_unit,
        "to_unit": to_unit,
        "result": round(result, 4),
    }


# --- Tool 2: visit planning ---

def plan_zoo_visit(available_minutes, num_exhibits_wanted, minutes_per_exhibit=15):
    if available_minutes <= 0 or num_exhibits_wanted <= 0 or minutes_per_exhibit <= 0:
        return {"error": "available_minutes, num_exhibits_wanted, and minutes_per_exhibit must all be positive."}

    max_exhibits_possible = int(available_minutes // minutes_per_exhibit)
    time_needed = num_exhibits_wanted * minutes_per_exhibit
    fits = time_needed <= available_minutes

    return {
        "available_minutes": available_minutes,
        "minutes_per_exhibit": minutes_per_exhibit,
        "num_exhibits_wanted": num_exhibits_wanted,
        "max_exhibits_possible_in_time": max_exhibits_possible,
        "time_needed_for_wanted_minutes": time_needed,
        "fits_in_available_time": fits,
        "shortfall_minutes": None if fits else round(time_needed - available_minutes, 1),
    }


# --- Tool 3: feeding schedule (simulated, not a real zoo schedule) ---

FEEDING_HOURS_BY_CATEGORY = {
    "mammal": [9, 13, 17],
    "bird": [8, 12, 16],
    "reptile": [11],
    "amphibian": [10, 18],
    "fish": [9, 15],
    "invertebrate": [10],
}


def next_feeding_time(animal_category, current_time_24h=None):
    category = (animal_category or "").strip().lower()
    hours = FEEDING_HOURS_BY_CATEGORY.get(category)
    if not hours:
        return {"error": "Unknown category '" + str(animal_category) + "'. Try one of: " + str(sorted(FEEDING_HOURS_BY_CATEGORY)) + "."}

    if current_time_24h:
        try:
            now = datetime.strptime(current_time_24h.strip(), "%H:%M")
        except ValueError:
            return {"error": "current_time_24h must be HH:MM 24-hour format, e.g. '14:30'."}
    else:
        now = datetime.now()

    today_times = [now.replace(hour=h, minute=0, second=0, microsecond=0) for h in hours]
    upcoming = [t for t in today_times if t > now]

    if upcoming:
        next_time = min(upcoming)
    else:
        next_time = today_times[0] + timedelta(days=1)  # roll over to tomorrow

    return {
        "animal_category": category,
        "reference_time": now.strftime("%H:%M"),
        "todays_feeding_times": [t.strftime("%H:%M") for t in today_times],
        "next_feeding_time": next_time.strftime("%H:%M"),
        "is_tomorrow": next_time.date() != now.date(),
    }


ZOO_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "convert_measurement",
            "description": "Convert a weight (kg/g/lb/oz) or length (cm/m/in/ft) measurement between units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "number", "description": "The numeric value to convert."},
                    "from_unit": {"type": "string", "description": "Unit of the input value, e.g. 'kg', 'lb', 'cm', 'ft'."},
                    "to_unit": {"type": "string", "description": "Unit to convert to."},
                },
                "required": ["value", "from_unit", "to_unit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_zoo_visit",
            "description": "Work out whether a visitor's exhibit wish-list fits in the time they have.",
            "parameters": {
                "type": "object",
                "properties": {
                    "available_minutes": {"type": "number", "description": "Total minutes the visitor has for their visit."},
                    "num_exhibits_wanted": {"type": "integer", "description": "How many exhibits the visitor wants to see."},
                    "minutes_per_exhibit": {"type": "number", "description": "Estimated minutes per exhibit (default 15)."},
                },
                "required": ["available_minutes", "num_exhibits_wanted"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "next_feeding_time",
            "description": "Get the next scheduled feeding time for an animal category (mammal, bird, reptile, amphibian, fish, invertebrate).",
            "parameters": {
                "type": "object",
                "properties": {
                    "animal_category": {"type": "string", "description": "One of: mammal, bird, reptile, amphibian, fish, invertebrate."},
                    "current_time_24h": {"type": "string", "description": "Optional current time as HH:MM (24h). Defaults to now."},
                },
                "required": ["animal_category"],
            },
        },
    },
]


def call_zoo_tool(name, args):
    """Runs one of the three zoo tools by name. Used by app.py's tool
    dispatch loop."""
    if name == "convert_measurement":
        return convert_measurement(**args)
    elif name == "plan_zoo_visit":
        return plan_zoo_visit(**args)
    elif name == "next_feeding_time":
        return next_feeding_time(**args)
    else:
        return {"error": "Unknown zoo tool '" + name + "'."}
