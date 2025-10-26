# Importei as ferramentas date e datetime para poder trabalhar com datas e horas
# como objetos inteligentes, e não como simples texto.
from datetime import date, datetime
import pytz  #Esta biblioteca serve para gerenciar fusos horários (time zones) em Python
import unicodedata #Esta biblioteca nativa ajuda lidar com caracteres unicode(acentos)
import random #Biblioteca para aleatorizar escolhas
import re
from typing import Optional, Union

def padronizar_data(data_obj: Optional[Union[date, datetime]], fuso_horario_str: str = 'America/Sao_Paulo') -> Optional[str]:
    """
Eu criei esta função para padronizar o formato das datas.
Ela pega um objeto de data ou data/hora do Python e o transforma numa
string no formato ISO, que é o padrão que o PostgreSQL entende e espera.
    """
    if isinstance(data_obj, datetime):
        # Se a data for "ingênua"(naive) (sem fuso horário), nós a tornamos "ciente".
        if data_obj.tzinfo is None:
            fuso = pytz.timezone(fuso_horario_str)
            data_obj = fuso.localize(data_obj)
        return data_obj.isoformat()
    elif isinstance(data_obj, date):
        # Objetos 'date' não têm hora, então o isoformat padrão é suficiente.
        return data_obj.isoformat()
    return None


def criar_email_do_nome(nome_completo: str) -> str:
    """
    Cria um endereço de email realista a partir de um nome completo.

    Exemplo: 'Ana Silva' -> 'ana.silva@example.com'
    """
    # Responsável por remover acentos e caracteres especiais
    nome_normalizado = unicodedata.normalize('NFD', nome_completo).encode('ascii', 'ignore').decode('utf-8')
    
    # Converte para minúsculas e substitui espaços por pontos
    partes_nome = nome_normalizado.lower().split()
    nome_para_email = ".".join(partes_nome)
    
    # Adiciona um número aleatório no final para diminuir a chance de duplicatas
    sufixo_aleatorio = str(random.randint(10, 99))
    
    # Sorteia um domínio genérico
    dominios = ['@example.com', '@example.net', '@example.org']
    
    return f"{nome_para_email}{sufixo_aleatorio}{random.choice(dominios)}"



def validar_email(email: Optional[str]) -> bool:
    """
    Valida o formato de um endereço de email usando uma expressão regular simples.

    Args:
        email (str): A string do email a ser validada.

    Returns:
        bool: True se o formato for válido, False caso contrário.
    """
    if not isinstance(email, str):
        return False
    # Expressão regular simples para o formato 'algo@algo.algo'
    padrao: str = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None