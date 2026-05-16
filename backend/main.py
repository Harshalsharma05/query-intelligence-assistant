from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import anthropic
from groq import Groq
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = FastAPI(title="Query Intelligence API")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clients
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

llm = anthropic.Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None
groq_llm = Groq(api_key=groq_api_key) if groq_api_key else None

# Groq fallback model.
GROQ_MODEL = "llama-3.3-70b-versatile"

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


# Models
class QueryRequest(BaseModel):
    query: str


class ExtractedIntelligence(BaseModel):
    intent: Optional[str] = None
    geography: Optional[str] = None
    domain: Optional[str] = None
    entity_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    temporal: Optional[str] = None


class QueryResponse(BaseModel):
    id: str
    raw_query: str
    extracted: ExtractedIntelligence
    created_at: str


# LLM Extraction
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


def extract_intelligence(query: str) -> ExtractedIntelligence:
    """Call Claude to extract structured fields from the raw query."""
    raw_text = ""
    provider_error = None

    # Primary path: Anthropic SDK
    if llm is not None:
        try:
            response = llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": query}],
            )
            raw_text = response.content[0].text.strip()
        except Exception as exc:
            print(f"[extract_intelligence] Anthropic provider failed: {exc}")
            provider_error = f"Anthropic failed: {exc}"
            raw_text = ""

    # Fallback path: Groq
    if not raw_text and groq_llm is not None:
        try:
            response = groq_llm.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0,
            )
            choice = response.choices[0].message.content
            raw_text = choice.strip() if isinstance(choice, str) else str(choice).strip()
        except Exception as exc:
            print(f"[extract_intelligence] Groq provider failed: {exc}")
            provider_error = f"Groq failed: {exc}"
            raw_text = ""

    if not raw_text:
        # No provider configured or both providers failed.
        message = provider_error or "No LLM provider is configured. Set ANTHROPIC_API_KEY or GROQ_API_KEY."
        raise HTTPException(status_code=503, detail=message)

    # Strip accidental markdown fences if the model adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Graceful fallback - return what we have
        data = {}

    return ExtractedIntelligence(
        **{k: v for k, v in data.items() if k in ExtractedIntelligence.model_fields}
    )


# Endpoints
@app.post("/queries", response_model=QueryResponse, status_code=201)
def create_query(body: QueryRequest):
    """Accept a natural language query, extract intelligence, persist, return."""
    if not body.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    # 1. Extract structured intelligence via Claude
    extracted = extract_intelligence(body.query)

    # 2. Persist to Supabase
    row = {
        "raw_query": body.query,
        "intent": extracted.intent,
        "geography": extracted.geography,
        "domain": extracted.domain,
        "entity_type": extracted.entity_type,
        "keywords": extracted.keywords,  # stored as JSONB
        "temporal": extracted.temporal,
    }

    result = supabase.table("queries").insert(row).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to persist query")

    saved = result.data[0]

    return QueryResponse(
        id=saved["id"],
        raw_query=saved["raw_query"],
        extracted=ExtractedIntelligence(
            intent=saved.get("intent"),
            geography=saved.get("geography"),
            domain=saved.get("domain"),
            entity_type=saved.get("entity_type"),
            keywords=saved.get("keywords"),
            temporal=saved.get("temporal"),
        ),
        created_at=str(saved["created_at"]),
    )


@app.get("/queries/{query_id}", response_model=QueryResponse)
def get_query(query_id: str):
    """Return a stored query and its extracted intelligence by ID."""
    result = (
        supabase.table("queries")
        .select("*")
        .eq("id", query_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

    saved = result.data[0]

    return QueryResponse(
        id=saved["id"],
        raw_query=saved["raw_query"],
        extracted=ExtractedIntelligence(
            intent=saved.get("intent"),
            geography=saved.get("geography"),
            domain=saved.get("domain"),
            entity_type=saved.get("entity_type"),
            keywords=saved.get("keywords"),
            temporal=saved.get("temporal"),
        ),
        created_at=str(saved["created_at"]),
    )


@app.get("/")
def read_root():
    return {"message": "Query Intelligence API is running!", "status": "healthy"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=300)