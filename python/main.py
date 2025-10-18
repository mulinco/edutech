from pathlib import Path
import sys
import pandas as pd
from gerador_dados import main as gerar_dados_main
from validador_csv import main as validar_csv_main

def limpar_csvs_para_importacao(nome_pasta="data"):
    print("\n--- 3. LIMPANDO ARQUIVOS CSV PARA IMPORTAÇÃO NO POSTGRESQL ---")
    pasta_data = Path(nome_pasta)
    if not pasta_data.exists(): return
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
                print(f" -> Colunas {colunas_a_remover} removidas de '{caminho_arquivo.name}'.")
        except Exception as e:
            print(f"Erro ao limpar o arquivo {caminho_arquivo.name}: {e}")

if __name__ == "__main__":
    print("--- 1. INICIANDO GERAÇÃO DOS ARQUIVOS CSV (COM ID TEMPORÁRIO) ---")
    gerar_dados_main()
    
    print("\n--- 2. INICIANDO VALIDAÇÃO DOS ARQUIVOS CSV ---")
    erros_validacao = validar_csv_main()
    
    if erros_validacao:
        print("\n\n--- ❌ VALIDAÇÃO FALHOU! ---")
        for erro in erros_validacao: print(f"- {erro}")
        print("\nCorrija os erros e tente novamente.")
        sys.exit(1)
    else:
        print("\n--- ✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO! ---")
        limpar_csvs_para_importacao()

    print("\n--- PROCESSO CONCLUÍDO! ---")
    print("Sua pasta 'data' contém os arquivos CSV limpos e prontos para importar no PostgreSQL.")