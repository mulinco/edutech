import os
import psycopg2
import logging
from dotenv import load_dotenv
from typing import Dict, Optional


# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

DB_CONFIG: Dict[str, Optional[str]] = {
    "dbname": os.getenv("DB_NAME", "edutech_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_db_connection():
    """
    Cria e retorna uma nova conexão com o banco de dados PostgreSQL.
    
    Utiliza a configuração centralizada (DB_CONFIG) lida do .env.
    Retorna 'None' em caso de falha na conexão.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("Conexão com o banco de dados bem-sucedida.")
        return conn
    except psycopg2.Error as e:
        # Se a conexão falhar, registra o erro e retorna None
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

