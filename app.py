"""
DeadlineAI - Last-Minute Life Saver
Vibe2Ship Hackathon 2026 | Coding Ninjas x Google for Developers
Builder: Dheer Parekh | Ramdeobaba University, Nagpur
"""

import json
import os
import re
import uuid
from datetime import datetime, timedelta
from functools import wraps
from html import escape

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, render_template_string, request, session, url_for
from google import genai
from google.genai import types
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "deadlineai-dev-secret-change-me")

MODEL_NAME = "gemini-2.0-flash"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

DEMO_USER = os.environ.get("DEADLINEAI_USER", "demo")
DEMO_PASSWORD_HASH = generate_password_hash(os.environ.get("DEADLINEAI_PASSWORD", "deadline123"))


SYSTEM_INSTRUCTION = """
You are DeadlineAI - a calm, brilliant best friend who is exceptionally good at time management and getting people unstuck.

You are NOT a corporate assistant. You are NOT a generic productivity chatbot.
You talk like a smart friend who genuinely cares - someone who looks at a messy situation, takes a breath, and says:
"Okay, I've got you. Here's exactly what we're doing."

== YOUR PERSONALITY ==
- Warm but direct. You don't sugarcoat but you never make someone feel stupid or hopeless.
- You briefly acknowledge the stress ("okay that IS a lot, but we can work with this") before immediately solving it.
- You use natural language - "here's what I'd do", "honestly", "the thing is", "don't worry about X right now".
- You're honest. If something genuinely can't be done in the time left, you say so kindly and give damage control.
- You end every response with something real and human - what a good friend would actually say, not a motivational poster.
- Never say "Certainly!", "Great question!", or any robotic filler. Just get into it.

== HOW YOU THINK (do this internally before responding) ==
1. Read the whole situation first. Don't jump to planning immediately.
2. Identify what is ACTUALLY urgent vs what just FEELS urgent.
3. Give realistic time estimates - people always underestimate. Be honest.
4. Build a plan that fits the actual time available, not an ideal world.
5. If there's something important tomorrow (exam, interview, presentation) - protect sleep. Always.
6. If something is impossible, say so. "This one might not happen fully - here's damage control."

== AUTO-DETECT MODE ==

RESCUE MODE - trigger when:
- Any deadline within 6 hours
- User says "tonight", "right now", "only X hours left", "urgent", "emergency", "due in X hours"
- Energy: calm and focused, not panicked. Like a friend who has been in this situation before.

PRIORITY MODE - trigger when:
- Multiple tasks, deadlines spread over days
- No immediate crisis
- Give a clear day-by-day breakdown

OVERWHELM MODE - trigger when:
- 6+ tasks at once
- User says "stressed", "panicking", "don't know where to start", "overwhelmed", "everything at once"
- Start with ONE sentence that acknowledges how they feel. Then immediately take control.

== OUTPUT FORMAT - USE THIS EVERY TIME ==

[One opening line - read the situation back briefly, like a friend would. "Okay so you've got X, Y, and Z - and [time context]. Got it."]

[RESCUE MODE only:]
Rescue mode on. Here's exactly what we're doing:

RIGHT NOW - [Task] (due: [when], ~[realistic time])
   -> [Specific action - what exactly to open, write, do]
   -> [What to skip or cut to save time]

AFTER THAT - [Next urgent task]
   -> [Same level of detail]

[TODAY/TOMORROW] - [Task] (due: [when])
   -> Start: [specific time]
   -> Time needed: ~[estimate]
   -> Focus on: [specific angle, not generic]

THIS WEEK - [Task] (due: [when])
   -> [Brief note on when to fit it in]

YOUR SCHEDULE:
[Time] -> [Task]
[Time] -> [Task]
[If needed:] [Time] -> Sleep. Non-negotiable - [reason why it matters here].

[If a task is impossible:]
Real talk: [task] probably won't happen fully in this time. [Specific damage control.]

[End with what a real friend would say - short, honest, human. Not inspirational. Just real.]

== HARD RULES ==
1. ALWAYS give a RIGHT NOW action - the user should never finish reading without knowing what to do first
2. ALWAYS give time estimates in hours/minutes - never say "spend some time on this"
3. NEVER say "manage your time well", "stay focused", "you've got this!" or any generic filler
4. ALWAYS protect sleep if exam/interview/presentation is the next day
5. Be honest about impossible tasks - give specific damage control, not false reassurance
6. Keep response under 450 words - dense and useful beats long and padded
7. Match tone to context:
   - Student: casual, uses "assignment", "prof", "submit", "marks"
   - Professional: crisp, uses "deliverable", "EOD", "stakeholder", "meeting"
   - Entrepreneur: ruthless prioritization, "what actually moves the needle"
8. In OVERWHELM MODE - one sentence of empathy, then immediately take control
9. The schedule must fit the actual time they have, not a perfect-world scenario
10. Sound like a person, not a tool
"""


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please log in first."}), 401
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def now_utc():
    return datetime.utcnow().replace(microsecond=0)


