import os
import json
import urllib.request
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()

app = FastAPI(title="Lead Triager")

gemini_llm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0.1,
    api_key=os.environ.get("GEMINI_API_KEY")
)

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")


class InquiryRequest(BaseModel):
    sender_email: str
    sender_name: str = "Unknown"
    subject: str = ""
    body: str


def create_notion_page(sender_email: str, sender_name: str, subject: str,
                        original_body: str, language: str, category: str,
                        priority: str, summary: str):
    payload = json.dumps({
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {
                "title": [{"text": {"content": subject or f"Inquiry from {sender_name}"}}]
            },
            "Sender Name": {
                "rich_text": [{"text": {"content": sender_name or "Unknown"}}]
            },
            "Category": {
                "select": {"name": category}
            },
            "Priority": {
                "select": {"name": priority}
            },
            "Language": {
                "select": {"name": language}
            },
            "Summary": {
                "rich_text": [{"text": {"content": summary}}]
            },
            "Original Message": {
                "rich_text": [{"text": {"content": original_body[:2000]}}]
            },
            "Status": {
                "select": {"name": "New"}
            }
        }
    }).encode()

    req = urllib.request.Request(
        "https://api.notion.com/v1/pages",
        data=payload,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    )
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Notion error detail: {error_body}")
        raise


def run_triage(sender_email: str, sender_name: str, subject: str, body: str):
    try:
        triage_agent = Agent(
            role="Multilingual Lead Triager",
            goal="Analyze client inquiries in any language and extract structured information.",
            backstory="""You are an expert at reading client emails in any language. 
            You detect the language, understand the intent, and classify inquiries accurately 
            regardless of whether they are in English, Arabic, French, Spanish, or any other language.""",
            verbose=True,
            llm=gemini_llm
        )

        triage_task = Task(
            description=f"""Analyze this client inquiry and return ONLY a JSON object, nothing else.

Sender: {sender_name} <{sender_email}>
Subject: {subject}
Message: {body}

Classify into:
- language: the language the email is written in (e.g. English, Arabic, French, Spanish)
- category: one of [Billing, Support, Sales, General]
  - Billing: payment issues, invoices, refunds, pricing questions
  - Support: technical issues, bugs, how-to questions, product problems
  - Sales: new purchase interest, demos, partnerships, upgrade inquiries
  - General: everything else
- priority: one of [Urgent, Normal, Low]
  - Urgent: angry tone, service down, legal threat, deadline mentioned
  - Normal: standard request needing a response
  - Low: general curiosity, no clear action needed
- summary: a single sentence in English summarizing the inquiry

Return ONLY this JSON with no extra text or markdown:
{{"language": "...", "category": "...", "priority": "...", "summary": "..."}}""",
            expected_output='A JSON object with keys: language, category, priority, summary',
            agent=triage_agent
        )

        crew = Crew(
            agents=[triage_agent],
            tasks=[triage_task],
            process=Process.sequential
        )

        result = crew.kickoff()
        raw = str(result).strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)

        create_notion_page(
            sender_email=sender_email,
            sender_name=sender_name,
            subject=subject,
            original_body=body,
            language=data.get("language", "Unknown"),
            category=data.get("category", "General"),
            priority=data.get("priority", "Normal"),
            summary=data.get("summary", "No summary available.")
        )

        print(f"✅ Triaged inquiry from {sender_email} → {data.get('category')} / {data.get('priority')}")

    except Exception as e:
        print(f"❌ Triage failed for {sender_email}: {str(e)}")


@app.post("/api/triage")
def triage_inquiry(request: InquiryRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        run_triage,
        request.sender_email,
        request.sender_name,
        request.subject,
        request.body
    )
    return {"status": "ok", "message": f"Triaging inquiry from {request.sender_email}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="::", port=5678)