import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import QueryRequest, QueryResponse
from extraction import extract_intelligence
from database import save_query, fetch_query

app = FastAPI(title="Query Intelligence API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes 
@app.get("/")
def read_root():
    return {"message": "Query Intelligence API is running!", "status": "healthy"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/queries", response_model=QueryResponse, status_code=201)
def create_query(body: QueryRequest):
    """
    Accept a natural language query, extract structured intelligence
    via an LLM, persist the result, and return the full record.
    """
    if not body.query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    extracted = extract_intelligence(body.query)
    return save_query(body.query, extracted)


@app.get("/queries/{query_id}", response_model=QueryResponse)
def get_query(query_id: str):
    """Return a previously stored query and its extracted intelligence by ID."""
    return fetch_query(query_id)


# Entrypoint 
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="localhost", port=port, timeout_keep_alive=300)