def parse_json_object(text):
    if not text:
        return {}
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


def gemini_text(prompt, temperature=0.4, max_output_tokens=1200, system_instruction=SYSTEM_INSTRUCTION):
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ),
    )
    return response.text or ""


def gemini_json(prompt, fallback=None):
    try:
        raw = gemini_text(
            prompt,
            temperature=0.15,
            max_output_tokens=900,
            system_instruction="Return only valid JSON. No markdown. No commentary.",
        )
        parsed = parse_json_object(raw)
        return parsed or (fallback or {})
    except Exception:
        return fallback or {}


def clean_task_title(title):
    title = re.sub(r"^[\-\*\d\.\)\s]+", "", title or "").strip()
    title = re.sub(r"^(RIGHT NOW|AFTER THAT|TODAY|TOMORROW|THIS WEEK)\s*[-:]\s*", "", title, flags=re.I)
    return title[:140].strip(" -")


def fallback_tasks_from_plan(plan):
    tasks = []
    seen = set()
    for line in plan.splitlines():
        raw = line.strip()
        if not raw:
            continue
        candidate = raw
        if "->" in candidate:
            candidate = candidate.split("->", 1)[1]
        elif "-" in candidate and re.search(r"\b(RIGHT NOW|AFTER THAT|TODAY|TOMORROW|THIS WEEK)\b", candidate, re.I):
            candidate = candidate.split("-", 1)[1]
        elif not re.search(r"\b(open|write|finish|submit|study|review|send|start|complete|prepare|fix|build)\b", candidate, re.I):
            continue
        title = clean_task_title(re.sub(r"\([^)]*\)", "", candidate))
        key = title.lower()
        if len(title) >= 4 and key not in seen:
            seen.add(key)
            tasks.append(
                {
                    "id": uuid.uuid4().hex[:10],
                    "title": title,
                    "due": "",
                    "estimate_minutes": None,
                    "priority": "normal",
                    "completed": False,
                    "completed_at": None,
                }
            )
        if len(tasks) >= 12:
            break
    return tasks


def extract_tasks(plan):
    prompt = f"""
Extract a practical checkbox task list from this plan.

Return JSON exactly like:
{{
  "tasks": [
    {{
      "title": "short action title",
      "due": "human due time if present, else empty string",
      "estimate_minutes": 45,
      "priority": "high|normal|low"
    }}
  ]
}}

Rules:
- Include only actionable work items the user can check off.
- Keep titles short and specific.
- Maximum 12 tasks.

Plan:
{plan}
"""
    data = gemini_json(prompt, {"tasks": []})
    tasks = data.get("tasks") if isinstance(data, dict) else []
    if not isinstance(tasks, list) or not tasks:
        return fallback_tasks_from_plan(plan)

    normalized = []
    seen = set()
    for task in tasks[:12]:
        if not isinstance(task, dict):
            continue
        title = clean_task_title(task.get("title", ""))
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        estimate = task.get("estimate_minutes")
        try:
            estimate = int(estimate) if estimate not in ("", None) else None
        except (TypeError, ValueError):
            estimate = None
        normalized.append(
            {
                "id": uuid.uuid4().hex[:10],
                "title": title,
                "due": str(task.get("due", "") or "")[:80],
                "estimate_minutes": estimate,
                "priority": task.get("priority", "normal") if task.get("priority") in ("high", "normal", "low") else "normal",
                "completed": False,
                "completed_at": None,
            }
        )
    return normalized or fallback_tasks_from_plan(plan)


