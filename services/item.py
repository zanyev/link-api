from sqlmodel import Session, text
from typing import BinaryIO
from fastapi import UploadFile, File
from fastapi import HTTPException
import csv
import io
from core.config import settings
from core.config import client



def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts at once."""
    response = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    return [item.embedding for item in response.data]

def detect_format_from_header(header: list[str]) -> str:
    if "produto" in header and "preco" in header:
        return "t1"
    if "nome_do_item" in header and "valor" in header:
        return "t2"
    raise ValueError("Unknown CSV format")

def normalize_csv(file) -> io.StringIO:
    """Normalize CSV and generate embeddings in batches."""
    file.seek(0)
    input_stream = io.TextIOWrapper(file, encoding="utf-8", newline="")
    reader = csv.DictReader(input_stream)

    if not reader.fieldnames:
        raise ValueError("CSV without header")

    fmt = detect_format_from_header(reader.fieldnames)
    mapping = settings.t1_mapping if fmt == "t1" else settings.t2_mapping

    # Primeira passada: coleta todos os dados
    rows_data = []
    embedding_texts = []
    
    for row in reader:
        name = row.get(next(k for k, v in mapping.items() if v == "name")) or ""
        description = row.get(next(k for k, v in mapping.items() if v == "description")) or ""
        
        rows_data.append({
            "business_id": row.get(next(k for k, v in mapping.items() if v == "business_id")),
            "name": name,
            "brand_name": row.get(next(k for k, v in mapping.items() if v == "brand_name")),
            "description": description,
            "price": row.get(next(k for k, v in mapping.items() if v == "price")),
            "stock": row.get(next((k for k, v in mapping.items() if v == "stock"), None)),
            "category": row.get(next((k for k, v in mapping.items() if v == "category"), None)),
            "unit_type": row.get(next((k for k, v in mapping.items() if v == "unit_type"), None)),
        })
        
        embedding_texts.append(f"{name}. {description[:200]}")
    
    # Gera todos embeddings de uma vez (OpenAI aceita até 2048 textos por request)
    embeddings = generate_embeddings_batch(embedding_texts)
    
    # Escreve CSV com embeddings
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "created_by",
        "business_id",
        "name",
        "brand_name",
        "description",
        "price",
        "stock",
        "category",
        "unit_type",
        "name_description_embedding"
    ])
    
    for row_data, embedding in zip(rows_data, embeddings):
        writer.writerow([
            "system",
            row_data["business_id"],
            row_data["name"],
            row_data["brand_name"],
            row_data["description"],
            row_data["price"],
            row_data["stock"],
            row_data["category"],
            row_data["unit_type"],
            embedding  # ou json.dumps(embedding) se preferir
        ])
    
    output.seek(0)
    return output


def copy_from_csv(
    db: Session,
    table_name: str,
    file: BinaryIO,
    columns: list[str],
    has_header: bool = True,
):
    """
    PostgreSQL COPY FROM STDIN using an existing SQLModel Session.
    """

    # Get raw psycopg connection
    raw_conn = db.connection().connection
    cursor = raw_conn.cursor()

    cols = ", ".join(columns)
    header = "HEADER" if has_header else ""

    sql = f"""
        COPY {table_name} ({cols})
        FROM STDIN
        WITH (FORMAT CSV, {header})
    """

    cursor.copy_expert(sql, file)

    # IMPORTANT: commit via Session, not raw_conn
    db.commit()

def ingest_items_csv(
    db: Session,
    file: UploadFile = File(...),
):
    
    """Ingest items from uploaded CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Invalid file type")

    if file.size and file.size > settings.max_size:
        raise HTTPException(413, "File too large")
    
    normalized_file = normalize_csv(file.file)

    copy_from_csv(
    db=db,
    table_name="raw_item",
    file=normalized_file,
    columns=[
        "created_by",
        "business_id",
        "name",
        "brand_name",
        "description",
        "price",
        "stock",
        "category",
        "unit_type",
        "name_description_embedding",
    ])
    return None

