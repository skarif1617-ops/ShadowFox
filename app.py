import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(page_title="Student AI Utility App", page_icon="📚")

# ---- API Client Setup ----
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ GROQ_API_KEY not found. Please add it to your .env file.")
    st.stop()

# Configure OpenAI client pointing to Groq with extended connection timeout
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
    timeout=45.0,     # Prevent short premature socket timeouts
    max_retries=2,    # Retry on transport drops
)

MIN_CHARS = 10
MAX_CHARS = 8000

# ---- UI Layout ----
st.title("📚 Student AI Utility App")
st.write(
    "Paste your notes, a question, or an answer below, choose a feature, "
    "and get an AI-generated result to help with your studies."
)

feature = st.selectbox(
    "Choose a feature:",
    [
        "Summarize Notes",
        "Generate Quiz",
        "Improve My Answer",
        "Explain a Concept",
    ],
)

FEATURE_CONFIG = {
    "Summarize Notes": {
        "label": "Paste your notes here:",
        "placeholder": "Paste your lecture notes or study material here...",
        "max_tokens": 600,
    },
    "Generate Quiz": {
        "label": "Paste the notes/topic to generate quiz questions from:",
        "placeholder": "Paste the content you want to be quizzed on...",
        "max_tokens": 900,
    },
    "Improve My Answer": {
        "label": "Paste your answer (and question, if relevant):",
        "placeholder": "e.g. Question: What is photosynthesis?\nMy answer: Plants make food from sunlight.",
        "max_tokens": 700,
    },
    "Explain a Concept": {
        "label": "Enter the concept or topic you want explained:",
        "placeholder": "e.g. Explain Newton's second law of motion",
        "max_tokens": 700,
    },
}

config = FEATURE_CONFIG[feature]
user_input = st.text_area(
    config["label"],
    height=220,
    placeholder=config["placeholder"],
)

col1, col2 = st.columns(2)
with col1:
    generate_clicked = st.button("Generate", type="primary")


def build_prompt(selected_feature: str, text: str) -> str:
    if selected_feature == "Summarize Notes":
        return (
            "You are a helpful study assistant. Summarize the following student notes into 5 to 8 clear, concise bullet points suitable for exam revision. Keep key facts, numbers, and definitions, and avoid adding information not in the notes.\n\n"
            f"Notes:\n{text}\n\nReturn only the bullet-point summary."
        )
    if selected_feature == "Generate Quiz":
        return (
            "You are a helpful study assistant. Based on the following notes or topic, generate 5 quiz questions to help a student test their understanding. Include a mix of short-answer and multiple-choice questions. After all questions, provide an 'Answer Key' section with the correct answers.\n\n"
            f"Content:\n{text}\n\nFormat clearly with numbered questions."
        )
    if selected_feature == "Improve My Answer":
        return (
            "You are a helpful study assistant. The student has written an answer below. Rewrite it into a stronger, clearer, more complete answer suitable for exams, while keeping their original meaning and intent. After the improved answer, add a short 'What was improved' section listing 2-3 specific changes.\n\n"
            f"Student's answer:\n{text}\n\n"
        )
    if selected_feature == "Explain a Concept":
        return (
            "You are a helpful study assistant. Explain the following concept in simple, clear language suitable for a student. Include: a short plain-language definition, one real-world example or analogy, and 2-3 key points to remember.\n\n"
            f"Concept:\n{text}\n\n"
        )
    raise ValueError(f"Unknown feature: {selected_feature}")


def validate_input(text: str):
    if not text or not text.strip():
        return "Please enter some content before generating."
    if len(text.strip()) < MIN_CHARS:
        return f"Your input looks too short (minimum {MIN_CHARS} characters)."
    if len(text) > MAX_CHARS:
        return f"Your input is too long (max {MAX_CHARS} characters). Try a shorter section."
    return None


def stream_groq_response(prompt: str, max_tokens: int):
    """
    Streams response token-by-token. If the primary model queues or times out,
    it falls over to a lightweight/high-availability model.
    """
    models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]

    last_error = None
    for model_name in models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert, encouraging academic study assistant.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                max_tokens=max_tokens,
                temperature=0.3,
                stream=True,
            )

            has_yielded = False
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    has_yielded = True
                    yield chunk.choices[0].delta.content

            if has_yielded:
                return

        except Exception as e:
            last_error = e
            # Failover if there is a timeout, queue saturation, or model unavailability
            err_msg = str(e).lower()
            if any(term in err_msg for term in ["timed out", "timeout", "503", "404", "model_not_found"]):
                continue
            raise e

    if last_error:
        raise last_error


if generate_clicked:
    validation_err = validate_input(user_input)
    if validation_err:
        st.warning(validation_err)
    else:
        try:
            prompt = build_prompt(feature, user_input)
            st.subheader(f"📝 Result: {feature}")

            # Stream chunks to UI as they arrive over HTTP
            st.write_stream(stream_groq_response(prompt, config["max_tokens"]))

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate_limit" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                st.warning("⏳ Groq rate limit reached. Please wait ~30-60 seconds before trying again.")
            elif "timed out" in err_str.lower():
                st.error("Connection timed out. Please check your internet connection or proxy settings.")
            else:
                st.error("Failed to generate response. Check technical details below.")

            with st.expander("Technical details (for debugging)"):
                st.code(err_str)

st.divider()
st.caption("Tip: pick the feature that matches your input, then hit Generate.")