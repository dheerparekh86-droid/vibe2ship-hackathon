"""
Nexora - Last-Minute Life Saver
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
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
    Response,
)
from google import genai
from google.genai import types
from werkzeug.security import check_password_hash, generate_password_hash
import time  
load_dotenv()

print("KEY BEING USED:", os.environ.get("GEMINI_API_KEY", "NOT FOUND")[:12])


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Nexora-dev-secret-change-me")
from flask_sqlalchemy import SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///Nexora.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_guest = db.Column(db.Boolean, default=False)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    input_text = db.Column(db.Text)
    plan_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"))
    title = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
MODEL_NAME = "gemini-2.5-flash-lite"
# Collect all available keys — supports both single key and rotation
GEMINI_KEYS = [
    os.environ.get("GEMINI_API_KEY_1"),
    os.environ.get("GEMINI_API_KEY_2"),
     os.environ.get("GEMINI_API_KEY_3"),
     os.environ.get("GEMINI_API_KEY_4"),
    os.environ.get("GEMINI_API_KEY"),  # fallback to old single key
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]  # remove None/empty

if not GEMINI_KEYS:
    raise RuntimeError("No Gemini API keys found. Set GEMINI_API_KEY_1 in your .env file.")

print(f"Nexora: {len(GEMINI_KEYS)} API key(s) loaded.")
_key_index = 0

def get_client():
    global _key_index
    return genai.Client(api_key=GEMINI_KEYS[_key_index % len(GEMINI_KEYS)])

def rotate_key():
    global _key_index
    _key_index += 1
    print(f"Rotated to key index {_key_index % len(GEMINI_KEYS)}")



SYSTEM_INSTRUCTION = """
You are Nexora - an elite AI productivity planner. You are NOT a simple task lister.
You think like a brilliant chief of staff who genuinely cares about the user's wellbeing, time, and sanity.

== STEP 1: WORKLOAD ANALYSIS (always do this first, internally) ==
Before planning, calculate:
- Total estimated hours for all tasks
- Total available hours (subtract sleep, meals, commute, fixed events, college/work hours)
- Overbooked by how many hours?
- Which tasks must be postponed?

Always open with this block:

🧠 AI Workload Analysis
Total work estimated: X hours
Available time: Y hours
[If overbooked]: ⚠ You are overbooked by Z hours. I recommend postponing: [list].
[If manageable]: ✅ This week is tight but doable. Here's how.

== STEP 2: CONSTRAINTS — NEVER IGNORE THESE ==
Extract and strictly respect ALL of the following if mentioned:
- College/work hours (e.g. 9AM–4PM means NO tasks scheduled during that time)
- Commute time (add travel BEFORE and AFTER college/work — both ways)
- Sleep requirement (protect it — never schedule past sleep cutoff)
- Fixed appointments (dentist, interviews, meetings, birthdays, family events)
- Gym days and times
- Meal times
- Energy patterns (if user says they procrastinate, schedule hard tasks in the morning)
- No-work windows (e.g. "no work after midnight")

If commute is 45 minutes each way, the schedule must show:
[Leave time] → Commute → [Arrive time] → College starts

== STEP 3: PRIORITY ORDERING ==
Rank tasks by:
1. Deadline proximity (earlier deadline = higher priority)
2. Effort required (high effort + close deadline = top priority)
3. Fixed time constraints (exam at 9AM Thursday beats everything Wednesday night)
4. Dependency (must finish DS assignment before you can revise it)

Always explain WHY you ordered tasks this way. Example:
"I scheduled Data Structures before Mathematics because DS is due Wednesday night, two days earlier."

== STEP 4: ENERGY-AWARE SCHEDULING ==
Morning (6AM–12PM): Hardest cognitive work (assignments, coding, exam prep)
Afternoon (12PM–5PM): Meetings, lighter tasks, commute
Evening (5PM–9PM): Practice, revision, calls, errands
Late evening (9PM–11PM): Review only — no new hard tasks
Never schedule demanding work in the last 2 hours before sleep

If user mentions procrastination: put the hardest task FIRST every day.

== STEP 5: CONFLICT DETECTION ==
Actively look for conflicts and call them out:
- Two deadlines on the same day
- Dentist appointment during college hours
- Interview during a class
- Too much work on one day
Say: "⚠ Thursday has 11 hours of planned work. I've moved [task] to Wednesday evening."

== STEP 6: WEEKLY CALENDAR OUTPUT ==
ALWAYS produce a complete day-by-day schedule for every day mentioned.
Format each day like this:

📅 [DAY], [Date if known]
[Time] → [Activity]
[Time] → [Activity]
...
[Sleep time] → Sleep ← always include this

Example:
📅 Monday
6:30 → Wake up
7:00 → Breakfast
7:30 → Leave home (45 min commute)
8:15 → Arrive at college
9:00–4:00 → College
4:00 → Leave college (45 min commute)
4:45 → Home + short break
5:00–7:00 → Data Structures Assignment (Session 1)
7:00–7:30 → Dinner
7:30–9:00 → Electronics Quiz Revision
9:00–9:15 → Break
9:15–10:00 → Reply emails
10:30 → Wind down
11:00 → Sleep

