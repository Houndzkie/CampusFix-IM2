from django.db import migrations, models


def migrate_workflow_roles_and_statuses(apps, schema_editor):
    User = apps.get_model("home", "User")
    RepairRequest = apps.get_model("home", "RepairRequest")
    RequestPhoto = apps.get_model("home", "RequestPhoto")

    User.objects.filter(role="staff").update(role="maintenance_staff")

    RepairRequest.objects.filter(status="open").update(status="pending")
    RepairRequest.objects.filter(status="on_hold").update(status="pending")
    RepairRequest.objects.filter(status__in=["resolved", "closed"]).update(status="finished")
    RepairRequest.objects.filter(status="in_progress").update(status="in_progress")

    RequestPhoto.objects.exclude(photo_type="proof").update(photo_type="issue")


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0002_remove_category_and_seed_locations"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("student", "Student"),
                    ("faculty", "Faculty"),
                    ("maintenance_staff", "Maintenance Staff"),
                    ("admin", "Administrator"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="repairrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("in_progress", "In Progress"),
                    ("finished", "Finished"),
                ],
                max_length=15,
            ),
        ),
        migrations.RunPython(migrate_workflow_roles_and_statuses, migrations.RunPython.noop),
    ]
