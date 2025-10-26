import random
from faker import Faker
import pandas as pd
from pathlib import Path 
from utils import padronizar_data, criar_email_do_nome
import logging 
from tqdm import tqdm
import argparse
from typing import List, Dict, Any, Set, Tuple

#CONFIGURAÇÃO INICIAL
fake: Faker = Faker('pt_BR')
IDS_CATEGORIAS: List[int] = list(range(1, 8))
IDS_ESPECIALIDADES: List[int] = list(range(1, 30))

#FUNÇÕES DE GERAÇÃO
def gerar_alunos(quantidade: int) -> List[Dict[str, Any]]:
    logging.info(f"-> Gerando {quantidade} alunos...")
    alunos: List[Dict[str, Any]] = []
    opcoes_genero: List[str] = ['Masculino', 'Feminino', 'Não Binário']
    opcoes_fonte: List[str] = ['Redes Sociais', 'Anúncio Google', 'Indicação de amigos', 'Youtube', 'Outro']
    for i in tqdm(range(quantidade), desc= "Gerando Alunos"):
        genero_escolhido: str = random.choice(opcoes_genero)
        if genero_escolhido == 'Masculino': nome_gerado = fake.name_male()
        elif genero_escolhido == 'Feminino': nome_gerado = fake.name_female()
        else: nome_gerado = fake.name()
        email_gerado: str = criar_email_do_nome(nome_gerado)
        alunos.append({
            'id': i + 1, 'nome': nome_gerado, 'email': email_gerado, 'genero': genero_escolhido,
            'data_nascimento': padronizar_data(fake.date_of_birth(minimum_age=16, maximum_age=70)),
            'data_cadastro': padronizar_data(fake.past_datetime(start_date='-2y')),
            'como_nos_conheceu': random.choice(opcoes_fonte)
        })
    return alunos

def gerar_instrutores(quantidade: int) -> Dict[str, List[Dict[str, Any]]]:
    logging.info(f"-> Gerando {quantidade} instrutores...")
    instrutores: List[Dict[str, Any]] = []
    instrutor_especialidades: List[Dict[str, Any]] = []
    opcoes_genero: List[str] = ['Masculino', 'Feminino', 'Não Binário']
    for i in tqdm(range(quantidade), desc= "Gerando Instrutores"):
        genero_escolhido: str = random.choice(opcoes_genero)
        if genero_escolhido == 'Masculino': nome_gerado = fake.name_male()
        elif genero_escolhido == 'Feminino': nome_gerado = fake.name_female()
        else: nome_gerado = fake.name()
        email_gerado = criar_email_do_nome(nome_gerado)
        instrutor_id = i + 1
        instrutores.append({
            'id': instrutor_id, 'nome': nome_gerado, 'email': email_gerado, 'genero': genero_escolhido,
            'data_nascimento': padronizar_data(fake.date_of_birth(minimum_age=25, maximum_age=65)),
            'data_cadastro': padronizar_data(fake.past_datetime(start_date='-2y')),
            'biografia': fake.paragraph(nb_sentences=3)
        })
        num_especialidades: int = random.randint(1, 5)
        especialidades_sorteadas: List[int] = random.sample(IDS_ESPECIALIDADES, num_especialidades)
        for especialidade_id in especialidades_sorteadas:
            instrutor_especialidades.append({'instrutor_id': instrutor_id, 'especialidade_id': especialidade_id})
    return {"instrutores": instrutores, "instrutor_especialidades": instrutor_especialidades}

def gerar_cursos(quantidade, instrutor_ids):
    logging.info(f"-> Gerando {quantidade} cursos...")
    cursos: List[Dict[str, Any]] = []
    opcoes_nivel: List[str] = ['iniciante', 'intermediario', 'avancado']
    for i in tqdm(range(quantidade), desc= "Gerando Cursos"):
        cursos.append({
            'id': i + 1, 'titulo': fake.bs().title(), 'descricao': fake.paragraph(nb_sentences=4),
            'categoria_id': random.choice(IDS_CATEGORIAS), 'instrutor_id': random.choice(instrutor_ids),
            'preco': round(random.uniform(49.90, 499.90), 2), 'carga_horaria': random.randint(10, 120),
            'nivel': random.choice(opcoes_nivel), 'data_criacao': padronizar_data(fake.past_datetime(start_date='-2y'))
        })
    return cursos

