# CampusFix JOIN and SUBQUERY Demo

## Before recording

- Start CampusFix with the project `.env` configured for Supabase. Never show the `.env` contents, password, or other credentials in the recording.
- Sign in with an authorized Django staff or superuser account. The Reports page is restricted to accounts with Django staff privileges.
- Supabase has been reset and is ready for fresh demo accounts and repair requests. Create a Student, Faculty, and Maintenance Staff account with a contact number for each. Reporter submissions require at least one issue photo.
- Prepare data in Supabase before recording:
  1. If there is no authorized admin account, run `python manage.py createsuperuser` from the project root. This project assigns the default `admin` role to a superuser.
  2. Confirm the migration seeded the RTL, NGE, GLE, and ACAD buildings and rooms 101–105, 201–205, 301–305, and 401–405.
  3. Register a Student or Faculty reporter account with a contact number, then submit two repair requests with issue photos.
  4. Show that the reporter can edit a request until Maintenance Staff takes it.
  5. Register or create a Maintenance Staff account, take one request, and show the reporter and assigned maintenance profiles as clickable links.
  6. Upload 1–5 completion proof photos and finish the request.
  7. Visit each profile to show reported/resolved counts for Student/Faculty and active/finished task counts for Maintenance Staff.
- Run `python manage.py showmigrations` and confirm migrations are applied. Do not use the reset scripts.
- Use a browser window with a readable resolution and close unrelated windows.

## Suggested recording flow (about 4–5 minutes)

### 1. Introduction (0:00–0:20)

**Show:** CampusFix login page or dashboard.

**Say:**
“This is CampusFix, a maintenance and repair request system built with Django and connected to Supabase PostgreSQL. I’ll demonstrate a JOIN in the ticket list and a SUBQUERY report for users with active repair requests.”

### 2. JOIN implementation (0:20–1:45)

**Show:** Sign in as staff and open **Tickets**. Point out a ticket’s room/building and reporter.

**Say:**
“Each repair request is related to a reporter and a room. Each room is related to a building. The ticket list combines these related records so staff can see the full report in one row. Django’s `select_related()` generates SQL JOINs for this view.”

**Show the generated JOIN SQL:** In a terminal at the project root, run:

```powershell
python manage.py shell
```

Then enter:

```python
from apps.home.models import RepairRequest

tickets = RepairRequest.objects.select_related(
    "reporter", "assigned_staff", "room__building"
).order_by("-created_at")

print(tickets.query)
```

**Say:**
“The SQL shows joins from `repair_request` to `user`, `room`, and `building`. These are the same related values displayed in the ticket list.”

### 3. SUBQUERY implementation (1:45–3:10)

**Show:** Return to CampusFix and open **Reports**. Point out the reporters and active-ticket counts.

**Say:**
“The Active Reporters report only lists users whose IDs appear in active repair requests. The inner query selects reporter IDs for pending or in-progress requests. The outer query filters users by those IDs and counts each user’s active requests.”

**Show the generated SUBQUERY SQL:** In the same Django shell, enter:

```python
from apps.tickets.views import active_reporters_queryset

reporters = active_reporters_queryset()
print(reporters.query)
```

**Say:**
“The generated SQL contains an `IN (SELECT ...)` subquery over `repair_request`. The results on screen come from that query.”

Type `exit()` to leave the shell.

### 4. Supabase verification (3:10–4:00)

**Show:** In the Supabase dashboard, open the relevant tables in the Table Editor:

- `repair_request`
- `user`
- `room`
- `building`

**Say:**
“These are the tables used by the app. `repair_request.reporter_id` references `user.user_id`, and `room_id` references `room.room_id`. The room’s `building_id` references `building.building_id`. The records shown in CampusFix are retrieved from these Supabase tables.”

### 5. Closing (4:00–4:15)

**Say:**
“This demonstrates one functional JOIN and one functional SUBQUERY, both integrated into CampusFix and retrieving data through Django from Supabase PostgreSQL.”

Upload the finished recording to the platform required by your course and submit the shareable video link. Do not include passwords or connection strings in the recording.
