from sqlmodel import SQLModel, create_engine

postgres_url = "postgresql+psycopg2://linkuser:secret@localhost:5435/link-db"

engine = create_engine(postgres_url, echo=False)

def create_db_and_tables():
    # Import models here to ensure they are registered
    from models.item import RawItem
    from models.item_cluster_snapshot import ItemClusterSnapshot

    SQLModel.metadata.create_all(engine)
    print("Database and tables created.")