def gerar_modulos_e_aulas(curso_ids: List[int]) -> Dict[str, List[Dict[str, Any]]]:
    logging.info(f"-> Gerando módulos e aulas para {len(curso_ids)} cursos...")
    modulos: List[Dict[str, Any]] = []
    aulas: List[Dict[str, Any]] = []
    modulo_id_counter: int = 1
    aula_id_counter: int = 1
    for curso_id in tqdm(curso_ids, desc= "Gerando Módulos/Aulas"):
        num_modulos = random.randint(3, 8)
        for i in range(num_modulos):
            modulos.append({
                'id': modulo_id_counter, 'curso_id': curso_id, 'titulo': f"Módulo {i + 1}: {fake.sentence(nb_words=3).replace('.', '')}",
                'ordem': i + 1, 'descricao': fake.sentence(nb_words=10)
            })
            num_aulas = random.randint(5, 15)
            for j in range(num_aulas):
                aulas.append({
                    'id': aula_id_counter, 'modulo_id': modulo_id_counter, 'curso_id': curso_id,
                    'titulo': f"Aula {j + 1}: {fake.sentence(nb_words=5).replace('.', '')}",
                    'ordem': j + 1, 'duracao_minutos': random.randint(5, 45), 'tipo': random.choice(['video', 'texto', 'quiz'])
                })
                aula_id_counter += 1
            modulo_id_counter += 1

    logging.info(f"-> {len(modulos)} módulos e {len(aulas)} aulas gerados.")        
    return {"modulos": modulos, "aulas": aulas}

def gerar_matriculas(quantidade: int, aluno_ids: List[int], curso_ids: List[int]) -> List[Dict[str, Any]]:
    logging.info(f"Iniciando geração de {quantidade} matrículas...")
    matriculas: List[Dict[str, Any]] = []
    pares_unicos: Set[Tuple[int, int]] = set() # um set de tuplas (aluno_id, curso_id)
    opcoes_status: List[str] = ['ativa', 'concluida', 'cancelada', 'pendente']
    
    while len(matriculas) < quantidade:
        aluno_id: int = random.choice(aluno_ids)
        curso_id: int = random.choice(curso_ids)
        if (aluno_id, curso_id) in pares_unicos: continue
        pares_unicos.add((aluno_id, curso_id))
        status: str = random.choice(opcoes_status)
        data_matricula = fake.past_date(start_date='-2y')
        data_conclusao = fake.date_between(start_date=data_matricula) if status == 'concluida' else None
        matriculas.append({
            'id': len(matriculas) + 1, 'aluno_id': aluno_id, 'curso_id': curso_id,
            'data_matricula': padronizar_data(data_matricula), 'data_conclusao': padronizar_data(data_conclusao), 'status': status
        })
            
    logging.info(f"-> {len(matriculas)} matrículas geradas.")    
    return matriculas

def gerar_acoes_pos_matricula(
    matriculas: List[Dict[str, Any]], 
    cursos: List[Dict[str, Any]], 
    df_aulas: pd.DataFrame
) -> Dict[str, List[Dict[str, Any]]]:
    
    logging.info(f"-> Gerando ações (pagamentos, etc.) para {len(matriculas)} matrículas...")
    pagamentos: List[Dict[str, Any]] = []
    progressos: List[Dict[str, Any]] = []
    avaliacoes: List[Dict[str, Any]] = []
    opcoes_metodo_pgto: List[str] = ['Cartão de Crédito', 'Pix', 'Boleto']
    opcoes_status_pgto: List[str] = ['Aprovado', 'Pendente', 'Recusado', 'Estornado']
    precos_por_curso: Dict[int, float] = {curso['id']: curso['preco'] for curso in cursos}
    aulas_por_curso: Dict[int, List[int]] = df_aulas.groupby('curso_id')['id'].apply(list).to_dict()
    for matricula in tqdm(matriculas, desc="Gerando Ações Pós-Matrícula"):
        preco_real = precos_por_curso.get(matricula['curso_id'], round(random.uniform(49.90, 499.90), 2))
        pagamentos.append({
            'id': matricula['id'], 'matricula_id': matricula['id'], 'valor': preco_real,
            'data_pagamento': padronizar_data(fake.past_datetime(start_date='-1y')),
            'metodo_pagamento': random.choice(opcoes_metodo_pgto), 'status_pagamento': random.choice(opcoes_status_pgto)
        })
        if matricula['status'] != 'cancelada':
            aulas_do_curso = aulas_por_curso.get(matricula['curso_id'], [])
            if aulas_do_curso:
                aulas_para_progresso = random.sample(aulas_do_curso, random.randint(0, len(aulas_do_curso)))
                for aula_id in aulas_para_progresso:
                    foi_concluida = random.random() < 0.8
                    data_conclusao_aula = padronizar_data(fake.past_datetime(start_date='-1y')) if foi_concluida else None
                    progressos.append({
                        'matricula_id': matricula['id'], 'aula_id': aula_id, 'concluida': foi_concluida,
                        'data_conclusao': data_conclusao_aula, 'tempo_assistido_minutos': random.randint(5, 60)
                    })
        if matricula['status'] == 'concluida' and random.random() < 0.5:
            avaliacoes.append({
                'id': len(avaliacoes) + 1, 'matricula_id': matricula['id'], 'curso_id': matricula['curso_id'],
                'nota': random.randint(3, 5), 'comentario': fake.paragraph(nb_sentences=2),
                'data_avaliacao': padronizar_data(fake.past_datetime(start_date='-1y'))
            })

    logging.info(f"-> {len(pagamentos)} pagamentos, {len(progressos)} progressos, e {len(avaliacoes)} avaliações gerados.")
    return {"pagamentos": pagamentos, "progresso_aula": progressos, "avaliacoes": avaliacoes}

