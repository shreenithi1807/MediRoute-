from backend.services.database import rows, execute, now


# =========================================================
# AMBULANCES
# =========================================================

def get_ambulances():
    return rows(
        "SELECT * FROM ambulances ORDER BY id"
    )


def available_ambulances():
    return rows("""
        SELECT *
        FROM ambulances
        WHERE status = 'available'
        ORDER BY id
    """)


def save_ambulance(data):
    execute("""
        INSERT INTO ambulances(
            id,
            location,
            status,
            latitude,
            longitude
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(id) DO UPDATE SET
            location = excluded.location,
            status = excluded.status,
            latitude = excluded.latitude,
            longitude = excluded.longitude
    """, (
        data["id"],
        data["location"],
        data.get("status", "available"),
        data.get("latitude"),
        data.get("longitude")
    ))


def update_ambulance_status(
    ambulance_id,
    status,
    location=None
):
    if location is not None:

        execute("""
            UPDATE ambulances
            SET status = ?,
                location = ?
            WHERE id = ?
        """, (
            status,
            location,
            ambulance_id
        ))

    else:

        execute("""
            UPDATE ambulances
            SET status = ?
            WHERE id = ?
        """, (
            status,
            ambulance_id
        ))


# =========================================================
# HOSPITALS
# =========================================================

def get_hospitals():
    return rows(
        "SELECT * FROM hospitals ORDER BY name"
    )


def save_hospital(data):
    execute("""
        INSERT INTO hospitals (
            name,
            location,
            beds,
            icu,
            trauma
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(name) DO UPDATE SET
            location = excluded.location,
            beds = excluded.beds,
            icu = excluded.icu,
            trauma = excluded.trauma
    """, (
        data["name"],
        data["location"],
        int(data.get("beds", 0)),
        int(data.get("icu", 0)),
        int(data.get("trauma", 0))
    ))

def get_hospital(name):
    result = rows("""
        SELECT *
        FROM hospitals
        WHERE name = ?
        LIMIT 1
    """, (name,))

    return result[0] if result else None


def hospital_incoming_cases(hospital_name):
    return rows("""
        SELECT
            a.id AS assignment_id,
            a.emergency_id,
            a.ambulance_id,
            a.hospital_name,
            a.route,
            a.eta_minutes,
            a.status AS assignment_status,
            a.created_at,

            e.location AS emergency_location,
            e.emergency_type,
            e.severity,
            e.required_facility,
            e.status AS emergency_status,
            e.latitude,
            e.longitude

        FROM assignments a

        JOIN emergencies e
            ON e.id = a.emergency_id

        WHERE a.hospital_name = ?

        AND a.status IN (
            'assigned',
            'en_route',
            'with_patient',
            'at_hospital'
        )

        AND e.status != 'cancelled'

        ORDER BY
            e.severity DESC,
            a.id DESC
    """, (hospital_name,))
# =========================================================
# ROADS
# =========================================================

def get_roads():
    return rows(
        "SELECT * FROM roads ORDER BY id"
    )


def execute_road_import(
    from_node,
    to_node,
    distance,
    traffic,
    status
):
    execute("""
        INSERT INTO roads(
            from_node,
            to_node,
            distance,
            traffic,
            status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        from_node,
        to_node,
        distance,
        traffic,
        status
    ))


def update_road(
    road_id,
    status,
    traffic=None
):
    if traffic is None:

        execute("""
            UPDATE roads
            SET status = ?
            WHERE id = ?
        """, (
            status,
            road_id
        ))

    else:

        execute("""
            UPDATE roads
            SET status = ?,
                traffic = ?
            WHERE id = ?
        """, (
            status,
            traffic,
            road_id
        ))


# =========================================================
# EMERGENCIES
# =========================================================

def save_emergency(emergency):
    execute("""
        INSERT INTO emergencies(
            id,
            location,
            emergency_type,
            severity,
            required_facility,
            status,
            latitude,
            longitude,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        emergency["id"],
        emergency["location"],
        emergency["type"],
        int(emergency["severity"]),
        emergency.get(
            "required_facility",
            ""
        ),
        emergency.get(
            "status",
            "waiting"
        ),
        emergency.get("latitude"),
        emergency.get("longitude"),
        now()
    ))


