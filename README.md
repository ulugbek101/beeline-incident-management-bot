# Incident Management Bot

A Telegram bot for managing workplace incidents. Users scan QR codes placed on building floors, register once, and submit incident reports with text, photos, video, or voice. Incidents are forwarded to a designated Telegram group where staff can mark them as resolved. An Excel export command gives admins a full incident log.

---

## Features

- **QR code-based registration** — QR codes encode floor numbers; scanning one starts the flow automatically
- **One-time user registration** — full name and Uzbekistan phone number, stored permanently
- **Rich incident submission** — supports text, photos, documents, video, round-video notes, and voice messages with optional captions
- **Group notifications** — each incident is forwarded to a configured Telegram group with a "Report Resolution" inline button
- **Incident resolution tracking** — any group member can click the button; the bot records who solved it and notifies the reporter
- **Excel statistics export** — `/send_stats` generates a colour-coded `.xlsx` with all incidents, user details, and resolution status
- **Fully async** — built on aiogram 3 and asyncpg, no blocking I/O
- **Dockerised** — single `docker compose up` starts the bot and a PostgreSQL 16 database

---

## Tech Stack

| Layer | Technology |
|---|---|
| Bot framework | [aiogram 3.28](https://docs.aiogram.dev/) |
| Database | PostgreSQL 16 via [asyncpg](https://magicstack.github.io/asyncpg/) |
| Excel export | [openpyxl](https://openpyxl.readthedocs.io/) |
| Async file I/O | aiofiles |
| Configuration | environs / python-dotenv |
| Containerisation | Docker + Docker Compose |
| Runtime | Python 3.12 |

---

## Project Structure

```
.
├── app.py                          # Entry point — connects DB, registers commands, starts polling
├── config.py                       # Loads environment variables
├── loader.py                       # Creates Bot, Dispatcher, and Database instances
├── router.py                       # Top-level aiogram router
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env                            # Secret configuration (see Configuration section)
│
├── handlers/
│   ├── start.py                    # /start and /create_incident — QR validation, routing
│   ├── user_registration.py        # FSM: collect full name → phone number → save user
│   ├── incident_registration.py    # FSM: collect floor (if no QR) → collect incident content
│   ├── incident_finish.py          # Inline button callback — mark incident as solved
│   ├── send_stats.py               # /send_stats — generate and send Excel report
│   └── cancel.py                   # Cancel button handler — clears FSM state
│
├── states/
│   └── forms.py                    # UserRegistrationForm and IncidentRegistrationForm states
│
├── utils/
│   ├── commands.py                 # Registers bot commands in Telegram
│   └── db_api/
│       └── db.py                   # Database wrapper (asyncpg connection pool + all queries)
│
└── media/                          # Uploaded photos, documents, videos, voice messages
```

---

## Database Schema

### `users`

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Internal user ID |
| `telegram_id` | TEXT UNIQUE | Telegram user ID |
| `fullname` | TEXT | User's full name |
| `phone_number` | TEXT | Phone in `9XXXXXXXX` format |

### `incidents`

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Incident ID |
| `user_id` | INT → users.id | Who reported it |
| `incident_description_type` | TEXT | `text`, `photo`, `document`, `voice`, `video`, `video_note` |
| `incident` | TEXT | Description text or path to saved media file |
| `document_caption` | TEXT | Optional caption when media was submitted |
| `floor` | INT | Floor number from QR code or manual input |
| `is_solved` | BOOLEAN | Resolution status (default `false`) |
| `solved_by` | INT → users.id | Who resolved it (nullable) |
| `datetime` | TIMESTAMP | When the incident was created |

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Start the bot or start a new incident (accepts QR floor number as argument) |
| `/create_incident` | Create an incident (accepts QR floor number as argument) |
| `/send_stats` | Export all incidents to Excel (group or private) |
| `/help` | Show help message |

---

## User Flows

### New user with QR code
```
User scans QR → /start <floor>
  → Not registered → Registration flow
      → Enter full name
      → Enter / share phone number
  → Registered automatically → Incident flow
      → Send description / photo / video / voice
  → Bot saves incident, confirms to user
  → Bot forwards to group with [Report Resolution] button
```

### Returning user
```
User sends /create_incident <floor>  OR  /start <floor>
  → Already registered → Incident flow (no re-registration)
      → Send description / photo / video / voice
  → Bot saves incident, confirms to user
  → Bot forwards to group with [Report Resolution] button
```

### Without QR code
```
User sends /start or /create_incident (no floor arg)
  → Bot asks to scan a QR code first
```

### Resolving an incident (group member)
```
Group member clicks [📝 Report Resolution] on incident message
  → Bot updates incident: is_solved=true, solved_by=<user>
  → Button changes to [Solved ✅]
  → Notification sent to group and to the original reporter
```

---

## Configuration

All configuration is via environment variables. Create a `.env` file in the project root:

```dotenv
# Telegram Bot Token from @BotFather
TOKEN=your_bot_token_here

# Telegram group/supergroup ID where incidents are forwarded
# Supergroup IDs are negative numbers, e.g. -1001234567890
GROUP_ID=-1001234567890

# PostgreSQL connection details
DB_NAME=incident_management_db
DB_USER=incident_management_db_user
DB_PASSWORD=your_secure_password
DB_HOST=db          # Use "db" for Docker, "localhost" for local dev
DB_PORT=5432

# Directory for storing uploaded media files
MEDIA_DIR=media/

# Comma-separated Telegram IDs of admins (reserved for future use)
ADMINS=123456789
```

### Getting the GROUP_ID

1. Add your bot to the target group and make it an admin.
2. Send any message in the group.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser.
4. Look for `"chat":{"id":...}` — the negative number is the group ID.

---

## Launch Instructions

### Option 1 — Docker Compose (recommended)

**Requirements:** Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone <repo-url>
cd "Incident management bot"

# 2. Create and fill in the .env file
cp .env.example .env   # or create it manually (see Configuration above)

# 3. Build and start all services (bot + PostgreSQL)
docker compose up --build

# To run in the background
docker compose up --build -d

# View logs
docker compose logs -f bot

# Stop all services
docker compose down

# Stop and remove database volume (full reset)
docker compose down -v
```

The bot creates all database tables automatically on first start, including a migration to add the `document_caption` column if upgrading from an older version.

---

### Option 2 — Local Python Environment

**Requirements:** Python 3.12+, PostgreSQL running locally.

```bash
# 1. Clone the repository
git clone <repo-url>
cd "Incident management bot"

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up PostgreSQL
#    Create a database and user matching your .env values:
psql -U postgres -c "CREATE USER incident_management_db_user WITH PASSWORD 'your_secure_password';"
psql -U postgres -c "CREATE DATABASE incident_management_db OWNER incident_management_db_user;"

# 5. Create the .env file (see Configuration above)
#    Set DB_HOST=localhost for local development

# 6. Create the media directory
mkdir -p media

# 7. Run the bot
python app.py
```

---

## QR Code Setup

Each QR code should encode a plain integer representing the floor number, formatted as a Telegram deep-link:

```
https://t.me/<bot_username>?start=<floor_number>
```

**Example** for floor 3 with bot `@MyIncidentBot`:
```
https://t.me/MyIncidentBot?start=3
```

Generate QR codes for each floor using any QR generator and print/place them on that floor. When a user scans the code with Telegram's camera, the bot receives `/start 3` and proceeds automatically.

---

## Excel Report (`/send_stats`)

The exported file contains one sheet with the following columns:

| Column | Description |
|---|---|
| ID | Incident ID |
| ФИО пользователя | Reporter full name |
| Телефон пользователя | Reporter phone (`+998 (XX) XXX-XX-XX`) |
| Тип обращения | Content type (text / photo / document / …) |
| Обращение | Description or media file path |
| Этаж | Floor number |
| Решён | Yes / No |
| ФИО решившего | Resolver full name |
| Телефон решившего | Resolver phone |
| Дата регистрации | Timestamp |

**Colour coding:**
- Header row — blue background
- Solved incidents — green background
- Unsolved incidents — red background

---

## Media Storage

Uploaded files are saved under the `MEDIA_DIR` directory (default `media/`) with the naming pattern `<file_id>.<ext>`. Supported extensions:

| Type | Extension |
|---|---|
| Photo | `.jpg` |
| Document | original extension from Telegram |
| Video | `.mp4` |
| Video note | `.mp4` |
| Voice | `.mp3` |

The saved relative path is stored in the `incidents.incident` column. Make sure the `media/` directory is persisted (via Docker volume or local filesystem) to avoid losing files on restart.

---

## Environment Notes

- The bot uses **MemoryStorage** for FSM — all in-progress conversation states are lost on restart. Users will need to re-initiate their flow.
- The bot filters incoming messages to **private chats only** for registration and incident submission. Group chats are used only for notifications and the resolution button.
- Phone numbers are validated as exactly 9 digits (Uzbekistan mobile format). The stored value is the raw 9-digit string; the Excel export formats it as `+998 (XX) XXX-XX-XX`.
