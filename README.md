# Student AI Utility App

An AI-powered student utility app with four prompt-based features, built on
the **Groq API** (Llama 3.3 70B): note summarization, quiz generation,
answer improvement, and concept explanation.

Groq was chosen over other providers for its very low inference latency —
responses generate noticeably faster, which matters for a student-facing
tool used interactively.

## Features

- **Summarize Notes** — turns notes into 5-8 exam-ready bullet points.
- **Generate Quiz** — creates 5 quiz questions (mixed short-answer/MCQ) plus
  an answer key from notes or a topic.
- **Improve My Answer** — rewrites a student's answer into a stronger,
  clearer version and explains what was improved.
- **Explain a Concept** — gives a plain-language definition, an example or
  analogy, and key points to remember for any topic.

A dropdown lets the user pick the feature; the input label/placeholder
updates to match it.

## How it works

1. The user selects a feature from the dropdown.
2. The user pastes notes, a question/answer, or a concept into the text area.
3. Input is validated (not empty, not too short, not too long).
4. A feature-specific prompt template wraps the input with clear
   instructions (format, tone, constraints) tailored to that use case.
5. The prompt is sent to Groq's `llama-3.3-70b-versatile` model via the
   Chat Completions API (Groq's API is OpenAI-compatible, so the same
   `chat.completions.create()` interface is used).
6. The result is displayed with Markdown formatting.
7. API failures are caught and shown as a friendly error, with technical
   details available in a collapsible section.

## Prompt design

Each feature has its own dedicated prompt (see `build_prompt()` in
`app.py`), so the model's behavior changes meaningfully per feature instead
of using one generic prompt for everything. Each prompt specifies: the
model's role, the expected output format, and constraints (e.g. don't
invent facts, keep the student's original meaning when improving answers).

## Validation & error handling

- Empty input → warning, no API call made.
- Input under 10 characters → warning asking for more content.
- Input over 8000 characters → warning asking to shorten it.
- Any API exception → caught and shown as a user-friendly error message.

## Setup & run

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your Groq API key (get one free at console.groq.com)
streamlit run app.py
```

## Why this isn't "just a chatbot"

The app is structured around four specific, purpose-built student
workflows rather than free-form chat: a fixed feature selector, tailored
prompt templates per feature, structured output formatting, and consistent
validation/error handling around every call.