def preserve_completed_tasks(new_tasks, old_tasks):
    completed_by_title = {
        task.get("title", "").strip().lower(): task
        for task in old_tasks
        if task.get("completed") and task.get("title")
    }
    for task in new_tasks:
        old = completed_by_title.get(task.get("title", "").strip().lower())
        if old:
            task["completed"] = True
            task["completed_at"] = old.get("completed_at")
    return new_tasks


def extract_calendar_events(plan):
    today = datetime.now().date().isoformat()
    prompt = f"""
Extract calendar events from this DeadlineAI plan.

Today is {today}. Convert relative dates like today/tomorrow/Friday into YYYY-MM-DD when possible.

Return JSON exactly like:
{{
  "events": [
    {{
      "title": "event title",
      "date": "YYYY-MM-DD",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "description": "short note"
    }}
  ]
}}

Rules:
- Include scheduled work blocks and deadlines only.
- If a start time exists but no end time exists, estimate a reasonable end time from the plan.
- If no usable date/time exists, return an empty events array.
- Maximum 20 events.

Plan:
{plan}
"""
    data = gemini_json(prompt, {"events": []})
    events = data.get("events") if isinstance(data, dict) else []
    normalized = []
    for event in events[:20]:
        if not isinstance(event, dict):
            continue
        title = str(event.get("title", "") or "Task").strip()[:120]
        date = str(event.get("date", "") or "").strip()
        start_time = str(event.get("start_time", "") or "").strip()
        end_time = str(event.get("end_time", "") or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            continue
        if not re.match(r"^\d{2}:\d{2}$", start_time):
            continue
        if not re.match(r"^\d{2}:\d{2}$", end_time):
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_time = (start_dt + timedelta(minutes=45)).strftime("%H:%M")
        normalized.append(
            {
                "id": uuid.uuid4().hex[:10],
                "title": title,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "description": str(event.get("description", "") or "")[:300],
            }
        )
    return normalized


def progress_snapshot():
    tasks = session.get("tasks", [])
    total = len(tasks)
    done = len([task for task in tasks if task.get("completed")])
    remaining = total - done
    percent = round((done / total) * 100) if total else 0
    return {"total": total, "done": done, "remaining": remaining, "percent": percent}


def save_plan_state(user_input, plan, old_tasks=None):
    tasks = extract_tasks(plan)
    if old_tasks:
        tasks = preserve_completed_tasks(tasks, old_tasks)
    events = extract_calendar_events(plan)
    started = now_utc()

    session["current_plan"] = plan
    session["current_input"] = user_input
    session["tasks"] = tasks
    session["calendar_events"] = events
    session["plan_started_at"] = started.isoformat()
    session["last_checkin_at"] = None
    session["next_checkin_at"] = (started + timedelta(minutes=25)).isoformat()
    session["completed_summary"] = None
    session.modified = True

    return {
        "plan": plan,
        "tasks": tasks,
        "calendar_events": events,
        "progress": progress_snapshot(),
        "next_checkin_at": session["next_checkin_at"],
        "calendar_url": url_for("calendar_view"),
    }


def build_checkin_message(force=False):
    tasks = session.get("tasks", [])
    progress = progress_snapshot()
    incomplete = [task for task in tasks if not task.get("completed")]

    if not tasks:
        return "No active checklist yet. Build a plan first, then I can check in properly."

    if progress["remaining"] == 0:
        return "Everything is checked off. Hit the summary endpoint and close the loop properly."

    next_task = incomplete[0]
    if force:
        return f"Quick check-in: {progress['done']}/{progress['total']} done. Next tiny move: {next_task['title']}."

    return f"Checking in: {progress['done']}/{progress['total']} done. Keep it small now - finish or update '{next_task['title']}'."


def build_completion_summary():
    tasks = session.get("tasks", [])
    plan = session.get("current_plan", "")
    progress = progress_snapshot()
    completed_titles = [task.get("title", "") for task in tasks if task.get("completed")]

    if not tasks:
        return "No tasks were tracked yet. Build a plan first, then check things off as you finish them."

    if progress["remaining"] > 0:
        remaining_titles = [task.get("title", "") for task in tasks if not task.get("completed")]
        return (
            f"You have {progress['done']}/{progress['total']} done. "
            f"Still left: {', '.join(remaining_titles[:4])}."
        )

    prompt = f"""
The user completed every task in this plan.

Original plan:
{plan}

Completed tasks:
{json.dumps(completed_titles, indent=2)}

Write a short completion summary in DeadlineAI's warm direct friend tone.
Mention what got done and one sane next step. Keep it under 120 words.
"""
    try:
        return gemini_text(prompt, temperature=0.4, max_output_tokens=300).strip()
    except Exception:
        return f"Done. You checked off all {progress['total']} tasks. Take a minute, save/submission-check anything important, then actually stop for a bit."


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == DEMO_USER and check_password_hash(DEMO_PASSWORD_HASH, password):
            session["user"] = username
            return redirect(url_for("home"))
        error = "Wrong username or password. Check the demo credentials below."
    return render_template("login.html", error=error, demo_user=DEMO_USER)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session["user"])


