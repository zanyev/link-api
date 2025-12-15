from core.config import settings
from core.database import engine
from sqlmodel import text
import numpy as np
import pandas as pd
import networkx as nx
import uuid
from sqlalchemy import insert
from models.item_cluster_snapshot import ItemClusterSnapshot


def persist_clusters_bulk_engine(engine, rows: list[dict]):
    if not rows:
        return

    stmt = insert(ItemClusterSnapshot)

    with engine.begin() as conn:
        conn.execute(stmt, rows)


def generate_clusters():
    with engine.connect() as conn:
        result = conn.execute(text(settings.similarity_query))
        all_items = conn.execute(
            text("SELECT id FROM raw_item")
        ).fetchall()

        df = pd.DataFrame(result.fetchall())

    all_item_ids = {row[0] for row in all_items}

    # ===== SVM =====
    X = np.column_stack([
        df.sim_name,
        df.sim_desc
    ])

    svm_score = np.dot(X, settings.w_vector) + settings.bias
    df["pred_shift"] = (svm_score > 0).astype(int)

    # ===== GRAPH =====
    edges_df = df[df["pred_shift"] == 0][["item_1_id", "item_2_id"]]

    G = nx.Graph()
    G.add_edges_from(edges_df.itertuples(index=False))

    clusters = list(nx.connected_components(G))

    items_in_graph = set().union(*clusters) if clusters else set()
    singleton_items = all_item_ids - items_in_graph

    for item_id in singleton_items:
        clusters.append({item_id})

    # ===== SNAPSHOT ROWS =====
    run_id = uuid.uuid4()

    rows = [
        {
            "created_by": "system",
            "cluster_run_id": run_id,
            "cluster_id": cluster_id,
            "raw_item_id": raw_item_id
        }
        for cluster_id, item_ids in enumerate(clusters)
        for raw_item_id in item_ids
    ]

    return rows

def link_job():
    rows = generate_clusters()
    persist_clusters_bulk_engine(engine, rows)


if __name__ == '__main__':
    rows = generate_clusters()
    persist_clusters_bulk_engine(engine, rows)