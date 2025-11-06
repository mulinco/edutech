import psycopg2
import pandas as pd
from pathlib import Path
import sys
import tabulate
import logging
from typing import List, Optional, Union
from db_utils import get_db_connection

LOG_DIR = Path("logs") # Define o nome da pasta
LOG_DIR.mkdir(exist_ok=True) # Cria a pasta (não dá erro se ela já existir)

logging.basicConfig(level=logging.INFO, 
                    filename=LOG_DIR / 'relatorios.log', 
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- DEFINIÇÃO DE TODAS AS QUERIES DE RELATÓRIO ---

# 1. Queries do Dashboard Geral
SQL_DASH_TOTAL_ALUNOS: str = "SELECT COUNT(id) AS total_alunos FROM aluno;"
SQL_DASH_TOTAL_CURSOS: str = "SELECT COUNT(id) AS total_cursos FROM curso;"
SQL_DASH_MATRICULAS_ATIVAS: str = "SELECT COUNT(id) AS matriculas_ativas FROM matricula WHERE status = 'ativa';"
SQL_DASH_RECEITA_TOTAL: str = "SELECT COALESCE(SUM(valor), 0.00) AS receita_total FROM pagamento WHERE status_pagamento = 'Aprovado';"

# 2. Relatório de Performance de Instrutores
SQL_RELATORIO_INSTRUTORES: str = """
    SELECT
        i.nome AS "Instrutor",
        COUNT(DISTINCT c.id) AS "Total de Cursos",
        COUNT(DISTINCT m.aluno_id) AS "Total de Alunos Únicos",
        ROUND(COALESCE(AVG(av.nota), 0.0), 2) AS "Média Geral de Avaliações"
    FROM instrutor i
    LEFT JOIN curso c ON i.id = c.instrutor_id
    LEFT JOIN matricula m ON c.id = m.curso_id
    LEFT JOIN avaliacoes av ON c.id = av.curso_id
    GROUP BY i.id, i.nome
    ORDER BY "Média Geral de Avaliações" DESC, "Total de Alunos Únicos" DESC;
"""

# 3. Cursos com Baixa Taxa de Conclusão (< 30%)
SQL_BAIXA_CONCLUSAO: str = """
    WITH AulasPorCurso AS (
        SELECT m.curso_id, COUNT(a.id) AS total_aulas
        FROM aula a JOIN modulo m ON a.modulo_id = m.id GROUP BY m.curso_id
    ),
    ProgressoPorMatricula AS (
        SELECT
            m.curso_id,
            (COUNT(pa.aula_id) * 100.0) / apc.total_aulas AS percentual_concluido
        FROM matricula m
        JOIN AulasPorCurso apc ON m.curso_id = apc.curso_id
        LEFT JOIN progresso_aula pa ON m.id = pa.matricula_id AND pa.concluida = TRUE
        WHERE apc.total_aulas > 0 AND m.status IN ('ativa', 'concluida')
        GROUP BY m.id, m.curso_id, apc.total_aulas
    )
    SELECT
        c.titulo AS "Curso",
        ROUND(AVG(p.percentual_concluido), 2) AS "Taxa Média de Conclusão (%)"
    FROM curso c
    JOIN ProgressoPorMatricula p ON c.id = p.curso_id
    GROUP BY c.id, c.titulo
    HAVING AVG(p.percentual_concluido) < 30
    ORDER BY "Taxa Média de Conclusão (%)" ASC;
"""

# 4. Instrutores Mais Bem Avaliados (Média >= 4.5)
SQL_INSTRUTORES_BEM_AVALIADOS: str = """
    SELECT
        i.nome AS "Instrutor",
        ROUND(COALESCE(AVG(av.nota), 0.0), 2) AS "Média Geral"
    FROM instrutor i
    LEFT JOIN curso c ON i.id = c.instrutor_id
    LEFT JOIN avaliacoes av ON c.id = av.curso_id
    GROUP BY i.id, i.nome
    HAVING AVG(av.nota) >= 4.5
    ORDER BY "Média Geral" DESC;
"""

# 5. Categorias Mais Populares (por nº de matrículas)
SQL_CATEGORIAS_POPULARES: str = """
    SELECT
        cat.nome AS "Categoria",
        COUNT(m.id) AS "Total de Matrículas"
    FROM categoria cat
    LEFT JOIN curso c ON cat.id = c.categoria_id
    LEFT JOIN matricula m ON c.id = m.curso_id
    GROUP BY cat.id, cat.nome
    ORDER BY "Total de Matrículas" DESC;
"""

# 6. Matrículas por Mês (Análise Temporal)
SQL_MATRICULAS_POR_MES: str = """
    SELECT
        DATE_TRUNC('month', data_matricula)::DATE AS "Mês",
        COUNT(id) AS "Novas Matrículas"
    FROM matricula
    WHERE EXTRACT(YEAR FROM data_matricula) = EXTRACT(YEAR FROM CURRENT_DATE)
    GROUP BY "Mês"
    ORDER BY "Mês" ASC;
"""



# FUNÇÕES DE ANÁLISE E FORMATAÇÃO

def gerar_barra_ascii(valor: Optional[Union[int, float]], max_valor: Union[int, float], tamanho_max_barra: int = 30) -> str:
    """Gera uma barra de progresso simples em texto ASCII."""
    if max_valor == 0 or valor is None or pd.isna(valor):
        return ""
    proporcao = valor / max_valor
    tamanho_barra = int(proporcao * tamanho_max_barra)
    return "█" * tamanho_barra + " " * (tamanho_max_barra - tamanho_barra)

def analisar_dashboard(conn):
    """Executa as 4 queries do dashboard e retorna um texto em Markdown."""
    relatorio: List[str] = ["## 🚀 Dashboard Geral da Plataforma\n"]
    try:
        total_alunos: int = pd.read_sql_query(SQL_DASH_TOTAL_ALUNOS, conn).iloc[0]['total_alunos']
        total_cursos: int = pd.read_sql_query(SQL_DASH_TOTAL_CURSOS, conn).iloc[0]['total_cursos']
        matriculas_ativas: int = pd.read_sql_query(SQL_DASH_MATRICULAS_ATIVAS, conn).iloc[0]['matriculas_ativas']
        receita_total: float = pd.read_sql_query(SQL_DASH_RECEITA_TOTAL, conn).iloc[0]['receita_total']
        
        relatorio.append("| Métrica | Valor |")
        relatorio.append("| :--- | ---: |")
        relatorio.append(f"| Total de Alunos | {total_alunos} |")
        relatorio.append(f"| Total de Cursos | {total_cursos} |")
        relatorio.append(f"| Matrículas Ativas | {matriculas_ativas} |")
        relatorio.append(f"| Receita Total (Aprovada) | R$ {receita_total:,.2f} |")
    except Exception as e:
        logging.error(f"Erro ao gerar dados do dashboard: {e}") 
        relatorio.append(f"Erro ao gerar dados do dashboard: {e}")
    return "\n".join(relatorio)

def analisar_performance_instrutores(df: pd.DataFrame) -> str:
    """Recebe um DataFrame de instrutores e gera uma análise formatada."""
    relatorio: List[str] = ["## 📈 Relatório de Performance de Instrutores\n"]
    if df.empty:
        relatorio.append("Nenhum dado de instrutor encontrado.\n")
        return "\n".join(relatorio)
    
    top_instrutor_alunos: pd.Series = df.iloc[0]
    relatorio.append(df.to_markdown(index=False))
    relatorio.append("\n")
    
    relatorio.append("### Visualização: Média Geral de Avaliações (Max 5.0)\n")
    relatorio.append("```")
    for _, instrutor in df.iterrows():
        nome: str = str(instrutor['Instrutor']).ljust(20)
        media: float = instrutor['Média Geral de Avaliações']
        barra: str = gerar_barra_ascii(media, 5.0)
        relatorio.append(f"{nome} | {barra} | {media:.2f}/5.0")
    relatorio.append("```")
    
    relatorio.append("\n### 💡 Insights:\n")
    relatorio.append(f"- **Destaque:** `{top_instrutor_alunos['Instrutor']}` é o instrutor com o maior engajamento, com {top_instrutor_alunos['Total de Alunos Únicos']} alunos únicos.")
    
    return "\n".join(relatorio)

def analisar_baixa_conclusao(df: pd.DataFrame) -> str:
    """Recebe um DataFrame de cursos com baixa conclusão e gera uma análise."""
    relatorio: List[str] = ["## 📉 Relatório de Cursos com Baixa Taxa de Conclusão (< 30%)\n"]
    if df.empty:
        relatorio.append("✅ Boa notícia! Nenhum curso foi identificado com baixa taxa de conclusão.\n")
        return "\n".join(relatorio)
    
    relatorio.append(df.to_markdown(index=False))
    relatorio.append("\n")
    
    relatorio.append("\n### 💡 Insights:\n")
    relatorio.append("- **Ação Recomendada:** Estes cursos devem ser revisados. Verificar se o conteúdo está desatualizado, se há bugs nas aulas finais ou se o marketing está atraindo o público errado.")
    
    return "\n".join(relatorio)

def analisar_instrutores_bem_avaliados(df: pd.DataFrame) -> str:
    """Recebe um DataFrame de instrutores de elite."""
    relatorio: List[str] = ["## 🏆 Relatório de Instrutores Mais Bem Avaliados (Média >= 4.5)\n"]
    if df.empty:
        relatorio.append("Nenhum instrutor atingiu a média de 4.5 estrelas.\n")
        return "\n".join(relatorio)
    
    relatorio.append(df.to_markdown(index=False))
    relatorio.append("\n")
    
    relatorio.append("\n### 💡 Insights:\n")
    relatorio.append(f"- **Instrutores de Elite:** Temos **{len(df)}** instrutores com performance excepcional.")
    relatorio.append("- **Ação Recomendada:** Considerar estes instrutores para criar novos cursos de alto impacto e para programas de mentoria interna.")
    
    return "\n".join(relatorio)

def analisar_categorias_populares(df: pd.DataFrame) -> str:
    """Recebe um DataFrame de categorias e gera uma análise."""
    relatorio: List[str] = ["## 🔥 Relatório de Categorias Mais Populares\n"]
    if df.empty:
        relatorio.append("Nenhum dado de matrícula por categoria encontrado.\n")
        return "\n".join(relatorio)
        
    relatorio.append(df.to_markdown(index=False))
    relatorio.append("\n")
    
    relatorio.append("### Visualização: Popularidade por Categoria\n")
    relatorio.append("```")
    max_matriculas: int = df['Total de Matrículas'].max()
    for _, categoria in df.iterrows():
        nome: str = str(categoria['Categoria']).ljust(25)
        total: int = categoria['Total de Matrículas']
        barra: str = gerar_barra_ascii(total, max_matriculas)
        relatorio.append(f"{nome} | {barra} | {total} matrículas")
    relatorio.append("```")
    
    relatorio.append("\n### 💡 Insights:\n")
    top_categoria: pd.Series = df.iloc[0]
    relatorio.append(f"- **O Carro-Chefe:** `{top_categoria['Categoria']}` é a área mais popular da plataforma, responsável pela maioria das matrículas.")
    
    return "\n".join(relatorio)

def analisar_matriculas_por_mes(df: pd.DataFrame) -> str:
    """Recebe um DataFrame de matrículas ao longo do tempo."""
    relatorio: List[str] = ["## 📅 Relatório de Tendência de Matrículas (Ano Atual)\n"]
    if df.empty:
        relatorio.append("Nenhuma matrícula encontrada para o ano atual.\n")
        return "\n".join(relatorio)
        
    relatorio.append(df.to_markdown(index=False))
    relatorio.append("\n")
    
    relatorio.append("### Visualização: Novas Matrículas por Mês\n")
    relatorio.append("```")
    max_matriculas: int = df['Novas Matrículas'].max()
    for _, mes in df.iterrows():
        # Garante que 'Mês' é um objeto datetime antes de chamar strftime
        try:
            nome_mes: str = mes['Mês'].strftime('%Y-%m') # Formata a data para AAAA-MM
        except AttributeError:
            nome_mes: str = str(mes['Mês']).ljust(7) # Fallback se não for data
            
        total: int = mes['Novas Matrículas']
        barra: str = gerar_barra_ascii(total, max_matriculas)
        relatorio.append(f"{nome_mes} | {barra} | {total} matrículas")
    relatorio.append("```")
    
    return "\n".join(relatorio)


def main() -> None:
    """
    Função principal que se conecta ao banco, executa todas as queries
    e gera o relatório final em Markdown.
    """
    relatorio_final_md: List[str] = ["# 📊 Relatório de Análise da Plataforma EduTech\n"]
    conn = None
    
    try:
        conn = psycopg2.connect(get_db_connection)
        logging.info("Conexão com o banco de dados bem-sucedida.") 

        # --- Relatório 0: Dashboard Geral ---
        logging.info("Gerando relatório: Dashboard Geral...") 
        relatorio_final_md.append(analisar_dashboard(conn))
        relatorio_final_md.append("\n---\n")
        
        # --- Relatório 1: Performance de Instrutores ---
        logging.info("Gerando relatório: Performance de Instrutores...") 
        df_instrutores: pd.DataFrame = pd.read_sql_query(SQL_RELATORIO_INSTRUTORES, conn)
        relatorio_final_md.append(analisar_performance_instrutores(df_instrutores))
        relatorio_final_md.append("\n---\n")
        
        # --- Relatório 2: Baixa Conclusão ---
        logging.info("Gerando relatório: Cursos com Baixa Conclusão...") 
        df_baixa_conclusao: pd.DataFrame = pd.read_sql_query(SQL_BAIXA_CONCLUSAO, conn)
        relatorio_final_md.append(analisar_baixa_conclusao(df_baixa_conclusao))
        relatorio_final_md.append("\n---\n")

        # --- Relatório 3: Instrutores de Elite ---
        logging.info("Gerando relatório: Instrutores Mais Bem Avaliados...") 
        df_bem_avaliados: pd.DataFrame = pd.read_sql_query(SQL_INSTRUTORES_BEM_AVALIADOS, conn)
        relatorio_final_md.append(analisar_instrutores_bem_avaliados(df_bem_avaliados))
        relatorio_final_md.append("\n---\n")

        # --- Relatório 4: Categorias Populares ---
        logging.info("Gerando relatório: Categorias Mais Populares...") 
        df_categorias: pd.DataFrame = pd.read_sql_query(SQL_CATEGORIAS_POPULARES, conn)
        relatorio_final_md.append(analisar_categorias_populares(df_categorias))
        relatorio_final_md.append("\n---\n")

        # --- Relatório 5: Matrículas por Mês ---
        logging.info("Gerando relatório: Matrículas por Mês...") 
        df_matriculas_mes: pd.DataFrame = pd.read_sql_query(SQL_MATRICULAS_POR_MES, conn)
        relatorio_final_md.append(analisar_matriculas_por_mes(df_matriculas_mes))
        relatorio_final_md.append("\n---\n")

    except psycopg2.Error as e:
        logging.error(f"\n--- ERRO DE BANCO DE DADOS ---") 
        logging.error(f"ERRO: {e}") 
        return
    except Exception as e:
        logging.error(f"\n--- ERRO INESPERADO ---") 
        logging.error(f"ERRO: {e}") 
        return
    finally:
        if conn:
            conn.close()
            logging.info("\nConexão com o banco de dados fechada.") 

    # --- Salvar o relatório final em um arquivo ---
    nome_arquivo_saida: str = "relatorio_edutech.md"
    pasta_saida: Path = Path("relatorios")
    pasta_saida.mkdir(exist_ok=True)
    caminho_arquivo: Path = pasta_saida / nome_arquivo_saida
    
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write("\n".join(relatorio_final_md))
            
        logging.info(f"\n✅ Relatório completo salvo em: {caminho_arquivo}") 
    except IOError as e:
        logging.error(f"--- ERRO AO SALVAR ARQUIVO ---") 
        logging.error(f"Não foi possível salvar o relatório em {caminho_arquivo}: {e}") 


if __name__ == "__main__":
    main()