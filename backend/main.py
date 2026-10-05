from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from backend.services import repository
from backend.services import data_service as ds
from backend.services import dispatcher
from backend.services.ai_service import ask_ai, understand_emergency
from backend.services.database import init_database
from backend.services.migrate_data import migrate_existing_data


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="MediRoute AI - Emergency Ambulance Dispatcher"
)


# =========================================================
# DATABASE
# =========================================================

init_database()
migrate_existing_data()


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# STATIC FRONTEND
# =========================================================

app.mount(
    "/static",
    StaticFiles(
        directory=ROOT / "frontend"
    ),
    name="static"
)


# =========================================================
# REQUEST MODELS
# =========================================================

class EmergencyIn(BaseModel):
    location: str
    emergency_type: str = "Accident"
    severity: int = Field(
        5,
        ge=1,
        le=5
    )
    required_facility: str = ""


class RoadUpdate(BaseModel):
    from_node: str
    to_node: str
    status: str


class AmbulanceStatusIn(BaseModel):
    status: str
    location: str | None = None


class PatientLocationIn(BaseModel):
    latitude: float
    longitude: float


class AmbulanceLocationIn(BaseModel):
    latitude: float
    longitude: float


class ChatIn(BaseModel):
    message: str


class AdminAmbulanceIn(BaseModel):
    id: str
    location: str
    status: str = "available"
    latitude: float | None = None
    longitude: float | None = None


class AdminHospitalIn(BaseModel):
    name: str
    location: str
    beds: int
    icu: int
    trauma: int


# =========================================================
# FRONTEND PAGES
# =========================================================

@app.get("/")
def home():
    return FileResponse(
        ROOT / "frontend" / "index.html"
    )


@app.get("/ambulance")
def ambulance_page():
    return FileResponse(
        ROOT / "frontend" / "ambulance.html"
    )


@app.get("/admin")
def admin_page():
    return FileResponse(
        ROOT / "frontend" / "admin.html"
    )
@app.get("/hospital")
def hospital_page():
    return FileResponse(
        ROOT / "frontend" / "hospital.html"
    )

# =========================================================
# SYSTEM STATE
# =========================================================

@app.get("/api/state")
def state():

    ds.refresh_from_database()

    return {
        "ambulances": ds.ambulances,
        "hospitals": ds.hospitals,
        "roads": ds.roads,
        "emergencies": dispatcher.emergencies
    }


# =========================================================
# RESET
# =========================================================

@app.post("/api/reset")
def reset():

    ds.reset_data()

    dispatcher.emergencies.clear()

    dispatcher.queue = (
        dispatcher.queue.__class__()
    )

    return {
        "success": True,
        "message": "Simulation reset."
    }


# =========================================================
# CREATE EMERGENCY
# =========================================================

@app.post("/api/emergencies")
def add_emergency(
    emergency: EmergencyIn
):

    return dispatcher.create_emergency(
        **emergency.model_dump()
    )


# =========================================================
# PATIENT LIVE LOCATION
# Patient -> Ambulance
# =========================================================

@app.post(
    "/api/emergencies/{emergency_id}/location"
)
def patient_location(
    emergency_id: str,
    location: PatientLocationIn
):

    emergency = repository.get_emergency(
        emergency_id
    )

    if not emergency:
        raise HTTPException(
            status_code=404,
            detail="Emergency not found"
        )

    repository.update_patient_location(
        emergency_id,
        location.latitude,
        location.longitude
    )

    return {
        "success": True,
        "emergency_id": emergency_id,
        "latitude": location.latitude,
        "longitude": location.longitude
    }


# =========================================================
# AMBULANCE LIVE LOCATION
# Ambulance -> Patient
# =========================================================

@app.post(
    "/api/ambulances/{ambulance_id}/location"
)
def update_ambulance_live_location(
    ambulance_id: str,
    location: AmbulanceLocationIn
):

    ambulance = repository.get_ambulance(
        ambulance_id
    )

    if not ambulance:
        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    repository.update_ambulance_location(
        ambulance_id,
        location.latitude,
        location.longitude
    )

    return {
        "success": True,
        "ambulance_id": ambulance_id,
        "latitude": location.latitude,
        "longitude": location.longitude
    }


