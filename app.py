"""
Vibe2Ship Starter — Flask + Gemini API
----------------------------------------
Generic scaffold. Once you see the problem statement:
  1. Edit SYSTEM_INSTRUCTION below to match your task.
  2. Edit the /api/process route to shape input/output for your use case.
  3. Edit index.html for your UI.
That's it — everything else (API wiring, error handling, deploy config) is done.
"""
import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads .env file and loads GEMINI_API_KEY into os.environ

app = Flask(__name__)
# --- Gemini client setup ---
# Set GEMINI_API_KEY as an environment variable (locally via .env, on Render via dashboard)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"  # swap to gemini-2.5-pro if you need deeper reasoning

# EDIT THIS once you know your problem statement — this is your app's "personality" / task framing
SYSTEM_INSTRUCTION = """You are a helpful assistant. Replace this with task-specific
instructions once you know the problem statement (e.g. "You are a resume reviewer
that gives concise, actionable feedback" or "You classify support tickets into
categories: Billing, Technical, General")."""


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process():
    """
    Generic endpoint: takes user input, sends to Gemini, returns response.
    Adapt the prompt construction below to your specific task.
    """
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                max_output_tokens=1024,
            ),
        )
        return jsonify({"result": response.text})

    except Exception as e:
        # Keep this verbose during the hackathon for fast debugging;
        # tighten before final demo if you want.
        return jsonify({"error": str(e)}), 500


@app.route("/api/structured", methods=["POST"])
def structured():
    """
    Example of getting STRUCTURED JSON back from Gemini instead of free text.
    Useful if your app needs to populate UI elements (lists, scores, categories, etc.)
    rather than just display a paragraph.
    """
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "").strip()

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    json_instruction = (
        SYSTEM_INSTRUCTION
        + "\n\nRespond ONLY with valid JSON, no markdown fences, no preamble. "
        "Example shape: {\"category\": \"...\", \"confidence\": 0.0, \"explanation\": \"...\"}"
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=json_instruction,
                temperature=0.3,  # lower temp = more consistent JSON formatting
                max_output_tokens=1024,
            ),
        )
        import json
        cleaned = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        return jsonify(parsed)

    except json.JSONDecodeError:
        return jsonify({"error": "Model did not return valid JSON", "raw": response.text}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Render uses this kind of endpoint to confirm the app is alive."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
