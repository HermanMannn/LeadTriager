# Lead Triager 🌍📬

An AI-powered multilingual lead triaging agent that automatically categorizes incoming client emails by type and priority, then logs them as structured tasks in a Notion CRM — no manual sorting required.

## What It Does

When a client sends an email, the agent will:

1. **Detect** the language of the inquiry (English, Arabic, French, Spanish, and more)
2. **Categorize** it into Billing, Support, Sales, or General
3. **Prioritize** it as Urgent, Normal, or Low
4. **Summarize** the inquiry in English regardless of original language
5. **Create a structured page** in your Notion CRM database automatically

---

## Architecture

```
Incoming Email (Gmail)
        ↓
    Make.com
    Watch Emails trigger
        ↓
    HTTP POST to FastAPI /api/triage
        ↓
    CrewAI Agent (Gemini 2.5 Flash)
    Multilingual Lead Triager
        ↓
    Notion CRM Database
    (Category, Priority, Language, Summary, Original Message)
```

---

## Stack

| Layer | Tech |
|---|---|
| AI Agent | [CrewAI](https://crewai.com) |
| LLM | Google Gemini 2.5 Flash |
| API Server | FastAPI + Uvicorn |
| Workflow Automation | [Make.com](https://make.com) |
| Email Provider | Gmail |
| CRM | [Notion](https://notion.so) |
| Tunnel (dev) | ngrok |

---

## Prerequisites

- Python 3.10+
- A [Make.com](https://make.com) account
- A Gmail account connected to Make.com
- A Notion account with an integration set up
- Google Gemini API key
- ngrok installed

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/yourusername/lead-triager.git
cd lead-triager
pip install -r requirements.txt
```

### 2. Create your `.env` file

```env
GEMINI_API_KEY=your-gemini-api-key
NOTION_TOKEN=secret_your-notion-integration-token
NOTION_DATABASE_ID=your-32-character-database-id
```

> ⚠️ `NOTION_DATABASE_ID` is just the 32-character ID — not the full URL. Strip everything after `?v=...`

### 3. Set up your Notion database

Create a Notion database with these exact properties:

| Property | Type |
|---|---|
| Title | Title |
| Sender Name | Text |
| Category | Select |
| Priority | Select |
| Language | Select |
| Summary | Text |
| Original Message | Text |
| Status | Select |

Pre-populate your Select options:
- **Category**: Billing, Support, Sales, General
- **Priority**: Urgent, Normal, Low
- **Status**: New, In Progress, Resolved

### 4. Connect Notion integration to your database

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) and create an integration
2. Copy the **Internal Integration Token** (starts with `secret_`)
3. Open your Notion database → `...` menu → **Connections** → add your integration

### 5. Set up Make.com scenario

1. Create a new scenario in Make.com
2. Add **Gmail → Watch Emails** as the first module
3. Add **HTTP → Make a request** as the second module:
   - URL: `https://your-ngrok-url/api/triage`
   - Method: `POST`
   - Body content type: `application/json`
   - Body input method: `Key-Value`
   - Add these 4 key-value pairs:

| Key | Value |
|---|---|
| `sender_email` | `1. From (email)` |
| `sender_name` | `1. From (name)` |
| `subject` | `1. Subject` |
| `body` | `1. Full text body` |

> ⚠️ Use **Key-Value** mode, not JSON string — email bodies contain special characters that break raw JSON strings in Make.com.

4. Send the test email to Gmail **first**, then click **Run once** — Make.com picks up emails that already arrived, it doesn't wait for new ones.
5. Activate the scenario

---

## Running

```bash
# Terminal 1 — Lead Triager API
python triage.py

# Terminal 2 — ngrok tunnel
ngrok http 8001
```

Copy the ngrok URL and paste it into your Make.com HTTP module.

### One-click startup

Add to your `start.bat`:
```bat
start "Lead Triager" cmd /k "cd /d %~dp0 && python triage.py"
start "ngrok" cmd /k "cd /d %~dp0 && ngrok http 8001"
```

---

## Testing

Send these emails to your connected Gmail to verify the agent works:

**Test 1 — Urgent Billing (English)**
```
Subject: I was charged twice this month
Body: Hi, I just noticed two charges on my credit card for the same subscription 
this month. This needs to be fixed immediately or I will dispute the charge with my bank.
```

**Test 2 — Support, Normal (French)**
```
Subject: Problème de connexion
Body: Bonjour, je n'arrive pas à me connecter à mon compte depuis hier. 
J'ai essayé de réinitialiser mon mot de passe mais je ne reçois pas l'email de confirmation.
```

**Test 3 — Sales, Low (Arabic)**
```
Subject: استفسار عن الخطط
Body: مرحباً، أنا مهتم بمعرفة المزيد عن خططكم وأسعاركم. هل يمكنكم إرسال مزيد من المعلومات؟
```

Each should create a new page in your Notion database with the correct category, priority, and language detected automatically.

---

## How the Agent Works

A single CrewAI agent powered by Gemini 2.5 Flash reads the raw email and returns a structured JSON object:

```json
{
  "language": "French",
  "category": "Support",
  "priority": "Normal",
  "summary": "Client cannot log in and is not receiving password reset emails."
}
```

The agent is prompted to handle any language and always return the summary in English, making it easy for your team to triage without needing to read the original language.

The FastAPI endpoint accepts both `application/json` and `application/x-www-form-urlencoded` content types, making it compatible with Make.com's Key-Value body mode out of the box.

---

## Project Structure

```
lead-triager/
├── triage.py        # FastAPI server + CrewAI agent logic
├── start.bat        # One-click startup script
├── requirements.txt # Python dependencies
├── .env             # API keys (never commit this)
├── .env.example     # Template for .env
└── README.md
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key from [aistudio.google.com](https://aistudio.google.com) |
| `NOTION_TOKEN` | Notion integration token from [notion.so/my-integrations](https://www.notion.so/my-integrations) |
| `NOTION_DATABASE_ID` | 32-character ID of your Notion database (no `?v=` suffix) |

---

## Supported Languages

The agent can detect and process inquiries in any language Gemini supports, including but not limited to English, Arabic, French, Spanish, German, Italian, Portuguese, Chinese, Japanese, and Korean. Summaries are always returned in English.

---

## License

MIT
