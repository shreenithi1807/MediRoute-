
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


# ---------------------------------------------------------
# Make the main MediRoute project available to Python
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.services import data_service as ds
from backend.services import dispatcher
from backend.algorithms.astar import astar


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------
app = FastAPI(
    title="MediRoute Web",
    description="Free educational emergency ambulance dispatcher.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Frontend
# ---------------------------------------------------------
WEB_DIR = Path(__file__).resolve().parent / "web"

app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR),
    name="static",
)


@app.get("/")
def home():
    return FileResponse(WEB_DIR / "index.html")


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "MediRoute Web",
        "mode": "free-local-simulator",
    }


# ---------------------------------------------------------
# Simple local emergency analysis
# ---------------------------------------------------------
def analyze_emergency(message: str):
    text = message.lower()

    # ---------------------------------------------
    # Detect location from MediRoute road network
    # ---------------------------------------------
    locations = [
        "Gandhipuram",
        "RS Puram",
        "Peelamedu",
        "Saibaba Colony",
        "Town Hall",
    ]

    location = None

    for place in locations:
        if place.lower() in text:
            location = place
            break

    if location is None:
        return {
            "ok": False,
            "error": (
                "I could not identify the emergency location. "
                "Please mention one of: Gandhipuram, RS Puram, "
                "Peelamedu, Saibaba Colony, or Town Hall."
            ),
        }

    # ---------------------------------------------
    # Detect emergency type
    # ---------------------------------------------
    if any(word in text for word in [
        "accident",
        "crash",
        "collision",
        "road accident",
    ]):
        emergency_type = "Road Accident"

    elif any(word in text for word in [
        "heart",
        "cardiac",
        "chest pain",
    ]):
        emergency_type = "Cardiac Emergency"

    elif any(word in text for word in [
        "bleeding",
        "blood",
        "hemorrhage",
    ]):
        emergency_type = "Severe Bleeding"

    elif any(word in text for word in [
        "fire",
        "burn",
        "burns",
    ]):
        emergency_type = "Burn Injury"

    else:
        emergency_type = "General Emergency"

    # ---------------------------------------------
    # Detect severity
    # ---------------------------------------------
    if any(word in text for word in [
        "critical",
        "life threatening",
        "life-threatening",
        "unconscious",
        "severe bleeding",
        "massive bleeding",
        "not breathing",
    ]):
        severity = 5

    elif any(word in text for word in [
        "severe",
        "serious",
        "major",
    ]):
        severity = 4

    elif any(word in text for word in [
        "moderate",
        "injured",
        "injury",
    ]):
        severity = 3

    elif any(word in text for word in [
        "minor",
        "small",
    ]):
        severity = 2

    else:
        severity = 3

    # ---------------------------------------------
    # Detect required hospital facility
    # ---------------------------------------------
    if any(word in text for word in [
        "icu",
        "intensive care",
        "critical care",
    ]):
        required_facility = "ICU"

    elif any(word in text for word in [
        "trauma",
        "traumatic",
        "major injury",
    ]):
        required_facility = "Trauma"

    else:
        required_facility = ""

    # ---------------------------------------------
    # Create simulated emergency
    # ---------------------------------------------
    emergency = dispatcher.create_emergency(
        location=location,
        emergency_type=emergency_type,
        severity=severity,
        required_facility=required_facility,
    )

    # ---------------------------------------------
    # Dispatch ambulance using existing algorithms
    # ---------------------------------------------
    result = dispatcher.dispatch(emergency["id"])

    if not result.get("success"):
        return {
            "ok": False,
            "error": result.get(
                "message",
                "Unable to dispatch an ambulance.",
            ),
            "emergency": emergency,
        }

    ambulance = result["ambulance"]
    route = result["route"]
    hospital = result["hospital"]

    # ---------------------------------------------
    # Return structured result
    # ---------------------------------------------
    return {
        "ok": True,
        "mode": "free-local-simulator",

        "answer": (
            "MediRoute simulation completed.\n\n"
            f"Emergency: {emergency_type}\n"
            f"Location: {location}\n"
            f"Severity: {severity}/5\n"
            f"Required facility: "
            f"{required_facility if required_facility else 'General care'}\n\n"
            f"Ambulance selected: {ambulance['id']}\n"
            f"Ambulance location: {ambulance['location']}\n"
            f"Ambulance type: {ambulance.get('type', 'Unknown')}\n"
            f"Route: {' → '.join(route['path'])}\n"
            f"Route cost: {route['cost']}\n"
            f"Estimated ETA: {result['eta_minutes']} minutes\n\n"
            f"Recommended hospital: {hospital['name']}\n"
            f"Hospital location: {hospital['location']}\n"
            f"Available beds: {hospital['beds']}\n"
            f"ICU available: "
            f"{'Yes' if hospital['icu'] else 'No'}\n"
            f"Trauma facility: "
            f"{'Yes' if hospital['trauma'] else 'No'}\n\n"
            "This is an educational simulation. "
            "No real ambulance, hospital, emergency service, "
            "or person has been contacted."
        ),

        "emergency": emergency,
        "ambulance": ambulance,
        "route": route,
        "hospital": hospital,
        "eta_minutes": result["eta_minutes"],
    }


# ---------------------------------------------------------
# Analyze API
# ---------------------------------------------------------
@app.post("/api/analyze")
async def analyze(
    message: str = Form(""),
    document: Optional[UploadFile] = File(None),
):
    if not message.strip() and document is None:
        return {
            "ok": False,
            "error": "Enter a situation or upload a document.",
        }

    # ---------------------------------------------
    # Handle uploaded document
    # ---------------------------------------------
    if document is not None:
        filename = document.filename or "document"

        try:
            data = await document.read()

            if len(data) > 32 * 1024 * 1024:
                return {
                    "ok": False,
                    "error": "Document is larger than 32 MB.",
                }

            # UTF-8 text files
            if (
                filename.lower().endswith(".txt")
                or document.content_type == "text/plain"
            ):
                try:
                    uploaded_text = data.decode("utf-8")
                except UnicodeDecodeError:
                    return {
                        "ok": False,
                        "error": (
                            "The text file must use UTF-8 encoding."
                        ),
                    }

                if message.strip():
                    message = (
                        message.strip()
                        + "\n\nUploaded document:\n"
                        + uploaded_text[:200000]
                    )
                else:
                    message = uploaded_text[:200000]

            # PDF support
            elif (
                filename.lower().endswith(".pdf")
                or document.content_type == "application/pdf"
            ):
                return {
                    "ok": False,
                    "error": (
                        "PDF upload is not enabled in this free "
                        "local version yet. Please upload a .txt "
                        "file or type the emergency description."
                    ),
                }

            else:
                return {
                    "ok": False,
                    "error": (
                        "For the free version, upload a UTF-8 "
                        "text (.txt) file or enter the emergency "
                        "description directly."
                    ),
                }

    if not message.strip():
        return {
            "ok": False,
            "error": "No emergency description supplied.",
        }

    # ---------------------------------------------
    # Run free local MediRoute engine
    # ---------------------------------------------
    return analyze_emergency(message.strip())