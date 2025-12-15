from pydantic_settings import BaseSettings
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv(override=True)

class AppSettings(BaseSettings):
    """Application settings using Pydantic."""

    max_size: int = 20 * 1024 * 1024  # 20MB

    w_vector : np.ndarray = np.array([-4.48104801, -3.03940367])  # Weights for name and description similarity
    
    bias: float = np.float64(3.966662191711139)  # Bias term for SVM


    t1_mapping: dict = {
        "codigo": "business_id",
        "produto": "name",
        "marca": "brand_name",
        "descricao": "description",
        "preco": "price",
        "categoria": "category",
        "unidade": "unit_type",
    }

    t2_mapping: dict = {
        "sku": "business_id",
        "nome_do_item": "name",
        "fabricante": "brand_name",
        "caracteristicas": "description",
        "valor": "price",
        "ncm": "category",
        "unidade_medida": "unit_type",
        "estoque": "stock",
    }

    similarity_query: str = """
    SELECT 
        a.id AS item_1_id,
        b.id AS item_2_id,
        similarity(a.name, b.name) AS sim_name,
        similarity(a.description, b.description) AS sim_desc
    FROM raw_item a
    JOIN raw_item b
    ON a.price BETWEEN b.price * 0.7 AND b.price * 1.3
    AND a.id < b.id
    WHERE 
        a.name IS NOT NULL
        AND b.name IS NOT NULL
        AND 1 - (a.name_description_embedding <=> b.name_description_embedding) >= 0.7
    """

client = OpenAI()
settings = AppSettings()