== STEP 7: AI INSIGHTS SECTION ==
End every plan with this section:

🧠 Nexora Insights
⚠ [Any day with >9 hours of work]: "[Day] is overloaded. Consider moving [task] to [other day]."
💡 [Energy tip]: "Your hardest tasks are front-loaded — good. Don't rearrange them."
😴 Sleep: [X hours/night preserved or warning if not]
🔥 Burnout Risk: Low / Moderate / High (based on workload density)
📊 Confidence this plan is achievable: X%
➡ If you fall behind: Skip [lowest priority task] first.
== STEP 8: CONTINGENCY RULES ==
At the end of every plan, always add this section:

🔄 If Things Slip
- If [Task A] takes longer than expected → postpone [Task B] to [specific time/day]
- If you miss the morning session → compress it to [X] minutes in the evening
- If [fixed event] runs late → skip [lowest priority task] entirely
- Recovery anchor: No matter what happens, protect [most critical deadline] above all else

Generate 3-5 specific contingency rules based on the actual tasks in the plan.
These must be specific, not generic. Name actual tasks, actual times.

== HARD RULES ==
1. NEVER schedule tasks during college/work hours
2. ALWAYS include commute time both ways if mentioned
3. NEVER ignore fixed appointments (dentist, birthdays, family, interviews)
4. ALWAYS detect and flag impossible deadlines
5. ALWAYS produce a full weekly calendar — not just Monday
6. ALWAYS explain priority ordering
7. Protect sleep — never let it drop below what user specified
8. If something truly cannot fit, say so explicitly and suggest postponing it
9. Keep tone warm, direct, like a brilliant friend — not a robot
10. Maximum 800 words for the full response — dense and useful, not padded
11. Match context: student → "assignment/prof/submit", professional → "deliverable/EOD/stakeholder"
12. Always write the workload score exactly like: "Workload Score: X/10"
13. Always write burnout risk exactly like: "Burnout Risk: Low/Moderate/High"  
14. Always write total hours exactly like: "Total work estimated: X hours"
15. Always write free hours exactly like: "Free hours remaining: X hours"
"""


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
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
    global _key_index
    for attempt in range(len(GEMINI_KEYS) * 2):
        try:
            client = get_client()
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
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                print(f"Key {_key_index % len(GEMINI_KEYS)} exhausted, rotating...")
                rotate_key()
                time.sleep(1)  # ← was 2, now 1
                continue
            elif "503" in err or "UNAVAILABLE" in err:
                print(f"503 on attempt {attempt}, retrying...")
                time.sleep(1)  # ← was 3, now 1
                continue
            raise
    return "I'm having trouble reaching the AI right now. Please try again in a minute."
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
Extract ONLY real actionable tasks from this plan — things the user must actually DO and check off.

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

STRICT RULES:
- NEVER include schedule/time entries like "8:15 AM → Arrive at college" or "7:00 → Wake up" or "Commute" or "Breakfast" or "Sleep" or "Break" — these are NOT tasks.
- NEVER include sentences or motivational text as tasks.
- NEVER include lines starting with time formats (e.g. 7:00, 8:15 AM, 9:00–4:00).
- ONLY include real work items: assignments, submissions, study sessions, calls, purchases, admin tasks.
- Good examples: "Pay electricity bill", "Data Structures Assignment Session 1", "Reply to important emails", "Buy birthday gift for cousin", "Interview prep", "Electronics Quiz revision"
- Bad examples: "Arrive at college", "Commute", "Dinner", "Wake up", "being and productivity", "Let's break down those larger tasks"
- Keep titles short (under 60 chars), specific, and action-oriented.
- Set priority: high = deadline within 48 hours or exam/interview, normal = this week, low = can wait
- Maximum 12 tasks, pick the most important ones.

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
Extract calendar events from this Nexora plan.

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
- Maximum 50 events.

Plan:
{plan}
"""
    raw = gemini_text(prompt, temperature=0.15, max_output_tokens=2500,
        system_instruction="Return only valid JSON. No markdown. No commentary.")
    data = parse_json_object(raw) or {"events": []}
    events = data.get("events") if isinstance(data, dict) else []
    normalized = []
    for event in events[:50]:
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
    # REMOVED time.sleep(2)
    if old_tasks:
        tasks = preserve_completed_tasks(tasks, old_tasks)
    events = extract_calendar_events(plan)
    started = now_utc()
    # ... rest unchanged

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
        "ics_url": url_for("export_ics") 
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

