# Astra DB Integration

CuraAssist CareHub uses Astra DB as an AI/vector-data layer alongside its existing application database and Supabase services.

## Runtime configuration

Set these variables in the backend deployment environment:

- `ASTRA_DB_API_ENDPOINT`
- `ASTRA_DB_APPLICATION_TOKEN`
- `ASTRA_DB_KEYSPACE` (optional; defaults to `default_keyspace`)

Never commit the application token to GitHub or expose it to the frontend.

## Current integration boundary

The initial integration only establishes a lazy, authenticated Astra Data API connection. It does not create collections or move application data.

Backend module:

`application/backend/app/database/astra.py`

The module exposes:

- `is_astra_configured()`
- `get_astra_database()`
- `get_astra_collection(name)`
- `check_astra_connection()`

## Planned AI layer

The Astra database is intended for AI-oriented workloads such as:

- healthcare knowledge retrieval
- vector search
- RAG context
- AI document embeddings
- future semantic/hybrid retrieval

Supabase/Auth and the application's transactional data remain separate responsibilities.

## Vector schema

No Astra collection is created by this foundation change. The embedding model, vector dimensions, similarity metric, metadata schema, and collection name will be finalized before the first vector collection is created.