def get_emergencies():
    return rows("""
        SELECT *
        FROM emergencies
        ORDER BY created_at DESC
    """)


def waiting_emergencies():
    return rows("""
        SELECT *
        FROM emergencies
        WHERE status = 'waiting'
        ORDER BY severity DESC,
                 created_at ASC
    """)


def update_emergency_status(
    emergency_id,
    status
):
    execute("""
        UPDATE emergencies
        SET status = ?
        WHERE id = ?
    """, (
        status,
        emergency_id
    ))


def update_patient_location(
    emergency_id,
    latitude,
    longitude
):
    execute("""
        UPDATE emergencies
        SET latitude = ?,
            longitude = ?
        WHERE id = ?
    """, (
        latitude,
        longitude,
        emergency_id
    ))


# =========================================================
# ASSIGNMENTS
# =========================================================

def create_assignment(
    emergency_id,
    ambulance_id,
    hospital_name,
    route,
    eta
):
    return execute("""
        INSERT INTO assignments(
            emergency_id,
            ambulance_id,
            hospital_name,
            route,
            eta_minutes,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        emergency_id,
        ambulance_id,
        hospital_name,
        route,
        eta,
        "assigned",
        now()
    ))


def assignments():
    return rows("""
        SELECT *
        FROM assignments
        ORDER BY id DESC
    """)


def assignment_for_ambulance(ambulance_id):
    result = rows("""
        SELECT *
        FROM assignments
        WHERE ambulance_id = ?
        AND status IN (
            'assigned',
            'en_route',
            'with_patient',
            'at_hospital'
        )
        ORDER BY id DESC
        LIMIT 1
    """, (
        ambulance_id,
    ))

    if result:
        return result[0]

    return None

def update_assignment_status(
    assignment_id,
    status
):
    execute("""
        UPDATE assignments
        SET status = ?
        WHERE id = ?
    """, (
        status,
        assignment_id
    ))


def timeout_assignment(
    assignment_id
):
    execute("""
        UPDATE assignments
        SET status = 'timed_out'
        WHERE id = ?
    """, (
        assignment_id,
    ))
def get_emergency(emergency_id):
    result = rows("""
        SELECT *
        FROM emergencies
        WHERE id = ?
        LIMIT 1
    """, (emergency_id,))

    return result[0] if result else None


def update_ambulance_location(
    ambulance_id,
    latitude,
    longitude
):
    execute("""
        UPDATE ambulances
        SET latitude = ?,
            longitude = ?
        WHERE id = ?
    """, (
        latitude,
        longitude,
        ambulance_id
    ))


def get_ambulance(ambulance_id):
    result = rows("""
        SELECT *
        FROM ambulances
        WHERE id = ?
        LIMIT 1
    """, (ambulance_id,))

    return result[0] if result else None


def assignment_for_emergency(emergency_id):
    result = rows("""
        SELECT *
        FROM assignments
        WHERE emergency_id = ?
        AND status IN (
            'assigned',
            'en_route',
            'with_patient',
            'at_hospital'
        )
        ORDER BY id DESC
        LIMIT 1
    """, (
        emergency_id,
    ))

    if result:
        return result[0]

    return None
def delete_ambulance(ambulance_id):
         execute(
               "DELETE FROM ambulances WHERE id = ?",
                (ambulance_id,)
         )
def cancel_emergency(emergency_id):
    assignment = assignment_for_emergency(emergency_id)

    execute(
        """
        UPDATE emergencies
        SET status = 'cancelled'
        WHERE id = ?
        """,
        (emergency_id,)
    )

    if assignment:
        ambulance_id = assignment["ambulance_id"]

        execute(
            """
            UPDATE assignments
            SET status = 'completed'
            WHERE id = ?
            """,
            (assignment["id"],)
        )

        execute(
            """
            UPDATE ambulances
            SET status = 'available'
            WHERE id = ?
            """,
            (ambulance_id,)
        )

    return True