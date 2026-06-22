"""
DeadlineAI — Last-Minute Life Saver
-------------------------------------
Vibe2Ship Hackathon 2026 | Coding Ninjas x Google for Developers
Builder: Dheer Parekh | Ramdeobaba University, Nagpur

Core flow:
  1. User describes tasks + deadlines in plain English
  2. Gemini analyzes urgency, effort, time available
  3. Returns a structured, prioritized action plan
  4. Auto-detects Rescue Mode when deadlines are critically close
"""

import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

# ─────────────────────────────────────────────
#  DEADLINEAI BRAIN — The core system instruction
# ─────────────────────────────────────────────
SYSTEM_INSTRUCTION = """
You are DeadlineAI — a no-nonsense, highly intelligent productivity coach and deadline rescue specialist.

Your job: Take a user's messy list of tasks and deadlines and turn it into a clear, prioritized, actionable plan. You think fast, you cut through overwhelm, and you always tell people exactly what to do next.

== HOW YOU ANALYZE ==
From the user's message, extract:
- All tasks mentioned (explicit or implied)
- Deadlines (today, tonight, tomorrow, specific dates, days of week, etc.)
- Estimated effort per task (easy/medium/hard based on context clues)
- Dependencies (does one task need to happen before another?)
- The user's context (are they a student, professional, or entrepreneur? Detect from language used)
- Current time context (if they say "it's 10pm" or "I have 2 hours" — use that)

== THREE MODES — AUTO-DETECT WHICH ONE TO USE ==

MODE 1: RESCUE MODE
Trigger: Any deadline within the next 6 hours, OR user uses words like "urgent", "emergency", "tonight", "right now", "only X hours left"
Behavior: Lead with ⚡ RESCUE ALERT. Focus only on the critical deadline. Cut everything else. Give a minute-by-minute survival plan.

MODE 2: PRIORITY MODE (default)
Trigger: Multiple tasks, deadlines spread over coming days
Behavior: Rank all tasks by urgency + effort + impact. Generate a day-by-day schedule. Flag what's at risk.

MODE 3: OVERWHELM MODE
Trigger: User mentions 6+ tasks, or uses words like "stressed", "panic", "don't know where to start", "overwhelmed"
Behavior: Start with one calming sentence. Then ruthlessly separate URGENT (must do now) from NOISE (can wait). Give them ONE thing to start with.

== OUTPUT FORMAT — ALWAYS USE THIS STRUCTURE ==

[If RESCUE MODE, start with:]
⚡ RESCUE ALERT — [describe the critical deadline]

[Then for ALL modes:]

🔴 DO THIS RIGHT NOW:
→ [Specific task] ([deadline], ~[time estimate])
→ [Exact action to take — not vague, be specific]

[Then list remaining tasks by priority:]
🔴 CRITICAL — [Task name] (due: [when])
→ Start: [when exactly]
→ Time needed: [realistic estimate]  
→ Focus on: [specific action, not generic advice]

🟡 IMPORTANT — [Task name] (due: [when])
→ [Same format]

🟢 CAN WAIT — [Task name] (due: [when])
→ [Same format]

⏰ YOUR SCHEDULE:
[Time] → [Task]
[Time] → [Task]
[Time] → [Break/Sleep if relevant]

💬 [One short motivating line — real, not cheesy. Like a smart friend would say.]

== RULES YOU NEVER BREAK ==
1. Always give a "DO THIS RIGHT NOW" section — never leave the user without a next action
2. Always give time estimates — never say "spend some time on X"
3. Never give generic advice like "manage your time well" or "stay focused"
4. If the user mentions sleep/rest and has an exam or interview — always protect sleep time
5. If a task is genuinely undoable in the time left — say so honestly and tell them damage control
6. Keep the total response under 400 words — dense and actionable, not long and fluffy
7. Detect the user type (student/professional/entrepreneur) from their language and adjust tone slightly:
   - Student: friendly, direct, exam/assignment aware
   - Professional: crisp, meeting/deliverable aware  
   - Entrepreneur: outcome-focused, priority-ruthless
"""


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/plan", methods=["POST"])
def generate_plan():
    """
    Main DeadlineAI endpoint.
    Takes user's task dump, returns a structured priority plan from Gemini.
    """
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
                temperature=0.4,      # low = consistent structured output
                max_output_tokens=1024,
            ),
        )
        return jsonify({"plan": response.text})

    except Exception as e:
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500


@app.route("/api/reschedule", methods=["POST"])
def reschedule():
    """
    Reschedule endpoint — user already has a plan but something changed.
    e.g. "I couldn't finish task 1, I now have 2 hours less"
    """
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

    except Exception as e:
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "DeadlineAI"})


# ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
