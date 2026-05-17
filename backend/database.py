from fastapi import HTTPException
from config import supabase_client
from models import ExtractedIntelligence, QueryResponse

TABLE = "queries"


def _row_to_response(row: dict) -> QueryResponse:
    """Convert a raw Supabase row dict into a QueryResponse model."""
    return QueryResponse(
        id=row["id"],
        raw_query=row["raw_query"],
        extracted=ExtractedIntelligence(
            intent=row.get("intent"),
            geography=row.get("geography"),
            domain=row.get("domain"),
            entity_type=row.get("entity_type"),
            keywords=row.get("keywords"),
            temporal=row.get("temporal"),
        ),
        created_at=str(row["created_at"]),
    )


def save_query(raw_query: str, extracted: ExtractedIntelligence) -> QueryResponse:
    """Insert a new query record and return the saved response."""
    row = {
        "raw_query":   raw_query,
        "intent":      extracted.intent,
        "geography":   extracted.geography,
        "domain":      extracted.domain,
        "entity_type": extracted.entity_type,
        "keywords":    extracted.keywords,   # stored as JSONB
        "temporal":    extracted.temporal,
    }

    result = supabase_client.table(TABLE).insert(row).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to persist query to database.")

    return _row_to_response(result.data[0])


def fetch_query(query_id: str) -> QueryResponse:
    """Fetch a single query record by UUID. Raises 404 if not found."""
    result = (
        supabase_client.table(TABLE)
        .select("*")
        .eq("id", query_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail=f"Query '{query_id}' not found.")

    return _row_to_response(result.data[0])