from pathlib import Path
import json

from backend.services.database import rows

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def load(name):
    return json.loads(
        (DATA / name).read_text()
    )


# Original JSON data remains as backup
ambulances = load("ambulances.json")
hospitals = load("hospitals.json")
roads = load("roads.json")


# ==========================================
# LOAD CURRENT SQLITE DATA
# ==========================================

def refresh_from_database():
    global ambulances, hospitals, roads

    db_ambulances = rows(
        "SELECT * FROM ambulances"
    )

    db_hospitals = rows(
        "SELECT * FROM hospitals"
    )

    db_roads = rows(
        "SELECT * FROM roads"
    )

    if db_ambulances:
        ambulances = db_ambulances

    if db_hospitals:
        hospitals = db_hospitals

    if db_roads:

        roads = []

        for road in db_roads:

            roads.append({
                "id": road["id"],
                "from": road["from_node"],
                "to": road["to_node"],
                "distance": road["distance"],
                "traffic": road["traffic"],
                "status": road["status"]
            })


# ==========================================
# RESET
# ==========================================

def reset_data():

    global ambulances
    global hospitals
    global roads

    refresh_from_database()


# ==========================================
# AMBULANCES
# ==========================================

def available_ambulances():

    refresh_from_database()

    return [
        ambulance
        for ambulance in ambulances
        if ambulance["status"] == "available"
    ]


def get_ambulance(ambulance_id):

    refresh_from_database()

    return next(
        (
            ambulance
            for ambulance in ambulances
            if ambulance["id"] == ambulance_id
        ),
        None
    )


def update_ambulance(
    ambulance_id,
    **updates
):

    from backend.services import repository

    ambulance = get_ambulance(
        ambulance_id
    )

    if not ambulance:
        return None

    new_status = updates.get(
        "status",
        ambulance["status"]
    )

    new_location = updates.get(
        "location",
        ambulance["location"]
    )

    repository.update_ambulance_status(
        ambulance_id,
        new_status,
        new_location
    )

    refresh_from_database()

    return get_ambulance(
        ambulance_id
    )


# ==========================================
# ROADS
# ==========================================

def update_road(
    from_node,
    to_node,
    status
):

    from backend.services.database import execute

    matching = rows("""
        SELECT id
        FROM roads
        WHERE
        (from_node=? AND to_node=?)
        OR
        (from_node=? AND to_node=?)
    """, (
        from_node,
        to_node,
        to_node,
        from_node
    ))

    if not matching:
        return False

    for road in matching:

        execute("""
            UPDATE roads
            SET status=?
            WHERE id=?
        """, (
            status,
            road["id"]
        ))

    refresh_from_database()

    return True