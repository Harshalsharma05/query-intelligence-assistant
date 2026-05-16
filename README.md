# Spark Studios Task — Query Intelligence Platoform Prototype

This repository contains a small Query Intelligence prototype with two main parts:

- `backend/` — FastAPI service that accepts natural-language queries, extracts structured fields (intent, geography, domain, entity_type, keywords, temporal), and stores them in Supabase.
- `frontend/` — Next.js app with a compact chat-like UI that submits queries and displays the extracted fields.

## Short overview

- Backend: `POST /queries` (create & extract) and `GET /queries/{id}` (retrieve). Primary LLM: Anthropic Claude; optional GROQ fallback (configure with `GROQ_API_KEY`/`GROQ_API_URL`). See `backend/README.md` for full details.
- Frontend: Minimal chat interface (single text input) that POSTs `{ query }` to a proxy route or directly to the backend and renders the structured `extracted` result.

# Endpoints

## 1. Create & Extract Query

Extracts structured metadata from a natural language query and stores it.

### Endpoint

```http
POST /queries
```

### Request Body

```json
{
  "query": "Show me solar panel installations in Texas in 2023 for residential properties"
}
```

### Example Request

```bash
curl -X POST /queries \
  -H "Content-Type: application/json" \
  -d '{
    "query":"Show me solar panel installations in Texas in 2023 for residential properties"
  }'
```

### Sample Response

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "Show me solar panel installations in Texas in 2023 for residential properties",
  "extracted": {
    "intent": "search",
    "geography": "Texas",
    "domain": "energy",
    "entity_type": "installations",
    "keywords": ["solar", "residential"],
    "temporal": "2023"
  }
}
```

---

## 2. Retrieve Query by ID

Fetches a previously stored query along with its extracted metadata.

### Endpoint

```http
GET /queries/{id}
```

### Example Request

```bash
curl /queries/123e4567-e89b-12d3-a456-426614174000
```

### Sample Response

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "Show me solar panel installations in Texas in 2023 for residential properties",
  "extracted": {
    "intent": "search",
    "geography": "Texas",
    "domain": "energy",
    "entity_type": "installations",
    "keywords": ["solar", "residential"],
    "temporal": "2023"
  }
}
```

---

# Example Queries

```json
{
  "query": "Which cities in California had the highest EV charging station growth in 2022?"
}
```

```json
{
  "query": "Find commercial wind energy projects in New York after 2021"
}
```

```json
{
  "query": "Show residential solar adoption trends in Florida for 2020"
}
```

---

# Frontend Preview

![Frontend Chat UI](frontend/public/demo.png)

# Possible Improvements / Future Scope

## 1. Redis Caching Layer

To improve performance and scalability, Redis can be added as a caching layer between the API and the database.

Currently, every query retrieval requires a database lookup. With Redis, frequently accessed queries and extracted results can be stored in memory for much faster access.

This would help in scenarios such as:
- repeated query searches
- active user sessions
- faster API response times
- reduced database load

### Proposed Flow

```text
Client Request
      ↓
   FastAPI
      ↓
Redis Cache (fast retrieval)
      ↓
 PostgreSQL Database
```

### Example Use Cases

- Cache recently processed queries
- Store temporary session data
- Cache LLM extraction results
- Improve performance for repeated requests

This makes the backend more production-ready and scalable for larger workloads.

---

## 2. Semantic Search Over Historical Queries

Currently, queries can only be retrieved using their unique ID.

A future improvement would be to add semantic search using vector embeddings. Instead of exact keyword matching, the system would understand the meaning of user queries and return similar previously stored queries.

### Example

If a user searches:

```text
EV battery startups in Asia
```

the system could also return related stored queries such as:
- lithium battery companies in Southeast Asia
- energy storage startups
- electric vehicle battery manufacturers

even if the wording is different.

### Proposed Enhancement

- Generate embeddings for each stored query
- Store embeddings using a vector database such as:
  - pgvector
  - Pinecone
  - ChromaDB
- Perform similarity search during retrieval

### Benefits

- smarter query discovery
- improved research experience
- related query recommendations
- better knowledge retrieval across historical searches

This would transform the project from a simple query storage system into a more intelligent research assistant backend.


## Quick setup

1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # or create .env with required keys
uvicorn main:app --reload --port 8000
```

2. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

# Author

**Harshal Sharma**  
Created as part of the **Spark Studios Internship Assignment**.
