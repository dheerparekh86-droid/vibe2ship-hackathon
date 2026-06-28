 Nexora — AI Productivity Planner

 Vibe2Ship Hackathon 2026 | Coding Ninjas × Google for Developers

> Turn an overwhelming week into a realistic plan you can actually follow—in under 30 seconds.

Nexora is an AIpowered productivity planner built for students and professionals who constantly juggle deadlines, classes, meetings, workouts, and everything in between. Instead of giving you another endless todo list, Nexora creates a practical weekly schedule that fits your time, priorities, and personal constraints.

It doesn't just organize your tasks—it helps you figure out whether your week is realistic in the first place.



 🎯 Why Nexora?

We've all been there.

It's Sunday night. You have multiple assignments due, appointments throughout the week, a gym routine you're trying to stick to, and absolutely no idea where to begin.

Most productivity apps let you dump everything into a list.

Nexora goes a step further. It analyzes your available time, understands your commitments, prioritizes what matters most, and builds a schedule that's actually achievable.



 ✨ Features

 🧠 Smart Workload Analysis

Before creating your schedule, Nexora calculates how much free time you really have after accounting for work or college, commute, sleep, meals, and other commitments. If your week is overloaded, it'll tell you honestly instead of pretending everything fits.

 📅 Weekly Planning

Generate a complete daybyday plan that respects your deadlines, appointments, preferred work hours, gym sessions, and other personal constraints.

 ⚡ Intelligent Prioritization

Tasks are ordered based on deadlines, estimated effort, and dependencies. Every recommendation comes with a short explanation so you understand why the schedule looks the way it does.

 🔄 Conflict Detection

Nexora automatically detects scheduling conflicts, overloaded days, or overlapping events and adjusts your plan whenever possible.

 ✅ Task Tracking

Each generated plan includes an interactive checklist so you can track progress throughout the week and monitor your completion rate.

 📆 Calendar Export

Export your schedule as a standard `.ics` file and import it directly into Google Calendar, Apple Calendar, or Outlook.

 🔁 Backup Plans

Life rarely goes exactly as planned. Every schedule includes practical fallback suggestions so you know what to move and when if something slips.

 👤 Authentication

Create an account to save your plans or jump straight in with Guest Mode for a quick trial.



 🛠 Tech Stack

| Layer          | Technology                                                |
|  |  |
| Backend        | Python, Flask                                             |
| AI             | Google Gemini 2.5 Flash Lite                              |
| Database       | SQLAlchemy, SQLite (Development), PostgreSQL (Production) |
| Frontend       | HTML, CSS, JavaScript                                     |
| Authentication | Flask Sessions, Werkzeug Password Hashing                 |
| Deployment     | Render                                                    |
| Calendar       | ICS Export                                                |



 🚀 Getting Started

 Prerequisites

 Python 3.10+
 Gemini API Key

 Installation

```bash
git clone https://github.com/yourusername/nexora.git

cd nexora

python m venv venv

source venv/bin/activate
 Windows
venv\Scripts\activate

pip install r requirements.txt
```

 Environment Variables

Create a `.env` file in the project root.

```env
GEMINI_API_KEY=your_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///nexora.db
```

Optional API key rotation:

```env
GEMINI_API_KEY_1=...
GEMINI_API_KEY_2=...
GEMINI_API_KEY_3=...
```

 Run the Application

```bash
python app.py
```

Open http://localhost:5000 in your browser.



 📁 Project Structure

```text
nexora/
├── app.py
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── sidebar.html
│   ├── index.html
│   ├── tasks.html
│   ├── assistant.html
│   ├── calendar_page.html
│   └── analytics_page.html
├── static/
├── requirements.txt
└── README.md
```



 🧠 How the AI Works

Rather than simply sorting tasks by deadline, Nexora follows a structured planning process.

1. Calculates available time for the week.
2. Extracts important constraints like work hours, appointments, and sleep.
3. Prioritizes tasks based on urgency and effort.
4. Schedules demanding work during highenergy periods.
5. Detects and resolves conflicts.
6. Generates a complete weekly timetable.
7. Highlights workload risks and planning insights.
8. Creates contingency plans if your schedule changes.

To improve reliability, Nexora also supports automatic API key rotation, allowing requests to continue even if one key reaches its rate limit.



 🏆 Challenges We Solved

Scaling from a single page to a multipage application

We refactored the project into a modular Flask application using Jinja templates and shared components to improve maintainability.

Handling AI response limits

Calendar generation occasionally exceeded the model's output limit. Increasing the extraction stage to 2500 tokens ensured complete weekly schedules.

Session storage limitations

Flask's session cookie size caused calendar data to disappear between pages. We solved this by introducing localStorage as a clientside persistence layer.

Deployment persistence

Render's freetier cold starts could clear session data. Migrating user history to PostgreSQL through SQLAlchemy made the application much more reliable.

Route conflicts

A duplicate Flask route introduced unexpected session issues during development. Static analysis helped catch the problem before deployment.



 🔮 Future Improvements

 Persistent databasebacked task management
 Mobileresponsive interface
 Habit tracking
 Recurring tasks
 Push notifications
 Google Calendar sync
 Shared planning and collaboration



 👨‍💻 Developer

Dheer Parekh

Ramdeobaba University, Nagpur

Built for Vibe2Ship Hackathon 2026 by Coding Ninjas × Google for Developers.



 📄 License

Released under the MIT License.



> Built during a deadline panic. Designed so you don't have one.
