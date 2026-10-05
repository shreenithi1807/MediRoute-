from backend.services import data_service as ds
from backend.services import repository
from backend.services.database import rows


def migrate_existing_data():

    # -------------------------
    # AMBULANCES
    # -------------------------

    existing = rows(
        "SELECT COUNT(*) AS count FROM ambulances"
    )

    if existing[0]["count"] == 0:

        for ambulance in ds.ambulances:

            repository.save_ambulance({
                "id": ambulance["id"],
                "location": ambulance["location"],
                "status": ambulance.get(
                    "status",
                    "available"
                )
            })

        print(
            f"Imported {len(ds.ambulances)} ambulances."
        )


    # -------------------------
    # HOSPITALS
    # -------------------------

    existing = rows(
        "SELECT COUNT(*) AS count FROM hospitals"
    )

    if existing[0]["count"] == 0:

        for hospital in ds.hospitals:

            repository.save_hospital({
                "name": hospital["name"],
                "location": hospital["location"],
                "beds": hospital.get("beds", 0),
                "icu": hospital.get("icu", False),
                "trauma": hospital.get(
                    "trauma",
                    False
                )
            })

        print(
            f"Imported {len(ds.hospitals)} hospitals."
        )


        # -------------------------
    # ROADS
    # -------------------------

    existing = rows(
        "SELECT COUNT(*) AS count FROM roads"
    )

    if existing[0]["count"] == 0:

        for road in ds.roads:

            repository.execute_road_import(
                from_node=road["from"],
                to_node=road["to"],
                distance=road.get(
                    "distance",
                    road.get("weight", 1)
                ),
                traffic=road.get(
                    "traffic",
                    1
                ),
                status=road.get(
                    "status",
                    "open"
                )
            )

        print(
            f"Imported {len(ds.roads)} roads."
        )