def exportar_para_csv(dados_por_tabela: Dict[str, pd.DataFrame], nome_pasta: str = "data") -> None:
    logging.info(f"\nIniciando exportação para a pasta '{nome_pasta}'...")
    pasta_saida = Path(nome_pasta)
    pasta_saida.mkdir(exist_ok=True)
    for nome_tabela, df in dados_por_tabela.items():
        if df.empty: continue
        caminho_arquivo = pasta_saida / f"{nome_tabela}.csv"
        df.to_csv(caminho_arquivo, index=False, encoding='utf-8')
        logging.info(f" -> Arquivo '{caminho_arquivo}' gerado com sucesso ({len(df)} linhas).")

def main(args: argparse.Namespace) -> None:
    logging.info("--- INICIANDO GERAÇÃO DE DADOS CSV ---")
    logging.info(f"Configuração: {args.alunos} alunos, {args.instrutores} instrutores, {args.cursos} cursos, {args.matriculas} matrículas.")

    # USANDO ARGS
    alunos_brutos: List[Dict[str, Any]] = gerar_alunos(args.alunos)
    dados_instrutores: Dict[str, List[Dict[str, Any]]] = gerar_instrutores(args.instrutores)
    instrutor_ids: List[int] = [i['id'] for i in dados_instrutores['instrutores']]
    
    cursos_brutos: List[Dict[str, Any]] = gerar_cursos(args.cursos, instrutor_ids)
    curso_ids: List[int] = [c['id'] for c in cursos_brutos]
    
    dados_estrutura_curso: Dict[str, List[Dict[str, Any]]] = gerar_modulos_e_aulas(curso_ids)
    
    aluno_ids: List[int] = [a['id'] for a in alunos_brutos]
    
    matriculas_brutas: List[Dict[str, Any]] = gerar_matriculas(args.matriculas, aluno_ids, curso_ids)
    
    df_aulas_temp = pd.DataFrame(dados_estrutura_curso['aulas'])
    dados_pos_matricula: Dict[str, List[Dict[str, Any]]] = gerar_acoes_pos_matricula(matriculas_brutas, cursos_brutos, df_aulas_temp)
    
    dados_brutos_agrupados: Dict[str, List[Dict[str, Any]]] = {
        "aluno": alunos_brutos, "instrutor": dados_instrutores['instrutores'],
        "instrutor_especialidade": dados_instrutores['instrutor_especialidades'], "curso": cursos_brutos,
        "modulo": dados_estrutura_curso['modulos'], "aula": dados_estrutura_curso['aulas'],
        "matricula": matriculas_brutas, "pagamento": dados_pos_matricula['pagamentos'],
        "progresso_aula": dados_pos_matricula['progresso_aula'], "avaliacoes": dados_pos_matricula['avaliacoes']
    }
    
    dataframes_finais: Dict[str, pd.DataFrame] = {
        nome_tabela: pd.DataFrame(dados) for nome_tabela, dados in dados_brutos_agrupados.items() if dados
    }
    
    exportar_para_csv(dataframes_finais)
    logging.info("--- GERAÇÃO DE DADOS CSV CONCLUÍDA ---")

