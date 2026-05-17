import json
from fastapi import HTTPException
from config import anthropic_client, groq_client, CLAUDE_MODEL, GROQ_MODEL
from models import ExtractedIntelligence
from rule_extraction import rule_based_extract

SYSTEM_PROMPT = """
You are a query intelligence engine for a corporate research platform.
Given a natural language query, extract structured fields as JSON.

Return ONLY a valid JSON object - no markdown fences, no explanation.

Fields to extract:
- intent      : what the user wants to do (e.g. "find", "compare", "monitor")
- geography   : any geographic scope (e.g. "Southeast Asia", "US", null)
- domain      : industry or technology area (e.g. "battery technology", "fintech")
- entity_type : type of entity being researched (e.g. "startups", "companies", "patents")
- keywords    : list of key search terms (array of strings)
- temporal    : any time-related constraint (e.g. "last 5 years", "2023", null)

Example input : "find battery technology startups in Southeast Asia over the last 5 years"
Example output:
{
  "intent": "find",
  "geography": "Southeast Asia",
  "domain": "battery technology",
  "entity_type": "startups",
  "keywords": ["battery technology", "startups", "Southeast Asia"],
  "temporal": "last 5 years"
}
""".strip()


def _call_anthropic(query: str) -> str:
    """Call Claude and return raw response text. Raises on failure."""
    response = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}],
    )
    return response.content[0].text.strip()


def _call_groq(query: str) -> str:
    """Call Groq and return raw response text. Raises on failure."""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": query},
        ],
        temperature=0,
    )
    choice = response.choices[0].message.content
    return choice.strip() if isinstance(choice, str) else str(choice).strip()


def _parse_raw(raw_text: str) -> dict:
    """Strip markdown fences if present, then JSON-parse the text."""
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {}


def extract_intelligence(query: str) -> ExtractedIntelligence:
    """
    Extract structured intelligence from a natural language query.

    Three-tier strategy (each tier is tried only if the previous fails):
      1. Anthropic Claude  — primary, highest quality
      2. Groq (Llama)      — secondary, still LLM-quality
      3. Rule-based engine — last resort, no network required

    The function always returns a result; it never raises an HTTP error.
    """
    raw_text = ""

    # Tier 1: Anthropic
    if anthropic_client is not None:
        try:
            raw_text = _call_anthropic(query)
            print("[extraction] Provider: Anthropic (Claude)")
        except Exception as exc:
            print(f"[extraction] Anthropic failed: {exc}")

    # Tier 2: Groq
    if not raw_text and groq_client is not None:
        try:
            raw_text = _call_groq(query)
            print("[extraction] Provider: Groq (Llama)")
        except Exception as exc:
            print(f"[extraction] Groq failed: {exc}")

    # Tier 3: Rule-based (no network, no api keys needed)
    if not raw_text:
        print("[extraction] Provider: rule-based fallback")
        return rule_based_extract(query)

    data = _parse_raw(raw_text)

    return ExtractedIntelligence(
        **{k: v for k, v in data.items() if k in ExtractedIntelligence.model_fields}
    )