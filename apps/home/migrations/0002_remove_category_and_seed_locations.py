from django.db import migrations, models


BUILDING_CODES = ("RTL", "NGE", "GLE", "ACAD")
ROOM_NAMES = (
    "101", "102", "103", "104", "105",
    "201", "202", "203", "204", "205",
    "301", "302", "303", "304", "305",
    "401", "402", "403", "404", "405",
)


def seed_campus_locations(apps, schema_editor):
    Building = apps.get_model("home", "Building")
    Room = apps.get_model("home", "Room")

    for building_code in BUILDING_CODES:
        building, _ = Building.objects.update_or_create(
            building_code=building_code,
            defaults={
                "building_name": building_code,
                "total_floors": 4,
            },
        )
        for room_name in ROOM_NAMES:
            Room.objects.update_or_create(
                building=building,
                room_name=room_name,
                defaults={
                    "floor_number": int(room_name[0]),
                    "room_type": "Classroom",
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="repairrequest",
            name="category",
        ),
        migrations.DeleteModel(
            name="Category",
        ),
        migrations.RunPython(seed_campus_locations, migrations.RunPython.noop),
    ]