# =========================================================
# PATIENT TRACKS ASSIGNED AMBULANCE
# =========================================================

@app.get(
    "/api/emergencies/{emergency_id}/tracking"
)
def patient_tracking(
    emergency_id: str
):

    emergency = repository.get_emergency(
        emergency_id
    )

    if not emergency:
        raise HTTPException(
            status_code=404,
            detail="Emergency not found"
        )

    assignment = (
        repository.assignment_for_emergency(
            emergency_id
        )
    )

    if not assignment:
        return {
            "emergency": emergency,
            "assignment": None,
            "ambulance": None
        }

    ambulance = repository.get_ambulance(
        assignment["ambulance_id"]
    )

    return {
        "emergency": emergency,
        "assignment": assignment,
        "ambulance": ambulance
    }


# =========================================================
# AMBULANCE GETS ASSIGNED PATIENT
# =========================================================

@app.get(
    "/api/ambulances/{ambulance_id}/assignment"
)
def ambulance_assignment(
    ambulance_id: str
):

    assignment = (
        repository.assignment_for_ambulance(
            ambulance_id
        )
    )

    if not assignment:
        return {
            "ambulance_id": ambulance_id,
            "assignment": None,
            "emergency": None
        }

    emergency = repository.get_emergency(
        assignment["emergency_id"]
    )

    return {
        "ambulance_id": ambulance_id,
        "assignment": assignment,
        "emergency": emergency
    }


# =========================================================
# MANUAL EMERGENCY DISPATCH
# =========================================================

@app.post(
    "/api/dispatch/{emergency_id}"
)
def dispatch_emergency(
    emergency_id: str
):

    try:

        return dispatcher.dispatch(
            emergency_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


# =========================================================
# PRIORITY QUEUE DISPATCH
# =========================================================

@app.post("/api/dispatch-next")
def dispatch_next():

    return dispatcher.dispatch_next()


# =========================================================
# ROAD UPDATE
# =========================================================

@app.post("/api/roads")
def update_road(
    road: RoadUpdate
):

    success = ds.update_road(
        road.from_node,
        road.to_node,
        road.status
    )

    if not success:

        raise HTTPException(
            status_code=404,
            detail="Road not found"
        )

    return {
        "success": True,
        "from": road.from_node,
        "to": road.to_node,
        "status": road.status
    }


# =========================================================
# AMBULANCE STATUS
# =========================================================

@app.post(
    "/api/ambulances/{ambulance_id}/status"
)
def ambulance_status(
    ambulance_id: str,
    body: AmbulanceStatusIn
):

    allowed_statuses = {
    "available",
    "paused",
    "assigned",
    "en_route",
    "with_patient",
    "at_hospital",
    "completed"
}

    if body.status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail="Invalid ambulance status"
        )

    ambulance = repository.get_ambulance(
        ambulance_id
    )

    if not ambulance:

        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    repository.update_ambulance_status(
        ambulance_id,
        body.status,
        body.location
    )

    # Keep data_service synchronized
    ds.refresh_from_database()

    assignment = (
        repository.assignment_for_ambulance(
            ambulance_id
        )
    )

    # Keep assignment lifecycle synchronized
    if assignment:

        repository.update_assignment_status(
            assignment["id"],
            body.status
        )

    return {
        "success": True,
        "ambulance": ambulance_id,
        "status": body.status
    }

@app.post("/api/emergencies/{emergency_id}/cancel")
def cancel_emergency(emergency_id: str):

    emergency = repository.get_emergency(emergency_id)

    if not emergency:
        raise HTTPException(
            status_code=404,
            detail="Emergency not found"
        )

    if emergency["status"] in {"completed", "cancelled"}:
        raise HTTPException(
            status_code=400,
            detail="Emergency cannot be cancelled."
        )

    repository.cancel_emergency(emergency_id)

    # Update in-memory emergency as well
    for item in dispatcher.emergencies:
        if item["id"] == emergency_id:
            item["status"] = "cancelled"
            break

    ds.refresh_from_database()

    return {
        "success": True,
        "emergency_id": emergency_id,
        "status": "cancelled",
        "message": "Emergency cancelled successfully."
    }
