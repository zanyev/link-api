from uuid import UUID
from sqlmodel import Session
from core.database import create_db_and_tables, engine
from models.item import RawItem
from models.item_cluster_snapshot import ItemClusterSnapshot


def insert_initial_data():
    with Session(engine) as session:
        raw_item = RawItem(
            created_by="system",
            business_id="BIZ123",
            name="Sample Item",
            brand_name="Sample Brand",
            description="This is a sample item.",
            category="Sample Category",
            unit_type="Sample Unit",
            price=19.99,
            stock=100,
            name_description_embedding=[0.0]*1536  # Example embedding vector
        )
        session.add(raw_item)
        session.flush()
        
        item_snapshot = ItemClusterSnapshot(
            created_by="system",
            cluster_run_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            cluster_id=1,
            raw_item_id=raw_item.id
        )
        session.add(item_snapshot)
        session.commit()


if __name__ == "__main__":
    create_db_and_tables()
    insert_initial_data()
