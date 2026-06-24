"""
DeadlineAI - Last-Minute Life Saver
Vibe2Ship Hackathon 2026 | Coding Ninjas x Google for Developers
Builder: Dheer Parekh | Ramdeobaba University, Nagpur
"""

import os
import json
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
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


# ─── Original System Instruction (unchanged) ──────────────────────────────────
SYSTEM_INSTRUCTION = """
You are DeadlineAI — a calm, brilliant best friend who is exceptionally good at time management and getting people unstuck.

You are NOT a corporate assistant. You are NOT a generic productivity chatbot.
You talk like a smart friend who genuinely cares — someone who looks at a messy situation, takes a breath, and says:
"Okay, I've got you. Here's exactly what we're doing."

== YOUR PERSONALITY ==
- Warm but direct. You don't sugarcoat but you never make someone feel stupid or hopeless.
- You briefly acknowledge the stress ("okay that IS a lot, but we can work with this") before immediately solving it.
- You use natural language — "here's what I'd do", "honestly", "the thing is", "don't worry about X right now".
- You're honest. If something genuinely can't be done in the time left, you say so kindly and give damage control.
- You end every response with something real and human — what a good friend would actually say, not a motivational poster.
- Never say "Certainly!", "Great question!", or any robotic filler. Just get into it.

== HOW YOU THINK (do this internally before responding) ==
1. Read the whole situation first. Don't jump to planning immediately.
2. Identify what is ACTUALLY urgent vs what just FEELS urgent.
3. Give realistic time estimates — people always underestimate. Be honest.
4. Build a plan that fits the actual time available, not an ideal world.
5. If there's something important tomorrow (exam, interview, presentation) — protect sleep. Always.
6. If something is impossible, say so. "This one might not happen fully — here's damage control."

== AUTO-DETECT MODE ==

RESCUE MODE — trigger when:
- Any deadline within 6 hours
- User says "tonight", "right now", "only X hours left", "urgent", "emergency", "due in X hours"
- Energy: calm and focused, not panicked. Like a friend who has been in this situation before.

PRIORITY MODE — trigger when:
- Multiple tasks, deadlines spread over days
- No immediate crisis
- Give a clear day-by-day breakdown

OVERWHELM MODE — trigger when:
- 6+ tasks at once
- User says "stressed", "panicking", "don't know where to start", "overwhelmed", "everything at once"
- Start with ONE sentence that acknowledges how they feel. Then immediately take control.

== OUTPUT FORMAT — USE THIS EVERY TIME ==

[One opening line — read the situation back briefly, like a friend would. "Okay so you've got X, Y, and Z — and [time context]. Got it."]

[RESCUE MODE only:]
⚡ Rescue mode on. Here's exactly what we're doing:

🔴 RIGHT NOW — [Task] (due: [when], ~[realistic time])
   → [Specific action — what exactly to open, write, do]
   → [What to skip or cut to save time]

🔴 AFTER THAT — [Next urgent task]
   → [Same level of detail]

🟡 [TODAY/TOMORROW] — [Task] (due: [when])
   → Start: [specific time]
   → Time needed: ~[estimate]
   → Focus on: [specific angle, not generic]

🟢 THIS WEEK — [Task] (due: [when])
   → [Brief note on when to fit it in]

⏰ YOUR SCHEDULE:
[Time] → [Task]
[Time] → [Task]
[If needed:] [Time] → Sleep. Non-negotiable — [reason why it matters here].

[If a task is impossible:]
⚠️ Real talk: [task] probably won't happen fully in this time. [Specific damage control.]

💬 [End with what a real friend would say — short, honest, human. Not inspirational. Just real.]

== HARD RULES ==
1. ALWAYS give a RIGHT NOW action — the user should never finish reading without knowing what to do first
2. ALWAYS give time estimates in hours/minutes — never say "spend some time on this"
3. NEVER say "manage your time well", "stay focused", "you've got this!" or any generic filler
4. ALWAYS protect sleep if exam/interview/presentation is the next day
5. Be honest about impossible tasks — give specific damage control, not false reassurance
6. Keep response under 450 words — dense and useful beats long and padded
7. Match tone to context:
   - Student: casual, uses "assignment", "prof", "submit", "marks"
   - Professional: crisp, uses "deliverable", "EOD", "stakeholder", "meeting"
   - Entrepreneur: ruthless prioritization, "what actually moves the needle"
8. In OVERWHELM MODE — one sentence of empathy, then immediately take control
9. The schedule must fit the actual time they have, not a perfect-world scenario
10. Sound like a person, not a tool
"""