# =========================================================
# COMPLETE CASE / RETURN TO DUTY
# =========================================================

@app.post(
    "/api/ambulances/{ambulance_id}/return-duty"
)
def return_to_duty(
    ambulance_id: str
):

    ambulance = repository.get_ambulance(
        ambulance_id
    )

    if not ambulance:

        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    assignment = (
        repository.assignment_for_ambulance(
            ambulance_id
        )
    )

    if assignment:

        repository.update_assignment_status(
            assignment["id"],
            "completed"
        )

        repository.update_emergency_status(
            assignment["emergency_id"],
            "completed"
        )

    repository.update_ambulance_status(
        ambulance_id,
        "available"
    )

    ds.refresh_from_database()

    waiting = (
        dispatcher.get_waiting_emergencies()
    )

    return {
        "success": True,
        "ambulance": ambulance_id,
        "status": "available",
        "waiting_emergencies": len(waiting),
        "message":
            "Case completed. Ambulance returned to duty."
    }


# =========================================================
# ADMIN - ALL DATA
# =========================================================

@app.get("/api/admin/data")
def admin_data():

    return {
        "ambulances":
            repository.get_ambulances(),

        "hospitals":
            repository.get_hospitals(),

        "roads":
            repository.get_roads(),

        "emergencies":
            repository.get_emergencies(),

        "assignments":
            repository.assignments()
    }


# =========================================================
# ADMIN - SAVE AMBULANCE
# =========================================================

@app.post("/api/admin/ambulances")
def admin_save_ambulance(
    ambulance: AdminAmbulanceIn
):

    repository.save_ambulance(
        ambulance.model_dump()
    )

    ds.refresh_from_database()

    return {
        "success": True,
        "message":
            "Ambulance saved successfully."
    }
# =========================================================
# ADMIN - DELETE AMBULANCE
# =========================================================

@app.delete("/api/admin/ambulances/{ambulance_id}")
def admin_delete_ambulance(ambulance_id: str):

    ambulance = repository.get_ambulance(
        ambulance_id
    )

    if not ambulance:
        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    # Do not delete ambulance handling a case
    if ambulance["status"] not in {
        "available",
        "paused"
    }:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an ambulance handling an active case."
        )

    repository.delete_ambulance(
        ambulance_id
    )

    ds.refresh_from_database()

    return {
        "success": True,
        "message": f"{ambulance_id} deleted successfully."
    }

# =========================================================
# ADMIN - SAVE HOSPITAL
# =========================================================

@app.post("/api/admin/hospitals")
def admin_save_hospital(
    hospital: AdminHospitalIn
):

    repository.save_hospital(
        hospital.model_dump()
    )

    ds.refresh_from_database()

    return {
        "success": True,
        "message":
            "Hospital saved successfully."
    }

# =========================================================
# HOSPITAL CONSOLE
# =========================================================

@app.get("/api/hospitals")
def hospital_list():

    return repository.get_hospitals()


@app.get("/api/hospital/{hospital_name}")
def hospital_details(hospital_name: str):

    hospital = repository.get_hospital(
        hospital_name
    )

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    incoming = (
        repository.hospital_incoming_cases(
            hospital_name
        )
    )

    return {
        "hospital": hospital,
        "incoming": incoming
    }


