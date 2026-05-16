# Spark Studios Task — Query Intelligence Platoform Prototype

This repository contains a small Query Intelligence prototype with two main parts:

- `backend/` — FastAPI service that accepts natural-language queries, extracts structured fields (intent, geography, domain, entity_type, keywords, temporal), and stores them in Supabase.
- `frontend/` — Next.js app with a compact chat-like UI that submits queries and displays the extracted fields.

## Short overview

- Backend: `POST /queries` (create & extract) and `GET /queries/{id}` (retrieve). Primary LLM: Anthropic Claude; optional GROQ fallback (configure with `GROQ_API_KEY`/`GROQ_API_URL`). See `backend/README.md` for full details.
- Frontend: Minimal chat interface (single text input) that POSTs `{ query }` to a proxy route or directly to the backend and renders the structured `extracted` result.

## API Usage

Base URL:

```txt
http://localhost:8000
```

---

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

Set `NEXT_PUBLIC_BACKEND_URL` (or `BACKEND_URL`) in the frontend environment if the backend is not at `http://localhost:8000`.
