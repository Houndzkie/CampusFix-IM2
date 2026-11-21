# CampusFix JOIN and SUBQUERY Demo

## Before recording

- Start CampusFix with the project `.env` configured for Supabase. Never show the `.env` contents, password, or other credentials in the recording.
- Sign in with an authorized Django staff or superuser account. The Reports page is restricted to accounts with Django staff privileges.
- At the time this script was prepared, Supabase had 3 ordinary users, no staff/superuser accounts, no seeded campus locations, and no repair requests. The query pages will be empty until the demo data is added.
- Prepare data in Supabase before recording:
  1. If there is no authorized admin account, run `python manage.py createsuperuser` from the project root. This project assigns the default `admin` role to a superuser.
  2. Confirm the migration seeded the RTL, NGE, GLE, and ACAD buildings and rooms 101–105, 201–205, 301–305, and 401–405.
  3. Register a reporter account and submit two repair requests through CampusFix.
  4. As staff, leave one request open and move the other to in progress. Optionally create a separate closed request to show it is excluded from the report.
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
“The Active Reporters report only lists users whose IDs appear in active repair requests. The inner query selects reporter IDs for open, in-progress, or on-hold requests. The outer query filters users using those IDs and counts each user’s active requests.”

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