@app.post("/api/hospital/{hospital_name}/capacity")
def hospital_update_capacity(
    hospital_name: str,
    body: AdminHospitalIn
):

    hospital = repository.get_hospital(
        hospital_name
    )

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found"
        )

    if body.beds < 0 or body.icu < 0 or body.trauma < 0:

        raise HTTPException(
            status_code=400,
            detail="Capacity cannot be negative."
        )

    repository.save_hospital({
        "name": hospital_name,
        "location": hospital["location"],
        "beds": body.beds,
        "icu": body.icu,
        "trauma": body.trauma
    })

    ds.refresh_from_database()

    return {
        "success": True,
        "hospital":
            repository.get_hospital(
                hospital_name
            ),
        "message":
            "Hospital capacity updated."
    }
# =========================================================
# AI CHAT
# =========================================================

@app.post("/api/chat")
def chat(
    chat_request: ChatIn
):

    message = (
        chat_request.message.strip()
    )

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )


    # -----------------------------------------------------
    # UNDERSTAND EMERGENCY COMMAND
    # -----------------------------------------------------

    parsed = understand_emergency(
        message
    )


    if (
        parsed
        and parsed.get("location")
    ):

        location = parsed.get(
            "location"
        )

        emergency_type = parsed.get(
            "emergency_type",
            "Accident"
        )

        severity = int(
            parsed.get(
                "severity",
                3
            )
        )

        required_facility = (
            parsed.get(
                "required_facility",
                ""
            )
        )


        # -------------------------------------------------
        # CREATE EMERGENCY
        # -------------------------------------------------

        emergency = (
            dispatcher.create_emergency(
                location=location,
                emergency_type=
                    emergency_type,
                severity=severity,
                required_facility=
                    required_facility
            )
        )


        # -------------------------------------------------
        # DISPATCH REQUESTED
        # -------------------------------------------------

        if parsed.get("dispatch"):

            # Priority Queue selects the
            # highest-priority waiting emergency.
            result = (
                dispatcher.dispatch_next()
            )


            if result.get("success"):

                dispatched_emergency = (
                    result["emergency"]
                )

                ambulance = (
                    result["ambulance"]
                )

                route = (
                    result["route"]
                )

                hospital = (
                    result["hospital"]
                )


                reply = (
                    "✓ EMERGENCY DISPATCHED\n\n"

                    f"Emergency: "
                    f"{dispatched_emergency['type']}\n"

                    f"Severity: "
                    f"{dispatched_emergency['severity']}/5\n"

                    f"Location: "
                    f"{dispatched_emergency['location']}\n\n"

                    f"Ambulance: "
                    f"{ambulance['id']}\n"

                    f"Ambulance Location: "
                    f"{ambulance['location']}\n"

                    f"ETA: "
                    f"{result['eta_minutes']} minutes\n\n"

                    f"Route: "
                    f"{' → '.join(route['path'])}\n\n"

                    f"Hospital: "
                    f"{hospital['name']}\n"

                    f"Available Beds: "
                    f"{hospital['beds']}\n\n"

                    "Decision Engine:\n"
                    "Priority Queue → "
                    "Min Heap → "
                    "A* → "
                    "Hospital Scoring"
                )


                return {
                    "reply":
                        reply,

                    "action":
                        "dispatch",

                    "created_emergency":
                        emergency,

                    "result":
                        result
                }


            return {
                "reply":
                    result.get(
                        "message",
                        "Dispatch could not be completed."
                    ),

                "action":
                    "dispatch_failed",

                "emergency":
                    emergency
            }


        # -------------------------------------------------
        # EMERGENCY CREATED BUT NOT DISPATCHED
        # -------------------------------------------------

        return {
            "reply": (
                f"Emergency "
                f"{emergency['id']} "
                f"created successfully.\n\n"

                f"Location: "
                f"{emergency['location']}\n"

                f"Severity: "
                f"{emergency['severity']}/5\n\n"

                "Added to the Priority Queue."
            ),

            "action":
                "emergency_created",

            "emergency":
                emergency
        }


    # -----------------------------------------------------
    # NORMAL QWEN CHAT
    # -----------------------------------------------------

    reply = ask_ai(
        message
    )

    if not reply:

        reply = (
            "I could not generate a response. "
            "Please try again."
        )


    return {
        "reply":
            reply,

        "action":
            "chat"
    }