def search_items_with_clusters(db: Session, query: str, top_k: int = 10):
    """Search nearest items by embedding and include cluster ids only from the latest snapshot run. Also return associated items per found cluster."""
    embedding = generate_embeddings_batch([query])[0]
    emb_str = "[" + ",".join(str(x) for x in embedding) + "]"

    # Get latest cluster_run_id by created_at
    latest_run_sql = text(
        """
        SELECT ics.cluster_run_id
        FROM item_cluster_snapshot ics
        ORDER BY ics.created_at DESC
        LIMIT 1
        """
    )
    latest_row = db.exec(latest_run_sql).first()
    latest_run_id = latest_row[0] if latest_row else None

    # Build query filtering snapshots to the latest run
    if latest_run_id is not None:
        sql = text(
            """
            SELECT 
                ri.id,
                ri.business_id,
                ri.name,
                ri.brand_name,
                ri.description,
                ri.price,
                ri.stock,
                ri.category,
                ri.unit_type,
                ics.cluster_id,
                (ri.name_description_embedding <-> CAST(:emb AS vector(1536))) AS distance
            FROM raw_item ri
            LEFT JOIN item_cluster_snapshot ics 
                ON ics.raw_item_id = ri.id AND ics.cluster_run_id = :run_id
            ORDER BY ri.name_description_embedding <-> CAST(:emb AS vector(1536))
            LIMIT :k
            """
        )
        rows = db.exec(sql.bindparams(emb=emb_str, run_id=latest_run_id, k=top_k)).fetchall()
    else:
        # Fallback without clusters if none exist
        sql = text(
            """
            SELECT 
                ri.id,
                ri.business_id,
                ri.name,
                ri.brand_name,
                ri.description,
                ri.price,
                ri.stock,
                ri.category,
                ri.unit_type,
                NULL AS cluster_id,
                (ri.name_description_embedding <-> CAST(:emb AS vector(1536))) AS distance
            FROM raw_item ri
            ORDER BY ri.name_description_embedding <-> CAST(:emb AS vector(1536))
            LIMIT :k
            """
        )
        rows = db.exec(sql.bindparams(emb=emb_str, k=top_k)).fetchall()

    items: dict[int, dict] = {}
    cluster_ids: set[int] = set()
    for row in rows:
        item_id = row.id
        if item_id not in items:
            items[item_id] = {
                "id": row.id,
                "business_id": row.business_id,
                "name": row.name,
                "brand_name": row.brand_name,
                "description": row.description,
                "price": str(row.price) if row.price is not None else None,
                "stock": row.stock,
                "category": row.category,
                "unit_type": row.unit_type,
                "distance": float(row.distance) if row.distance is not None else None,
                "cluster_ids": [],
                "associated_items": {}
            }
        if row.cluster_id is not None and row.cluster_id not in items[item_id]["cluster_ids"]:
            items[item_id]["cluster_ids"].append(row.cluster_id)
            cluster_ids.add(row.cluster_id)

    # If we have clusters and latest_run_id, fetch associated items for those clusters
    if latest_run_id is not None and cluster_ids:
        assoc_sql = text(
            """
            SELECT 
                ics.cluster_id,
                ri.id,
                ri.business_id,
                ri.name,
                ri.brand_name,
                ri.description,
                ri.price,
                ri.stock,
                ri.category,
                ri.unit_type
            FROM item_cluster_snapshot ics
            JOIN raw_item ri ON ri.id = ics.raw_item_id
            WHERE ics.cluster_run_id = :run_id
              AND ics.cluster_id = ANY(:cluster_ids)
            """
        )
        assoc_rows = db.exec(assoc_sql.bindparams(run_id=latest_run_id, cluster_ids=list(cluster_ids))).fetchall()

        # Build a mapping cluster_id -> dict of associated items keyed by id (to avoid duplicates)
        cluster_to_items: dict[int, dict[int, dict]] = {}
        for arow in assoc_rows:
            cid = arow.cluster_id
            if cid not in cluster_to_items:
                cluster_to_items[cid] = {}
            # Upsert by id to keep one copy and avoid duplicates
            cluster_to_items[cid][arow.id] = {
                "id": arow.id,
                "business_id": arow.business_id,
                "name": arow.name,
                "brand_name": arow.brand_name,
                "description": arow.description,
                "price": str(arow.price) if arow.price is not None else None,
                "stock": arow.stock,
                "category": arow.category,
                "unit_type": arow.unit_type,
            }

        # Attach to each result only the clusters it belongs to, with de-duplicated associated items and excluding the item itself
        for item in items.values():
            assoc = {}
            for cid in item["cluster_ids"]:
                # Get items dict for this cluster and remove the current item id if present
                items_dict = cluster_to_items.get(cid, {})
                if items_dict:
                    # Build a unique list excluding the current item
                    assoc[cid] = [v for iid, v in items_dict.items() if iid != item["id"]]
                else:
                    assoc[cid] = []
            item["associated_items"] = assoc

    return list(items.values())