@app.route("/calendar")
@login_required
def calendar_view():
    events = sorted(session.get("calendar_events", []), key=lambda item: (item.get("date", ""), item.get("start_time", "")))
    rows = "\n".join(
        f"""
        <article class="event">
            <time>{escape(event.get("date", ""))} {escape(event.get("start_time", ""))}-{escape(event.get("end_time", ""))}</time>
            <h2>{escape(event.get("title", "Task"))}</h2>
            <p>{escape(event.get("description", ""))}</p>
        </article>
        """
        for event in events
    )
    if not rows:
        rows = '<p class="empty">No calendar blocks yet. Build or revise a plan first.</p>'

    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>DeadlineAI Calendar</title>
            <style>
                body { margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f7f3ec; color: #241f1a; }
                main { width: min(920px, calc(100% - 32px)); margin: 32px auto; }
                header { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
                a { color: #7a3f2b; font-weight: 700; text-decoration: none; }
                .event { background: #fffaf2; border: 1px solid #e2d6c8; border-radius: 8px; padding: 16px; margin: 12px 0; }
                time { color: #7a3f2b; font-size: 13px; font-weight: 800; }
                h1 { margin: 0; font-size: 28px; }
                h2 { margin: 8px 0 6px; font-size: 18px; }
                p { margin: 0; line-height: 1.5; }
                .empty { background: #fffaf2; border: 1px solid #e2d6c8; border-radius: 8px; padding: 16px; }
            </style>
        </head>
        <body>
            <main>
                <header>
                    <h1>Calendar</h1>
                    <a href="{{ url_for('home') }}">Back to plan</a>
                </header>
                {{ rows|safe }}
            </main>
        </body>
        </html>
        """,
        rows=rows,
    )


@app.route("/api/session")
def current_session():
    return jsonify({"logged_in": bool(session.get("user")), "user": session.get("user")})


@app.route("/api/plan", methods=["POST"])
@login_required
def generate_plan():
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "Please describe your tasks and deadlines."}), 400
    if len(user_input) < 10:
        return jsonify({"error": "Tell me more - what tasks do you have and when are they due?"}), 400

    try:
        plan = gemini_text(user_input, temperature=0.5, max_output_tokens=1200)
        return jsonify(save_plan_state(user_input, plan))
    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {str(exc)}"}), 500


@app.route("/api/reschedule", methods=["POST"])
@login_required
def reschedule():
    data = request.get_json(silent=True) or {}
    original_plan = data.get("original_plan", "").strip() or session.get("current_plan", "")
    update = data.get("update", "").strip()

    if not update:
        return jsonify({"error": "Tell me what changed."}), 400

    combined_input = f"""
Original situation: {original_plan}

What changed: {update}

Reassess with this new information and give a revised plan.
Briefly acknowledge what changed, then give the updated plan with the same warm, direct friend energy.
"""

    try:
        plan = gemini_text(combined_input, temperature=0.5, max_output_tokens=1200)
        old_tasks = session.get("tasks", [])
        state = save_plan_state(update, plan, old_tasks=old_tasks)
        state["changed"] = update
        return jsonify(state)
    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {str(exc)}"}), 500


@app.route("/api/weekplan", methods=["POST"])
@login_required
def week_plan():
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "Tell me what your week looks like first."}), 400

    prompt = f"""
Build a realistic 7-day plan for this user.
Prioritize deadlines, protect sleep, and include calendar-friendly time blocks.
Keep the same DeadlineAI warm direct friend tone.

User situation:
{user_input}
"""
    try:
        plan = gemini_text(prompt, temperature=0.45, max_output_tokens=1400)
        return jsonify(save_plan_state(user_input, plan))
    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {str(exc)}"}), 500


@app.route("/api/tasks", methods=["GET"])
@login_required
def get_tasks():
    return jsonify({"tasks": session.get("tasks", []), "progress": progress_snapshot()})


@app.route("/api/tasks/<task_id>/complete", methods=["POST"])
@login_required
def set_task_complete(task_id):
    data = request.get_json(silent=True) or {}
    completed = bool(data.get("completed", True))
    tasks = session.get("tasks", [])

    for task in tasks:
        if task.get("id") == task_id:
            task["completed"] = completed
            task["completed_at"] = now_utc().isoformat() if completed else None
            session["tasks"] = tasks
            session.modified = True

            progress = progress_snapshot()
            summary = None
            if progress["remaining"] == 0:
                summary = build_completion_summary()
                session["completed_summary"] = summary
                session.modified = True

            return jsonify({"task": task, "progress": progress, "summary": summary})

    return jsonify({"error": "Task not found."}), 404


@app.route("/api/checkin", methods=["GET", "POST"])
@login_required
def checkin():
    data = request.get_json(silent=True) or {}
    interval_minutes = data.get("interval_minutes", request.args.get("interval_minutes", 25))
    try:
        interval_minutes = max(5, min(120, int(interval_minutes)))
    except (TypeError, ValueError):
        interval_minutes = 25

    now = now_utc()
    force = bool(data.get("force", request.args.get("force", False)))
    next_checkin_raw = session.get("next_checkin_at")
    due = True
    if next_checkin_raw and not force:
        try:
            due = now >= datetime.fromisoformat(next_checkin_raw)
        except ValueError:
            due = True

    message = build_checkin_message(force=force or due)
    if due or force:
        session["last_checkin_at"] = now.isoformat()
        session["next_checkin_at"] = (now + timedelta(minutes=interval_minutes)).isoformat()
        session.modified = True

    return jsonify(
        {
            "due": due or force,
            "message": message,
            "progress": progress_snapshot(),
            "next_checkin_at": session.get("next_checkin_at"),
        }
    )


@app.route("/api/summary", methods=["GET", "POST"])
@login_required
def summary():
    cached = session.get("completed_summary")
    progress = progress_snapshot()

    if cached and progress["remaining"] == 0:
        return jsonify({"summary": cached, "progress": progress})

    summary_text = build_completion_summary()
    if progress["remaining"] == 0:
        session["completed_summary"] = summary_text
        session.modified = True

    return jsonify({"summary": summary_text, "progress": progress})


@app.route("/api/calendar", methods=["GET", "POST"])
@login_required
def calendar_events():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        plan = data.get("plan", "").strip() or session.get("current_plan", "")
        if not plan:
            return jsonify({"events": [], "calendar_url": url_for("calendar_view")})
        events = extract_calendar_events(plan)
        session["calendar_events"] = events
        session.modified = True
    else:
        events = session.get("calendar_events", [])

    return jsonify({"events": events, "calendar_url": url_for("calendar_view")})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "DeadlineAI"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
