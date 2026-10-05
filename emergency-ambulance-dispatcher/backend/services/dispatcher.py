from uuid import uuid4
import threading
import time

from backend.services import data_service as ds
from backend.services import repository

from backend.algorithms.astar import astar
from backend.algorithms.ambulance_heap import best_ambulance
from backend.algorithms.priority_queue import EmergencyPriorityQueue


# =========================================================
# GLOBAL EMERGENCY QUEUE
# =========================================================

queue = EmergencyPriorityQueue()
emergencies = []


# =========================================================
# CREATE EMERGENCY
# =========================================================

def create_emergency(
    location,
    emergency_type,
    severity,
    required_facility="",
    latitude=None,
    longitude=None
):
    emergency = {
        "id": "E-" + uuid4().hex[:6].upper(),
        "location": location,
        "type": emergency_type,
        "severity": int(severity),
        "required_facility": required_facility,
        "status": "waiting",
        "latitude": latitude,
        "longitude": longitude
    }

    emergencies.append(emergency)

    # REAL Priority Queue
    queue.push(emergency)

    # Save emergency to SQLite
    try:
        repository.save_emergency(emergency)

    except Exception as error:
        print(
            "Database emergency save warning:",
            error
        )

    return emergency


# =========================================================
# AMBULANCE SELECTION - MIN HEAP
# =========================================================

def choose_ambulance(
    emergency,
    excluded_ambulance_ids=None
):
    ds.refresh_from_database()

    if excluded_ambulance_ids is None:
        excluded_ambulance_ids = []

    candidates = [
        ambulance
        for ambulance in ds.available_ambulances()
        if ambulance["id"]
        not in excluded_ambulance_ids
    ]

    if not candidates:
        return None

    scores = {}

    for ambulance in candidates:

        route = astar(
            ds.roads,
            ambulance["location"],
            emergency["location"]
        )

        if route:
            scores[ambulance["id"]] = route["cost"]

        else:
            scores[ambulance["id"]] = 10**9

    return best_ambulance(
        candidates,
        scores
    )


# =========================================================
# HOSPITAL SCORING
# =========================================================

def hospital_score(
    hospital,
    emergency
):
    route = astar(
        ds.roads,
        emergency["location"],
        hospital["location"]
    )

    if not route:
        return 10**9

    penalty = 0

    required = emergency.get(
        "required_facility",
        ""
    ).lower()

    if (
        required == "icu"
        and not hospital["icu"]
    ):
        penalty += 1000

    if (
        required == "trauma"
        and not hospital["trauma"]
    ):
        penalty += 1000

    if hospital["beds"] <= 0:
        penalty += 500

    return route["cost"] + penalty


def choose_hospital(
    emergency
):
    ds.refresh_from_database()

    hospitals = [
        hospital
        for hospital in ds.hospitals
        if hospital["beds"] > 0
    ]

    if not hospitals:
        return None

    return min(
        hospitals,
        key=lambda hospital: hospital_score(
            hospital,
            emergency
        )
    )


# =========================================================
# AMBULANCE RESPONSE TIMEOUT
# =========================================================

# TESTING:
# Keep this at 10 seconds for now.
# After testing works, change it to 60.
AMBULANCE_RESPONSE_TIMEOUT = 10


def start_response_timer(
    emergency_id,
    ambulance_id,
    assignment_id,
    excluded_ambulance_ids=None
):
    if excluded_ambulance_ids is None:
        excluded_ambulance_ids = []

    excluded_ambulance_ids = list(
        excluded_ambulance_ids
    )

    # Do not assign this emergency back
    # to an ambulance that already timed out.
    if ambulance_id not in excluded_ambulance_ids:
        excluded_ambulance_ids.append(
            ambulance_id
        )

    def check_response():

        time.sleep(
            AMBULANCE_RESPONSE_TIMEOUT
        )

        try:
            assignment = (
                repository.assignment_for_emergency(
                    emergency_id
                )
            )

            # Assignment no longer exists.
            if not assignment:
                return

            # Another assignment has replaced this one.
            if assignment["id"] != assignment_id:
                return

            # Crew already responded.
            if assignment["status"] != "assigned":
                return

            print(
                f"{ambulance_id} did not respond "
                f"within "
                f"{AMBULANCE_RESPONSE_TIMEOUT} seconds."
            )

            # Mark current assignment as timed out.
            repository.timeout_assignment(
                assignment_id
            )

            # Release old ambulance.
            repository.update_ambulance_status(
                ambulance_id,
                "available"
            )

            emergency = repository.get_emergency(
                emergency_id
            )

            if not emergency:
                return

            # Do not reassign cancelled emergency.
            if emergency["status"] == "cancelled":
                return

            # Convert database emergency format
            # to dispatcher format.
            emergency_data = {
                "id": emergency["id"],
                "location": emergency["location"],
                "type": emergency["emergency_type"],
                "severity": emergency["severity"],
                "required_facility": emergency.get(
                    "required_facility",
                    ""
                ),
                "status": "waiting",
                "latitude": emergency.get(
                    "latitude"
                ),
                "longitude": emergency.get(
                    "longitude"
                )
            }

            repository.update_emergency_status(
                emergency_id,
                "waiting"
            )

            # Synchronize in-memory emergency.
            for item in emergencies:

                if item["id"] == emergency_id:
                    item["status"] = "waiting"
                    break

            ds.refresh_from_database()

            # Try another ambulance.
            result = _dispatch_emergency(
                emergency_data,
                excluded_ambulance_ids=
                    excluded_ambulance_ids
            )

            if result["success"]:

                for item in emergencies:

                    if item["id"] == emergency_id:
                        item["status"] = "assigned"
                        break

                print(
                    f"{emergency_id} reassigned from "
                    f"{ambulance_id} to "
                    f"{result['ambulance']['id']}."
                )

            else:
                repository.update_emergency_status(
                    emergency_id,
                    "waiting"
                )

                for item in emergencies:

                    if item["id"] == emergency_id:
                        item["status"] = "waiting"
                        break

                ds.refresh_from_database()

                print(
                    f"Reassignment failed for "
                    f"{emergency_id}: "
                    f"{result['message']}"
                )

        except Exception as error:
            print(
                "Ambulance response timer error:",
                error
            )

    thread = threading.Thread(
        target=check_response,
        daemon=True
    )

    thread.start()