Write a short completion summary in Nexora's warm direct friend tone.
Mention what got done and one sane next step. Keep it under 120 words.
"""
    try:
        return gemini_text(prompt, temperature=0.4, max_output_tokens=300).strip()
    except Exception:
        return f"Done. You checked off all {progress['total']} tasks. Take a minute, save/submission-check anything important, then actually stop for a bit."


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and not user.is_guest and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("home"))
        error = "Wrong email or password."
    return render_template("login.html", error=error)
@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("home"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or not password:
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."
        elif User.query.filter_by(username=username).first():
            error = "That username is taken."
        else:
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("home"))
    return render_template("register.html", error=error)
@app.route("/guest-login")
def guest_login():
    guest_name = f"guest_{uuid.uuid4().hex[:6]}"
    user = User(
        username=guest_name,
        email=f"{guest_name}@guest.Nexora",
        password_hash=generate_password_hash(uuid.uuid4().hex),
        is_guest=True
    )
    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        user = db.session.get(User, user_id)
        if user and user.is_guest:
            # Clean up guest data
            Plan.query.filter_by(user_id=user_id).delete()
            Task.query.filter_by(user_id=user_id).delete()
            db.session.delete(user)
            db.session.commit()
    session.clear()
    return redirect(url_for("login"))




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
            <title>Nexora Calendar</title>
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

    return jsonify({"logged_in": bool(session.get("user_id")), "user": session.get("username")})



# CORRECT:
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

        if not plan or "trouble reaching" in plan:
            return jsonify({"error": "AI is busy. Try again in 10 seconds."}), 503

        new_plan = Plan(user_id=session["user_id"], input_text=user_input, plan_text=plan)
        db.session.add(new_plan)
        db.session.commit()

        tasks = fallback_tasks_from_plan(plan)
        events = []

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

        return jsonify({
            "plan": plan,
            "tasks": tasks,
            "calendar_events": events,
            "progress": progress_snapshot(),
            "next_checkin_at": session["next_checkin_at"],
            "calendar_url": url_for("calendar_view"),
            "ics_url": url_for("export_ics"),
        })
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
        if not plan or "trouble reaching" in plan:
            return jsonify({"error": "AI is busy. Try again in 10 seconds."}), 503

        old_tasks = session.get("tasks", [])
        tasks = fallback_tasks_from_plan(plan)
        tasks = preserve_completed_tasks(tasks, old_tasks)
        events = []

        started = now_utc()
        session["current_plan"] = plan
        session["current_input"] = update
        session["tasks"] = tasks
        session["calendar_events"] = events
        session["plan_started_at"] = started.isoformat()
        session["last_checkin_at"] = None
        session["next_checkin_at"] = (started + timedelta(minutes=25)).isoformat()
        session["completed_summary"] = None
        session.modified = True

        return jsonify({
            "plan": plan,
            "tasks": tasks,
            "calendar_events": events,
            "progress": progress_snapshot(),
            "next_checkin_at": session["next_checkin_at"],
            "calendar_url": url_for("calendar_view"),
            "ics_url": url_for("export_ics"),
            "changed": update,
        })
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
Keep the same Nexora warm direct friend tone.

User situation:
{user_input}
"""
    try:
        plan = gemini_text(prompt, temperature=0.45, max_output_tokens=1400)
        if not plan or "trouble reaching" in plan:
            return jsonify({"error": "Model is busy right now. Try again in 10 seconds."}), 503
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
# ↑ existing calendar_events() ends here

@app.route("/api/calendar/ics")
@login_required
def export_ics():
    events = session.get("calendar_events", [])
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Nexora//EN",
        "CALSCALE:GREGORIAN",
    ]
    for i, ev in enumerate(events):
        uid = f"Nexora-{i}-{uuid.uuid4()}"
        dt_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        date = ev.get("date", "").replace("-", "")
        start = ev.get("start_time", "00:00").replace(":", "")
        end = ev.get("end_time", "00:00").replace(":", "")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dt_stamp}",
            f"DTSTART:{date}T{start}00",
            f"DTEND:{date}T{end}00",
            f"SUMMARY:{ev.get('title', 'Task')}",
            f"DESCRIPTION:{ev.get('description', '')}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return Response(
        "\r\n".join(lines),
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment; filename=Nexora.ics"},
    )

# ↓ existing /health route stays here

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "Nexora"})
@app.route("/api/analytics")
@login_required
def analytics():
    uid = session["user_id"]
    total_plans = Plan.query.filter_by(user_id=uid).count()
    total_tasks = Task.query.filter_by(user_id=uid).count()
    completed_tasks = Task.query.filter_by(user_id=uid, completed=True).count()
    recent_plans = Plan.query.filter_by(user_id=uid).order_by(Plan.created_at.desc()).limit(5).all()
    
    return jsonify({
        "total_plans": total_plans,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": round((completed_tasks/total_tasks*100) if total_tasks else 0),
        "recent_plans": [
            {"input": p.input_text[:60], "created_at": p.created_at.isoformat()}
            for p in recent_plans
        ]
    })
# CHANGE THESE 5 ROUTES:

@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session.get("username", ""), page="dashboard")

@app.route("/tasks")
@login_required
def tasks_page():
    return render_template("tasks.html", username=session.get("username", ""), page="tasks")

@app.route("/assistant")
@login_required
def assistant_page():
    return render_template("assistant.html", username=session.get("username", ""), page="assistant")

@app.route("/calendar-view")
@login_required
def calendar_page():
    return render_template("calendar_page.html", username=session.get("username", ""), page="calendar")

@app.route("/analytics")
@login_required
def analytics_page():
    return render_template("analytics_page.html", username=session.get("username", ""), page="analytics")
@app.route("/debug-users")
def debug_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username, "email": u.email} for u in users])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

