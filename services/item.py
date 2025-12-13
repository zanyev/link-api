from sqlmodel import Session
from typing import BinaryIO
from fastapi import UploadFile, File
from fastapi import HTTPException
import csv
import io
from core.config import settings

def detect_format_from_header(header: list[str]) -> str:
    if "produto" in header and "preco" in header:
        return "t1"
    if "nome_do_item" in header and "valor" in header:
        return "t2"
    raise ValueError("Unknown CSV format")

def normalize_csv(file) -> io.StringIO:
    file.seek(0)

    input_stream = io.TextIOWrapper(file, encoding="utf-8", newline="")
    reader = csv.DictReader(input_stream)

    if not reader.fieldnames:
        raise ValueError("CSV without header")

    fmt = detect_format_from_header(reader.fieldnames)
    mapping = settings.t1_mapping if fmt == "t1" else settings.t2_mapping

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
    ])

    for row in reader:
        writer.writerow([
            "system",
            row.get(next(k for k, v in mapping.items() if v == "business_id")),
            row.get(next(k for k, v in mapping.items() if v == "name")),
            row.get(next(k for k, v in mapping.items() if v == "brand_name")),
            row.get(next(k for k, v in mapping.items() if v == "description")),
            row.get(next(k for k, v in mapping.items() if v == "price")),
            row.get(next((k for k, v in mapping.items() if v == "stock"), None)),
            row.get(next((k for k, v in mapping.items() if v == "category"), None)),
            row.get(next((k for k, v in mapping.items() if v == "unit_type"), None)),
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
    ])
    return None


