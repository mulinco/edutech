import pandas as pd
from pathlib import Path
from utils import validar_email

def validar_csv(caminho_arquivo, colunas_obrigatorias, ids_existentes=None):
    erros = []
    nome_arquivo = caminho_arquivo.name
    try:
        df = pd.read_csv(caminho_arquivo)
    except FileNotFoundError:
        return [f"Arquivo não encontrado: {caminho_arquivo}"]
    
    for coluna in colunas_obrigatorias:
        if df[coluna].isnull().any():
            linhas_com_erro = df[df[coluna].isnull()].index.tolist()
            erros.append(f"[{nome_arquivo}] Erro: A coluna '{coluna}' tem valores nulos nas linhas: {[i+2 for i in linhas_com_erro]}.")
    
    if 'id' in df.columns and df['id'].duplicated().any():
        erros.append(f"[{nome_arquivo}] Erro: IDs duplicados encontrados.")
        
    for index, linha in df.iterrows():
        linha_num = index + 2
        if 'email' in df.columns and not validar_email(linha['email']):
            erros.append(f"[{nome_arquivo}] Linha {linha_num}: Email '{linha['email']}' inválido.")
        if 'nota' in df.columns and not (1 <= linha['nota'] <= 5):
            erros.append(f"[{nome_arquivo}] Linha {linha_num}: Nota '{linha['nota']}' fora do range (1-5).")
        if ids_existentes:
            for coluna_fk, ids_validos in ids_existentes.items():
                if coluna_fk in df.columns:
                    valor_fk = linha[coluna_fk]
                    if pd.notna(valor_fk) and int(valor_fk) not in ids_validos:
                        erros.append(f"[{nome_arquivo}] Linha {linha_num}: ID '{int(valor_fk)}' na coluna '{coluna_fk}' não existe na tabela de referência.")
    return erros

def main():
    pasta_data = Path("data")
    relatorio_final = []
    print("\nCarregando IDs de referência...")
    try:
        ids_alunos = set(pd.read_csv(pasta_data / "aluno.csv")['id'])
        ids_instrutores = set(pd.read_csv(pasta_data / "instrutor.csv")['id'])
        ids_cursos = set(pd.read_csv(pasta_data / "curso.csv")['id'])
        ids_aulas = set(pd.read_csv(pasta_data / "aula.csv")['id'])
        ids_matriculas = set(pd.read_csv(pasta_data / "matricula.csv")['id'])
        print("IDs carregados com sucesso.")
    except (FileNotFoundError, KeyError) as e:
        print(f"Erro crítico ao carregar IDs: {e}. Verifique se o 'gerador_dados.py' foi executado corretamente.")
        return [str(e)]
        
    regras = {
        "aluno.csv": {"colunas_obrigatorias": ['id', 'nome', 'email'], "ids_existentes": {}},
        "curso.csv": {"colunas_obrigatorias": ['id', 'titulo', 'instrutor_id'], "ids_existentes": {"instrutor_id": ids_instrutores}},
        "matricula.csv": {"colunas_obrigatorias": ['id', 'aluno_id', 'curso_id'], "ids_existentes": {"aluno_id": ids_alunos, "curso_id": ids_cursos}},
        "avaliacoes.csv": {"colunas_obrigatorias": ['id', 'matricula_id', 'curso_id', 'nota'], "ids_existentes": {"matricula_id": ids_matriculas, "curso_id": ids_cursos}},
    }
    for arquivo, regras_arquivo in regras.items():
        print(f"Validando arquivo: {arquivo}...")
        erros = validar_csv(pasta_data / arquivo, regras_arquivo['colunas_obrigatorias'], regras_arquivo['ids_existentes'])
        if erros: relatorio_final.extend(erros)
        else: print(f" -> {arquivo} está VÁLIDO.")
    return relatorio_final

if __name__ == "__main__":
    erros = main()
    if erros:
        print("\n\n--- ❌ RELATÓRIO DE ERROS DE VALIDAÇÃO ---")
        for erro in erros: print(erro)
    else:
        print("\n\n--- ✅ SUCESSO! Todos os arquivos foram validados. ---")