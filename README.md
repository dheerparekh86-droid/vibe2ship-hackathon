# DeadlineAI — Last-Minute Life Saver

> An AI-powered productivity companion that helps you plan, prioritize, and act before deadlines are missed.

**Vibe2Ship Hackathon 2026 | Coding Ninjas × Google for Developers**  
**Builder:** Dheer Parekh | First-Year Engineering | Ramdeobaba University, Nagpur

---

## The Problem

Students, professionals, and entrepreneurs constantly miss deadlines, forget assignments, and let important commitments slip. Existing tools send passive reminders — they notify you, but don't help you *act*. A ping saying "Assignment due in 1 hour" doesn't tell you what to do first or how to manage your time.

## The Solution

**DeadlineAI** is a conversational AI productivity companion powered by **Google Gemini 2.5 Flash**. You describe your tasks and deadlines in plain English — DeadlineAI thinks with you, not just at you.

Instead of:
> ❌ "Reminder: Assignment due tomorrow"

DeadlineAI gives you:
> ✅ "Here's your priority order, time estimates, what's at risk, and exactly what to do right now."

---

## Live Demo

🚀 **[Try it live →](https://vibe2ship-app.onrender.com)**

---

## Features

- **Intelligent Task Prioritization** — Gemini ranks your tasks by urgency, effort, and deadline proximity
- **AI-Powered Schedule Generation** — describes your situation in plain language, gets a realistic action plan back
- **Last-Minute Rescue Mode** — when time is critically short, focuses only on what matters most
- **Context-Aware Advice** — understands if you're a student, professional, or entrepreneur and adjusts tone
- **Plain Language Input** — no forms, no dropdowns, just talk to it naturally
- **Live & Deployed** — accessible from any device, no installation needed

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Model | Google Gemini 2.5 Flash |
| AI Platform | Google AI Studio |
| Backend | Python 3, Flask |
| Frontend | HTML, CSS, JavaScript (vanilla) |
| Deployment | Render |
| Version Control | GitHub |

---

## Project Structure

```
vibe2ship-hackathon/
├── app.py                  # Flask backend + Gemini API integration
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment configuration
├── .gitignore              # Excludes .env and cache files
├── .env.example            # Environment variable template
├── README.md               # This file
└── templates/
    └── index.html          # Frontend UI
```

---

## How It Works

1. User describes their tasks and deadlines in plain natural language
2. Flask backend receives the input and sends it to Gemini 2.5 Flash with a carefully crafted system instruction
3. Gemini analyzes urgency, effort required, time available, and dependencies
4. Returns a structured, prioritized action plan with time estimates and risk flags
5. Frontend displays the plan clearly — what to do first, what can wait, what's at risk

---

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/dheerparekh86-droid/vibe2ship-hackathon.git
cd vibe2ship-hackathon
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up your API key**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Gemini API key
# Get one free at: https://aistudio.google.com
GEMINI_API_KEY=your_key_here
```

**4. Run the app**
```bash
python app.py
```

**5. Open in browser**
```
http://localhost:5000
```

---

## Example Usage

**Input:**
```
I have a physics exam tomorrow at 10am, two programming 
assignments due Friday, a group project presentation on 
Monday, and I haven't started any of them. It's 8pm now. 
What do I do?
```

**DeadlineAI Output:**
```
Priority Plan for Tonight:

🔴 URGENT — Physics Exam (due in ~14 hours)
→ Focus here for the next 3 hours (8pm–11pm)
→ Do: past papers, formula sheet, key concepts only
→ Sleep by midnight — exam performance needs rest

🟡 NEXT — Programming Assignment 1 (due Friday)
→ Start tomorrow after exam, allocate 2–3 hours
→ Break into: setup → logic → testing

🟡 NEXT — Programming Assignment 2 (due Friday)  
→ Wednesday evening, ~2 hours

🟢 MANAGEABLE — Group Project (due Monday)
→ Coordinate with team Thursday, present Sunday

⚡ Do THIS right now: Close all tabs. Open your physics 
notes. Set a 90-minute timer. Go.
```

---

## Deployment

The app is deployed on **Render** with automatic deploys on every GitHub push.

Environment variables are configured directly in Render's dashboard — no `.env` file is used in production.

**Deploy your own:**
1. Fork this repo
2. Connect to [Render](https://render.com)
3. Add `GEMINI_API_KEY` in Render's Environment settings
4. Deploy — `render.yaml` handles the rest

---

## Why Gemini?

Gemini 2.5 Flash was chosen for its ability to understand nuanced, real-world context. A user saying *"I have an exam tomorrow, three assignments, and a job interview next week — what do I do first?"* requires genuine reasoning, not keyword matching. Gemini handles this naturally, making the experience feel like talking to a smart mentor rather than filling a form.

---

## Evaluation Criteria Addressed

| Criterion | How DeadlineAI addresses it |
|---|---|
| AI Usage | Core functionality powered by Gemini 2.5 Flash |
| Real Problem | Universal pain point — missed deadlines affect everyone |
| Working Demo | Live on Render, accessible from any device |
| Creativity | Conversational interface, not a traditional to-do app |
| Execution | Fully deployed, clean codebase, clear architecture |

---

## Contact

**Dheer Parekh**  
First-Year Engineering Student  
Ramdeobaba University, Nagpur  
GitHub: [@dheerparekh86-droid](https://github.com/dheerparekh86-droid)
