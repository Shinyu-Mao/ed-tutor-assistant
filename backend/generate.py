"""
RAG answer generation using the Claude API.
Takes a new question + retrieved past Q&A records and drafts a reply.
"""

import os
import anthropic

_client: anthropic.Anthropic | None = None

STYLE_INSTRUCTIONS = {
    "friendly":  "Be direct and friendly. Write in natural prose.",
    "formal":    "Use a formal, professional tone. Avoid contractions.",
    "bullet":    "Respond using short bullet points. No long paragraphs.",
    "detailed":  "Provide a thorough explanation with reasoning and examples where helpful.",
}


def _get_client(api_key: str | None = None) -> anthropic.Anthropic:
    global _client
    # If a per-request key is provided, use it directly (no caching)
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    # Otherwise use the cached client backed by .env
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def build_prompt(
    title: str,
    question: str,
    matches: list[dict],
    style: str = "friendly",
    max_words: int = 150,
) -> str:
    context_blocks = []
    for m in matches:
        answers_text = "\n".join(f"  - {a}" for a in m["answers"])
        context_blocks.append(
            f"[Thread #{m['number']} — {m['title']}]\n"
            f"Question: {m['question']}\n"
            f"Staff answer(s):\n{answers_text}"
        )
    context = "\n\n---\n\n".join(context_blocks)
    style_note = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["friendly"])

    return f"""You are a teaching assistant for a university information retrieval course (INFS7410).
A student has posted the following question on Ed Discussion.

STUDENT QUESTION TITLE: {title}
STUDENT QUESTION BODY:
{question}

Below are the most relevant past Q&A records from this course's discussion board:

{context}

---

Using the past Q&A as your primary reference, draft a reply to the student's question.
- {style_note}
- If the past records answer the question well, adapt that answer to the specific phrasing of this question.
- If the question is slightly different, acknowledge it and fill the gap with relevant course knowledge.
- Do NOT mention that you are an AI or that you searched a database.
- Keep the reply under {max_words} words.
- Start with "Hi," and end naturally.
"""


def generate_answer(
    title: str,
    question: str,
    matches: list[dict],
    api_key: str | None = None,
    style: str = "friendly",
    max_words: int = 150,
) -> str:
    prompt = build_prompt(title, question, matches, style=style, max_words=max_words)
    client = _get_client(api_key=api_key)
    # Rough token budget: 1 word ≈ 1.3 tokens
    max_tokens = min(int(max_words * 1.5), 1024)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()
