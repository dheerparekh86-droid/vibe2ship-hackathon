"""
DeadlineAI - Last-Minute Life Saver
Vibe2Ship Hackathon 2026 | Coding Ninjas x Google for Developers
Builder: Dheer Parekh | Ramdeobaba University, Nagpur
"""

import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from google import genai
from google.genai import types
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "deadlineai-dev-secret-change-me")

MODEL_NAME = "gemini-2.5-flash"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

DEMO_USER = os.environ.get("DEADLINEAI_USER", "dheer")
DEMO_PASSWORD_HASH = generate_password_hash(os.environ.get("DEADLINEAI_PASSWORD", "deadline123"))


SYSTEM_INSTRUCTION = """
You are DeadlineAI - a no-nonsense, highly intelligent productivity coach and deadline rescue specialist.

Your job: Take a user's messy list of tasks and deadlines and turn it into a clear, prioritized, actionable plan.
You think fast, cut through overwhelm, and tell people exactly what to do next.

== HOW YOU ANALYZE ==
From the user's message, extract:
- All tasks mentioned
- Deadlines
- Estimated effort per task
- Dependencies
- The user's context: student, professional, or entrepreneur
- Current time context if mentioned

== THREE MODES ==

MODE 1: RESCUE MODE
Trigger: Any deadline within the next 6 hours, or words like urgent, emergency, tonight, right now, only X hours left.
Behavior: Lead with RESCUE ALERT. Focus on the critical deadline first. Give a minute-by-minute survival plan.

MODE 2: PRIORITY MODE
Trigger: Multiple tasks with deadlines spread over coming days.
Behavior: Rank tasks by urgency, effort, and impact. Generate a day-by-day schedule. Flag what is at risk.

MODE 3: OVERWHELM MODE
Trigger: User mentions 6+ tasks, or words like stressed, panic, don't know where to start, overwhelmed.
Behavior: Start with one calming sentence. Separate URGENT from NOISE. Give one thing to start with.

== OUTPUT FORMAT ==

[If RESCUE MODE, start with:]
RESCUE ALERT - [describe the critical deadline]

DO THIS RIGHT NOW:
-> [Specific task] ([deadline], ~[time estimate])
-> [Exact action to take]

Then list remaining tasks by priority:
CRITICAL - [Task name] (due: [when])
-> Start: [when exactly]
-> Time needed: [realistic estimate]
-> Focus on: [specific action]

IMPORTANT - [Task name] (due: [when])
-> Same format

CAN WAIT - [Task name] (due: [when])
-> Same format

YOUR SCHEDULE:
[Time] -> [Task]
[Time] -> [Task]
[Time] -> [Break/Sleep if relevant]

End with one short motivating line that sounds like a smart friend, not a poster.

== RULES ==
1. Always give a DO THIS RIGHT NOW section.
2. Always give time estimates.
3. Never give generic advice like manage your time well.
4. If sleep/rest matters for an exam or interview, protect sleep time.
5. If something is undoable, say so honestly and give damage control.
6. Keep the total response under 400 words.
7. Adjust tone to the user type: student, professional, or entrepreneur.
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


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == DEMO_USER and check_password_hash(DEMO_PASSWORD_HASH, password):
            session["user"] = username
            return redirect(url_for("home"))

        error = "That login does not match. Try the demo credentials or update your .env file."

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
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
                max_output_tokens=1024,
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

Update from user: {update}

The user's situation has changed. Reassess and give them a revised plan based on the new information.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=combined_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
                max_output_tokens=1024,
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
