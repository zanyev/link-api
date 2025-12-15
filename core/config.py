from pydantic_settings import BaseSettings
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

class AppSettings(BaseSettings):
    """Application settings using Pydantic."""

    max_size: int = 20 * 1024 * 1024  # 20MB

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

client = OpenAI()
settings = AppSettings()
