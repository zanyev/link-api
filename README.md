# Linking Service (link-api)

FastAPI service to ingest catalog items from CSV, generate embeddings with OpenAI, store them in Postgres/pgvector, build clusters of similar items, and search across items with cluster context.

## Features
- CSV ingestion of supplier item catalogs (supports two header formats).
- Batch OpenAI embeddings (text-embedding-3-small) for name+description.
- Storage with SQLModel on PostgreSQL + pgvector.
- Clustering via SVM score + graph connected components snapshot.
- Search nearest items by embedding and return associated items per cluster.

## Tech Stack
- Python 3.12, FastAPI
- SQLModel, PostgreSQL, pgvector, psycopg2-binary
- NetworkX, NumPy, Pandas, scikit-learn
- OpenAI (Embeddings)
- Pydantic v2, pydantic-settings, python-dotenv

## Project Structure
- `main.py`: FastAPI app bootstrap
- `endpoints/routers/item.py`: Item endpoints (CSV ingest, link job, search)
- `core/config.py`: App settings, OpenAI client, SQL/weights
- `core/database.py`: SQLModel engine and migrations bootstrap
- `models/`: SQLModel tables (`RawItem`, `ItemClusterSnapshot`)
- `services/item.py`: CSV normalization, embeddings, copy to Postgres, search
- `services/link_job.py`: Similarity query, SVM score, graph clustering, snapshot
- `schemas/item.py`: Response models for search
- `db_create.py`: Helper to create tables and insert sample data
- `data/`: Example CSVs

## Requirements
- Python 3.12+
- PostgreSQL with pgvector extension
- OpenAI API key

## Environment Variables
Create a `.env` file in `link-api/` with:
- `OPENAI_API_KEY=<your_key>`
- Optionally adjust Postgres URL in `core/database.py` if not using defaults.

Default DB URL (change if needed):
`postgresql+psycopg2://linkuser:secret@localhost:5435/link-db`

## Database Setup
1. Install pgvector in your Postgres:
   - `CREATE EXTENSION IF NOT EXISTS vector;`
   - `CREATE EXTENSION IF NOT EXISTS pg_trgm;`
2. Ensure a database `link-db` and user `linkuser` with password `secret` exist.
3. Create tables and optional seed data:
   - Run `db_create.py` or start the API and ingest CSVs which will auto-create on first import.

## Install & Run (uv / pip)
- Using uv (recommended):
  - `uv sync`
  - `uv run fastapi dev main.py` (or `uv run python -m fastapi dev main.py`)
- Using pip:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -e .`
  - `fastapi dev main.py`

API will be available at `http://localhost:8000` with docs at `/docs` and `/redoc`.

## Endpoints
- POST `/item/csv` — Upload CSV to ingest items
  - Form field: `file` (CSV)
  - Response: `{ message }`
- POST `/item/link` — Generate cluster snapshots
  - Response: `{ message }`
- GET `/item/search?q=<query>&top_k=<n>` — Search items with cluster context
  - Response: `{ results: [ ... ] }`

## CSV Formats Supported
Two header formats are auto-detected:
- Format t1 (example columns):
  - `codigo` → business_id
  - `produto` → name
  - `marca` → brand_name
  - `descricao` → description
  - `preco` → price
  - Optional: `categoria`, `unidade`
- Format t2 (example columns):
  - `sku` → business_id
  - `nome_do_item` → name
  - `fabricante` → brand_name
  - `caracteristicas` → description
  - `valor` → price
  - Optional: `ncm` (category), `unidade_medida` (unit_type), `estoque` (stock)

During ingestion:
- The service batches embedding requests for efficiency.
- Rows are written with `COPY` into `raw_item` including a `name_description_embedding` vector(1536).

## Clustering Logic
- Similarities are computed via `settings.similarity_query`:
  - Uses `pg_trgm` similarity on `name` and `description` and a vector similarity filter.
- A linear SVM score is applied: `svm = X·w + bias` with `w_vector` and `bias` from settings.
- Items with `pred_shift == 0` produce edges; connected components become clusters.
- A snapshot run is persisted to `item_cluster_snapshot` with a generated `cluster_run_id`.

## Search Response Shape
Each result includes:
- Basic item fields plus `distance` (embedding distance)
- `cluster_ids`: list of cluster IDs it belongs to (from latest snapshot)
- `associated_items`: map `cluster_id -> [items]` for items in the same cluster (excluding the item itself)

## Example Usage
1. Ingest examples:
   - Use `/item/csv` with `data/exemplo_fornecedor_a.csv` or `data/exemplo_fornecedor_b.csv`.
2. Run linking:
   - POST `/item/link`
3. Search:
   - GET `/item/search?q=notebook gamer 16gb ram&top_k=1`

## Notes
- Ensure your OpenAI usage complies with your quota and model availability.
- Adjust `settings.similarity_query`, SVM `w_vector` and `bias` to tune clustering.
- For large files, the max upload size is `settings.max_size` (default 20MB).