# =========================================================
# CORE DISPATCH LOGIC
# =========================================================

def _dispatch_emergency(
    emergency,
    excluded_ambulance_ids=None
):

    # -----------------------------------------------------
    # MIN HEAP -> CHOOSE AMBULANCE
    # -----------------------------------------------------

    ambulance = choose_ambulance(
        emergency,
        excluded_ambulance_ids
    )

    if not ambulance:
        return {
            "success": False,
            "message": "No available ambulance."
        }

    # -----------------------------------------------------
    # A* -> AMBULANCE TO PATIENT
    # -----------------------------------------------------

    ds.refresh_from_database()

    route = astar(
        ds.roads,
        ambulance["location"],
        emergency["location"]
    )

    if not route:
        return {
            "success": False,
            "message": "No route to emergency."
        }

    # -----------------------------------------------------
    # HOSPITAL SELECTION
    # -----------------------------------------------------

    hospital = choose_hospital(
        emergency
    )

    if not hospital:
        return {
            "success": False,
            "message":
                "No suitable hospital available."
        }

    # -----------------------------------------------------
    # ETA
    # -----------------------------------------------------

    eta = max(
        1,
        round(
            route["cost"] * 2
        )
    )

    # -----------------------------------------------------
    # UPDATE CURRENT DATA
    # -----------------------------------------------------

    ds.update_ambulance(
        ambulance["id"],
        status="assigned"
    )

    emergency["status"] = "assigned"

    # -----------------------------------------------------
    # UPDATE SQLITE
    # -----------------------------------------------------

    try:
        repository.update_ambulance_status(
            ambulance["id"],
            "assigned"
        )

        repository.update_emergency_status(
            emergency["id"],
            "assigned"
        )

        assignment_id = (
            repository.create_assignment(
                emergency_id=
                    emergency["id"],
                ambulance_id=
                    ambulance["id"],
                hospital_name=
                    hospital["name"],
                route=
                    " -> ".join(
                        route["path"]
                    ),
                eta=eta
            )
        )

        # Start response timer.
        start_response_timer(
            emergency["id"],
            ambulance["id"],
            assignment_id,
            excluded_ambulance_ids
        )

    except Exception as error:
        print(
            "Database dispatch warning:",
            error
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    return {
        "success": True,
        "emergency": emergency,
        "ambulance": ambulance,
        "route": route,
        "hospital": hospital,
        "eta_minutes": eta
    }


# =========================================================
# REAL PRIORITY QUEUE DISPATCH
# =========================================================

def dispatch_next():

    # Priority Queue decides which
    # patient is dispatched next.
    emergency = queue.pop()

    if not emergency:
        return {
            "success": False,
            "message":
                "No waiting emergencies."
        }

    result = _dispatch_emergency(
        emergency
    )

    # If dispatch failed, return emergency
    # to waiting queue.
    if not result["success"]:

        emergency["status"] = "waiting"

        queue.push(
            emergency
        )

    return result


# =========================================================
# COMPATIBILITY FUNCTION
# =========================================================

def dispatch(eid):

    """
    Kept so existing MCP/API code does not break.

    Dispatch a particular emergency when explicitly
    requested by another part of the project.
    """

    emergency = next(
        (
            item
            for item in emergencies
            if item["id"] == eid
        ),
        None
    )

    if not emergency:
        raise ValueError(
            "Emergency not found"
        )

    return _dispatch_emergency(
        emergency
    )


# =========================================================
# VIEW WAITING QUEUE
# =========================================================

def get_waiting_emergencies():

    return [
        emergency
        for emergency in emergencies
        if emergency.get("status")
        == "waiting"
    ]