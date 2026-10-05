import re
import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:0.6b"


def ask_ai(message: str) -> str:
    system_prompt = """
You are MediRoute AI, an emergency ambulance dispatch assistant.

Answer briefly and clearly.

You are part of an academic emergency ambulance dispatch simulation.

Do not claim to contact real emergency services.

If the user is only asking a general question, answer normally.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "stream": False,
                "options": {
                    "num_predict": 80,
                    "temperature": 0.2
                }
            },
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        return data["message"]["content"]

    except requests.exceptions.ConnectionError:
        return "Ollama is not running."

    except requests.exceptions.Timeout:
        return "The local AI is taking too long to respond."

    except Exception as e:
        return f"AI service error: {str(e)}"


def understand_emergency(message: str):
    text = message.lower().strip()

    # --------------------------------------------------
    # 1. DETECT SUPPORTED LOCATION
    # --------------------------------------------------

    locations = {
        "gandhipuram": "Gandhipuram",
        "rs puram": "RS Puram",
        "r.s. puram": "RS Puram",
        "peelamedu": "Peelamedu",
        "saibaba colony": "Saibaba Colony",
        "sai baba colony": "Saibaba Colony",
        "town hall": "Town Hall"
    }

    location = None

    for key, value in locations.items():
        if key in text:
            location = value
            break

    # Without a supported location, treat the message
    # as normal chatbot conversation.
    if not location:
        return None

    # --------------------------------------------------
    # 2. DETECT EMERGENCY TYPE
    # --------------------------------------------------

    if any(word in text for word in [
        "cardiac",
        "heart attack",
        "heart problem",
        "chest pain",
        "unconscious"
    ]):
        emergency_type = "Cardiac"

    elif any(word in text for word in [
        "panic attack",
        "panic",
        "breathing problem",
        "difficulty breathing",
        "breathless"
    ]):
        emergency_type = "Medical Emergency"

    elif any(word in text for word in [
        "injury",
        "injured",
        "wound",
        "bleeding",
        "fracture"
    ]):
        emergency_type = "Injury"

    elif any(word in text for word in [
        "accident",
        "crash",
        "collision",
        "hit"
    ]):
        emergency_type = "Accident"

    else:
        # A supported location was supplied but there is
        # no recognizable emergency description.
        return None

    # --------------------------------------------------
    # 3. DETECT SEVERITY
    # --------------------------------------------------

    severity = 3

    severity_match = re.search(
        r"severity\s*[:\-]?\s*([1-5])",
        text
    )

    if severity_match:
        severity = int(severity_match.group(1))

    elif any(word in text for word in [
        "critical",
        "severe",
        "life threatening",
        "life-threatening",
        "not breathing",
        "unconscious"
    ]):
        severity = 5

    # --------------------------------------------------
    # 4. DETECT REQUIRED FACILITY
    # --------------------------------------------------

    if "icu" in text:
        required_facility = "ICU"

    elif "trauma" in text:
        required_facility = "Trauma"

    else:
        required_facility = ""

    # --------------------------------------------------
    # 5. AUTOMATIC DISPATCH
    # --------------------------------------------------

    # If MediRoute has detected both:
    #   - a supported location
    #   - a recognizable emergency
    #
    # the ambulance dispatch process should start
    # automatically.
    dispatch = True

    return {
        "is_emergency_command": True,
        "location": location,
        "emergency_type": emergency_type,
        "severity": severity,
        "required_facility": required_facility,
        "dispatch": dispatch
    }