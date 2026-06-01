"""
RAG answer generation using the Claude API.
Takes a new question + retrieved past Q&A records and drafts a reply.
"""

import os
import anthropic

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def build_prompt(title: str, question: str, matches: list[dict]) -> str:
    context_blocks = []
    for m in matches:
        answers_text = "\n".join(f"  - {a}" for a in m["answers"])
        context_blocks.append(
            f"[Thread #{m['number']} — {m['title']}]\n"
            f"Question: {m['question']}\n"
            f"Staff answer(s):\n{answers_text}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are a teaching assistant for a university information retrieval course (INFS7410).
A student has posted the following question on Ed Discussion.

STUDENT QUESTION TITLE: {title}
STUDENT QUESTION BODY:
{question}

Below are the most relevant past Q&A records from this course's discussion board:

{context}

---

Using the past Q&A as your primary reference, draft a concise, helpful reply to the student's question.
- Be direct and friendly.
- If the past records answer the question well, adapt that answer to the specific phrasing of this question.
- If the question is slightly different, acknowledge it and fill the gap with relevant course knowledge.
- Do NOT mention that you are an AI or that you searched a database.
- Keep the reply under 150 words unless the question genuinely requires more detail.
- Start with "Hi," and end naturally.
"""


def generate_answer(title: str, question: str, matches: list[dict]) -> str:
    prompt = build_prompt(title, question, matches)
    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
