## 🤖 Google AI Studio & Gemini API

Nexora is built using the **Google Gemini API** through **Google AI Studio**, with **Gemini 2.5 Flash Lite (`gemini-2.5-flash-lite`)** serving as the core AI engine behind the application.

Rather than functioning as a simple chatbot, Gemini acts as an intelligent planning assistant. When a user describes their week—such as upcoming deadlines, classes, work hours, appointments, commute, gym sessions, sleep goals, or personal preferences—the model analyzes the entire workload before generating a plan.

The AI performs several planning steps, including:

* Calculating available hours after accounting for fixed commitments like work, college, sleep, meals, and travel.
* Extracting scheduling constraints and identifying potential conflicts or overloaded days.
* Prioritizing tasks based on deadlines, estimated effort, and dependencies.
* Creating a realistic day-by-day weekly schedule that respects the user's availability and energy patterns.
* Generating actionable task checklists, planning insights, and contingency suggestions if the user falls behind.
* Producing calendar-ready events that can be exported as a standard `.ics` file for Google Calendar, Apple Calendar, or Outlook.

To provide a smoother experience, Nexora also includes **automatic Gemini API key rotation**. If one API key reaches its rate limit, the application seamlessly switches to another configured key without interrupting the user's request.

Google AI Studio and the Gemini API enable Nexora to deliver personalized, context-aware planning in seconds, transforming unstructured user input into a practical, conflict-free weekly schedule.