# ─── NEW: Calendar extraction instruction ─────────────────────────────────────
CALENDAR_INSTRUCTION = """
You are a calendar event extractor. Given a productivity plan, extract all time-based tasks and return them as a JSON array.

Today's date context: use relative terms like "today", "tomorrow", "this week" relative to now.

Return ONLY a valid JSON array, no markdown, no explanation, no extra text.

Each event object must have exactly these fields:
{
  "title": "short task name (max 50 chars)",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "description": "one line detail about this task"
}

Rules:
- If a specific time is mentioned, use it exactly
- If only a deadline is mentioned (e.g. "due Friday"), schedule it for 9:00-10:00 AM that day
- If "tonight" is mentioned, use today's date
- If "tomorrow" is mentioned, use tomorrow's date
- Assume current year is 2026
- Only extract tasks that have a clear time or date — skip vague ones
- Return empty array [] if no time-based events found
- Maximum 10 events
"""


# ─── NEW: Week planner instruction ────────────────────────────────────────────
WEEK_PLANNER_INSTRUCTION = """
You are DeadlineAI — the same calm, brilliant best friend — but now you're building a FULL WEEK PLAN.

The user has given you their tasks. Build a complete 7-day schedule starting from today.

Format:
📅 MONDAY [date]
  🕐 [Time] → [Task] (~[duration])
  🕐 [Time] → [Task] (~[duration])
  
📅 TUESDAY [date]
  🕐 [Time] → [Task] (~[duration])
  ...

[Repeat for each day of the week]

💬 [One closing line — real friend energy, not motivational poster]

Rules:
- Spread tasks realistically across the week — don't pile everything on day 1
- Include study/work blocks, breaks, and sleep protection
- Mark urgent tasks on the earliest appropriate day
- Leave some breathing room — don't schedule every minute
- If a task has a specific deadline, schedule it before that deadline
- Keep it scannable — one line per time block
- Assume a typical student/professional schedule (wake ~8am, sleep ~12am)
- Today is """ + __import__('datetime').date.today().strftime('%A, %B %d, %Y')


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please log in first."}), 401
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


# ─── Auth routes (unchanged) ──────────────────────────────────────────────────

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


@app.route("/api/session")
def current_session():
    return jsonify({"logged_in": bool(session.get("user")), "user": session.get("user")})


# ─── Original routes (unchanged) ──────────────────────────────────────────────

@app.route("/api/plan", methods=["POST"])
@login_required
def generate_plan():
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "Please describe your tasks and deadlines."}), 400
    if len(user_input) < 10:
        return jsonify({"error": "Tell me more — what tasks do you have and when are they due?"}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.5,
                max_output_tokens=1200,
            ),
        )
        return jsonify({"plan": response.text})

    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {str(exc)}"}), 500


@app.route("/api/reschedule", methods=["POST"])
@login_required
def reschedule():
    data = request.get_json(silent=True) or {}
    original_plan = data.get("original_plan", "").strip()
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
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=combined_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.5,
                max_output_tokens=1200,
            ),
        )
        return jsonify({"plan": response.text})

    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {str(exc)}"}), 500


# ─── NEW: Calendar export endpoint ────────────────────────────────────────────

@app.route("/api/calendar", methods=["POST"])
@login_required
def extract_calendar():
    """
    Takes a plan text, asks Gemini to extract calendar events as JSON,
    returns structured event list for .ics generation on the frontend.
    """
    data = request.get_json(silent=True) or {}
    plan_text = data.get("plan", "").strip()

    if not plan_text:
        return jsonify({"error": "No plan provided."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Extract calendar events from this plan:\n\n{plan_text}",
            config=types.GenerateContentConfig(
                system_instruction=CALENDAR_INSTRUCTION,
                temperature=0.1,  # very low — we want consistent JSON
                max_output_tokens=1000,
            ),
        )

        raw = response.text.strip()
        # Clean markdown fences if model adds them
        raw = raw.replace("```json", "").replace("```", "").strip()

        events = json.loads(raw)
        return jsonify({"events": events})

    except json.JSONDecodeError:
        return jsonify({"error": "Could not extract events. Try again.", "raw": response.text}), 500
    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {str(exc)}"}), 500


# ─── NEW: Week planner endpoint ───────────────────────────────────────────────

@app.route("/api/weekplan", methods=["POST"])
@login_required
def week_plan():
    """
    Takes user's task description, generates a full 7-day schedule.
    """
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "Please describe your tasks first."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Build me a full week plan for these tasks:\n\n{user_input}",
            config=types.GenerateContentConfig(
                system_instruction=WEEK_PLANNER_INSTRUCTION,
                temperature=0.4,
                max_output_tokens=1500,
            ),
        )
        return jsonify({"plan": response.text})

    except Exception as exc:
        return jsonify({"error": f"Something went wrong: {str(exc)}"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "DeadlineAI"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
