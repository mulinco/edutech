from pathlib import Path
import sys
import pandas as pd
import logging
import argparse

try:
    from gerador_dados import main as gerar_dados_main
    from validador_csv import main as validar_csv_main
except ModuleNotFoundError:
    print("ERRO: Certifique-se de que 'gerador_dados.py' e 'validador_csv.py' estão na mesma pasta que 'main.py'")
    sys.exit(1)

LOG_DIR = Path("logs") # nome da pasta para armazenamento dos logs
LOG_DIR.mkdir(exist_ok=True) # cria a pasta (e não dá erro se ela existir)

logging.basicConfig(level=logging.INFO, 
                    filename=LOG_DIR / 'fluxo1_geracao.log', 
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')


def limpar_csvs_para_importacao(nome_pasta="data"):
    logging.info("\n--- 3. LIMPANDO ARQUIVOS CSV PARA IMPORTAÇÃO NO POSTGRESQL ---")
    pasta_data = Path(nome_pasta)
    if not pasta_data.exists():
        logging.warning(f"Pasta '{nome_pasta}' não encontrada, pulando limpeza.")
        return
    for caminho_arquivo in pasta_data.glob("*.csv"):
        try:
            df = pd.read_csv(caminho_arquivo)
            colunas_a_remover = []
            if 'id' in df.columns and '_especialidade' not in caminho_arquivo.name:
                colunas_a_remover.append('id')
            if caminho_arquivo.name == 'aula.csv' and 'curso_id' in df.columns:
                colunas_a_remover.append('curso_id')
            if colunas_a_remover:
                df = df.drop(columns=colunas_a_remover)
                df.to_csv(caminho_arquivo, index=False, encoding='utf-8')
                logging.info(f" -> Colunas {colunas_a_remover} removidas de '{caminho_arquivo.name}'.")
        except Exception as e:
            logging.error(f"Erro ao limpar o arquivo {caminho_arquivo.name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fluxo 1: Gerar e Validar CSVs.")
    parser.add_argument("--alunos", type=int, default=100, help="Número de alunos a gerar.")
    parser.add_argument("--instrutores", type=int, default=25, help="Número de instrutores a gerar.")
    parser.add_argument("--cursos", type=int, default=50, help="Número de cursos a gerar.")
    parser.add_argument("--matriculas", type=int, default=200, help="Número de matrículas a gerar.")
    args = parser.parse_args()

    logging.info("--- 1. INICIANDO GERAÇÃO DOS ARQUIVOS CSV (COM ID TEMPORÁRIO) ---")
    gerar_dados_main(args)
    
    logging.info("\n--- 2. INICIANDO VALIDAÇÃO DOS ARQUIVOS CSV ---")
    erros_validacao = validar_csv_main()
    
    if erros_validacao:
        logging.error("\n\n--- ❌ VALIDAÇÃO FALHOU! ❌---")
        for erro in erros_validacao: print(f"- {erro}")
        logging.error("\nCorrija os erros e tente novamente.")
        sys.exit(1)
    else:
        logging.info("\n--- ✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO! ✅---")
        limpar_csvs_para_importacao()

    logging.info("\n--- PROCESSO CONCLUÍDO! ---")
    logging.info("Sua pasta 'data' contém os arquivos CSV limpos e prontos para importar no PostgreSQL.")