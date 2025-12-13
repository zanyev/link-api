from uuid import UUID
from sqlmodel import Session
from core.database import create_db_and_tables, engine
from models.item import RawItem
from models.item_cluster import ItemCluster


def insert_initial_data():
    with Session(engine) as session:
        raw_item = RawItem(
            created_by="system",
            business_id="BIZ123",
            name="Sample Item",
            brand_name="Sample Brand",
            description="This is a sample item.",
            price=19.99,
            stock=100
        )
        session.add(raw_item)
        session.flush()
        # Create an item cluster
        item_cluster = ItemCluster(
            created_by="system",
            raw_item_id=raw_item.id,
            match_score=0.95
        )
        session.add(item_cluster)
        session.flush()
        session.commit()

if __name__ == "__main__":
    create_db_and_tables()
    insert_initial_data()
