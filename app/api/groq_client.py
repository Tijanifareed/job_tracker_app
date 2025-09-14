import os
import re
import json
import requests
import logging
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def analyze_resume_with_groq(resume_text: str, job_description: str) -> dict:
    if not GROQ_API_KEY:
     raise RuntimeError("GROQ_API_KEY not set in environment")
    """
    Sends resume and JD to Groq API and extracts structured insights.
    Always returns a dict with keys: score, missing_keywords, suggestions.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0,

        "messages": [
            {
               "role": "system",
    "content": (
        "You are an professional ATS resume scoring assistant. "
        "You are to think step by step"
        "Your job is to always return a structured JSON object ONLY, in this format:\n"
        "{\n"
        '  "ats_score": <int 0-100>,\n'
        '  "keyword_match_score": <int 0-100>,\n'
        '  "missing_keywords": [<list of strings>],\n'
        '  "suggestions": [<list of strings>]\n'
        "}\n\n"
        "Rules you MUST follow:\n"
        "1. Extract ALL important hard skills, soft skills, tools, and role-specific terms from the Job Description (JD). "
        "Never skip or summarize. Even if the resume partially covers them, list the missing ones clearly.\n"
        "2. ats_score is the overall fit (skills, formatting, clarity, seniority match).\n"
        "3. keyword_match_score is strictly based on the % of JD keywords found in the resume. "
        "Do not invent or omit keywords.\n"
        "4. missing_keywords must always be an exhaustive list of terms from the JD that are NOT clearly found in the resume and note: you must return all missing keywords. "
        "Never output an empty list unless the resume matches 100% of the JD.\n"
        "5. suggestions must be 4–10 short, plain-language tips that even a beginner job seeker can follow. "
        "Examples: \"Add more of the required keywords\", \"Show achievements with numbers\", "
        "\"Make your skills easier to spot\", \"Match your job titles to the JD more closely\".\n"
        "6. Be deterministic. Given the same JD and resume, you MUST always return the same results. "
        "Do not randomize or vary answers between runs.\n"
        "7. Do not include anything outside the JSON object."
    ),
          },

            {
                "role": "user",
                "content": f"""
          Job Description:
          {job_description}

          Resume:
          {resume_text}
          """
            },
        ],
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Extract JSON safely
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group())

    except Exception as e:
     logger.error(f"Groq API call failed: {e}")
     return {
          "ats_score": 0,
          "keyword_match_score": 0,
          "missing_keywords": [],
          "suggestions": [f"Groq API failed: {str(e)}"]
     }

