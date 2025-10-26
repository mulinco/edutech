import random
from faker import Faker
from datetime import datetime
import psycopg2 
import psycopg2.extras
from tqdm import tqdm
import logging
import argparse
from pathlib import Path
from db_utils import get_db_connection


LOG_DIR = Path("logs") # Define o nome da pasta
LOG_DIR.mkdir(exist_ok=True) # Cria a pasta (não dá erro se ela já existir)

logging.basicConfig(level=logging.INFO, 
                    filename=LOG_DIR / 'fluxo2_geracao.log', 
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s')

fake = Faker('pt_BR')

# --- DEFINIÇÃO DAS OPÇÕES DE ENUM 
OPCOES_GENERO = ['Masculino', 'Feminino', 'Não Binário', 'Outros', 'Prefiro Não Informar']
OPCOES_FONTE_CONHECIMENTO = ['Redes Sociais', 'Anúncio Google', 'Indicação de amigos', 'Youtube', 'Outro']
OPCOES_NIVEL_CURSO = ['iniciante', 'intermediario', 'avancado']
OPCOES_TIPO_AULA = ['video', 'texto', 'quiz']
OPCOES_STATUS_MATRICULA = ['ativa', 'concluida', 'cancelada', 'pendente']
OPCOES_METODO_PAGAMENTO = ['Cartão de Crédito', 'Pix', 'Boleto']
OPCOES_STATUS_PAGAMENTO = ['Pendente', 'Aprovado', 'Recusado', 'Estornado']


# --- FUNÇÃO 1: O "RESET" COMPLETO ---
def recriar_schema_completo(conn):
    """APAGA TUDO e recria a estrutura completa do banco de dados a partir do zero."""
    logging.info("\n--- 1. LIMPANDO E RECRIANDO O SCHEMA DO BANCO DE DADOS ---")
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DROP TABLE IF EXISTS aluno, instrutor, categoria, especialidade, curso, modulo, aula, matricula, pagamento, progresso_aula, avaliacoes, instrutor_especialidade CASCADE;
                DROP TYPE IF EXISTS tipo_fonte_conhecimento, tipo_nivel_curso, tipo_aula, tipo_status_matricula, tipo_metodo_pagamento, tipo_status_pagamento, tipo_genero CASCADE;
            """)
            logging.info("-> Estruturas antigas (tabelas e tipos) removidas.")
            
            cursor.execute("""
                CREATE TYPE tipo_fonte_conhecimento AS ENUM ('Redes Sociais', 'Anúncio Google', 'Indicação de amigos', 'Youtube', 'Outro');
                CREATE TYPE tipo_nivel_curso AS ENUM ('iniciante', 'intermediario', 'avancado');
                CREATE TYPE tipo_aula AS ENUM ('video', 'texto', 'quiz');
                CREATE TYPE tipo_status_matricula AS ENUM ('ativa', 'concluida', 'cancelada', 'pendente');
                CREATE TYPE tipo_metodo_pagamento AS ENUM ('Cartão de Crédito', 'Pix', 'Boleto');
                CREATE TYPE tipo_status_pagamento AS ENUM ('Pendente', 'Aprovado', 'Recusado', 'Estornado');
                CREATE TYPE tipo_genero AS ENUM ('Masculino', 'Feminino', 'Não Binário', 'Outros', 'Prefiro Não Informar');
                CREATE TABLE categoria ( id SERIAL PRIMARY KEY, nome VARCHAR(100) NOT NULL UNIQUE, descricao TEXT );
                CREATE TABLE especialidade ( id SERIAL PRIMARY KEY, nome VARCHAR(100) NOT NULL UNIQUE );
                CREATE TABLE aluno ( id SERIAL PRIMARY KEY, nome VARCHAR(100) NOT NULL, email VARCHAR(60) NOT NULL UNIQUE, genero tipo_genero, data_nascimento DATE, data_cadastro TIMESTAMPTZ NOT NULL DEFAULT NOW(), como_nos_conheceu tipo_fonte_conhecimento );
                CREATE TABLE instrutor ( id SERIAL PRIMARY KEY, nome VARCHAR(100) NOT NULL, email VARCHAR(60) NOT NULL UNIQUE, genero tipo_genero, data_nascimento DATE, data_cadastro TIMESTAMPTZ NOT NULL DEFAULT NOW(), biografia TEXT );
                CREATE TABLE curso ( id SERIAL PRIMARY KEY, titulo VARCHAR(200) NOT NULL, descricao TEXT, categoria_id INT NOT NULL REFERENCES categoria(id), instrutor_id INT NOT NULL REFERENCES instrutor(id), preco NUMERIC(10, 2) NOT NULL CHECK (preco >= 0), carga_horaria INT NOT NULL CHECK (carga_horaria > 0), nivel tipo_nivel_curso NOT NULL, data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW() );
                CREATE TABLE modulo ( id SERIAL PRIMARY KEY, curso_id INT NOT NULL REFERENCES curso(id), titulo VARCHAR(200) NOT NULL, ordem INT NOT NULL CHECK (ordem > 0), descricao TEXT );
                CREATE TABLE aula ( id SERIAL PRIMARY KEY, modulo_id INT NOT NULL REFERENCES modulo(id), titulo VARCHAR(200) NOT NULL, ordem INT NOT NULL CHECK (ordem > 0), duracao_minutos INT CHECK (duracao_minutos > 0), tipo tipo_aula NOT NULL );
                CREATE TABLE matricula ( id SERIAL PRIMARY KEY, aluno_id INT NOT NULL REFERENCES aluno(id), curso_id INT NOT NULL REFERENCES curso(id), data_matricula DATE NOT NULL DEFAULT CURRENT_DATE, data_conclusao DATE, status tipo_status_matricula NOT NULL, UNIQUE (aluno_id, curso_id) );
                CREATE TABLE progresso_aula ( id SERIAL PRIMARY KEY, matricula_id INT NOT NULL REFERENCES matricula(id), aula_id INT NOT NULL REFERENCES aula(id), concluida BOOLEAN NOT NULL DEFAULT FALSE, data_conclusao TIMESTAMPTZ, tempo_assistido_minutos INT, UNIQUE (matricula_id, aula_id) );
                CREATE TABLE pagamento ( id SERIAL PRIMARY KEY, matricula_id INT NOT NULL REFERENCES matricula(id), valor NUMERIC(10, 2) NOT NULL CHECK (valor >= 0), data_pagamento TIMESTAMPTZ NOT NULL DEFAULT NOW(), metodo_pagamento tipo_metodo_pagamento NOT NULL, status_pagamento tipo_status_pagamento NOT NULL );
                CREATE TABLE avaliacoes ( id SERIAL PRIMARY KEY, matricula_id INT NOT NULL REFERENCES matricula(id), curso_id INT NOT NULL REFERENCES curso(id), nota INT NOT NULL CHECK (nota >= 1 AND nota <= 5), comentario TEXT, data_avaliacao TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE (matricula_id, curso_id) );
                CREATE TABLE instrutor_especialidade ( instrutor_id INT NOT NULL REFERENCES instrutor(id), especialidade_id INT NOT NULL REFERENCES especialidade(id), PRIMARY KEY (instrutor_id, especialidade_id) );
            """)
            conn.commit()
        logging.info("-> Schema do banco de dados recriado com sucesso.")
    except psycopg2.Error as e:
        logging.info(f"\n--- ERRO NA CRIAÇÃO DO SCHEMA ---")
        logging.error(e)
        conn.rollback()
        raise e

#  A FUNÇÃO DE INSERÇÃO DE DADOS
def popular_banco(conn, QTD_ALUNOS, QTD_INSTRUTORES, QTD_CURSOS, QTD_MATRICULAS):
    """Gera e insere todos os dados fakes diretamente no banco."""
    logging.info("\n--- 2. INICIANDO POVOAMENTO DO BANCO DE DADOS ---")
    
    
    try:
        with conn.cursor() as cursor:
            # Popula e busca IDs de tabelas base
            cursor.execute("""
                INSERT INTO categoria (nome) VALUES ('Desenvolvimento Web'), ('Ciência de Dados'), ('Inteligência Artificial'), ('Cloud Computing'), ('Design & UX/UI'), ('Gestão de Projetos'), ('Segurança da Informação') RETURNING id;
            """)
            categoria_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("""
                INSERT INTO especialidade (nome) VALUES
                ('Desenvolvimento Back-End'), ('Desenvolvimento Front-End'), ('Ciência de Dados'), ('Inteligência Artificial'), ('Banco de Dados SQL'), ('Engenharia de Dados'),
                ('Business Intelligence'), ('Cloud AWS'), ('Cloud Azure'), ('DevOps'), ('Docker & Kubernetes'), ('Segurança da Informação'), ('Desenvolvimento Mobile'),
                ('React.js'), ('Angular'), ('Node.js'), ('JavaScript'), ('Metodologias Ágeis'), ('Python'), ('Java'), ('C#'), ('TypeScript'), ('PHP'), ('Go (Golang)'),
                ('Rust'), ('Kotlin'), ('Swift'), ('Ruby'), ('SQL'), ('HTML/CSS') 
                RETURNING id;
            """)
            especialidade_ids = [row[0] for row in cursor.fetchall()]
            logging.info("-> Tabelas de apoio (categoria, especialidade) populadas.")

            # Gerar e inserir Alunos
            alunos_data = []
            for _ in tqdm(range(QTD_ALUNOS), desc="Gerando Alunos"):
                genero = random.choice(OPCOES_GENERO)
                nome = fake.name_male() if genero == 'Masculino' else (fake.name_female() if genero == 'Feminino' else fake.name())
                alunos_data.append((nome, f"{nome.lower().replace(' ','.')}{random.randint(10,99)}@example.com", genero, fake.date_of_birth(minimum_age=16), fake.past_datetime(start_date='-2y'), random.choice(OPCOES_FONTE_CONHECIMENTO)))
            
            
            query_aluno = "INSERT INTO aluno (nome, email, genero, data_nascimento, data_cadastro, como_nos_conheceu) VALUES %s RETURNING id;"
            aluno_ids = inserir_dados(conn, query_aluno, alunos_data)
            logging.info(f"-> Inserido {len(aluno_ids)} alunos.")

            #Gerar e inserir Instrutores
            instrutores_data = []
            for _ in tqdm(range(QTD_INSTRUTORES), desc="Gerando Instrutores"):
                genero = random.choice(OPCOES_GENERO)
                nome = fake.name_male() if genero == 'Masculino' else (fake.name_female() if genero == 'Feminino' else fake.name())
                instrutores_data.append((nome, f"{nome.lower().replace(' ','.')}{random.randint(10,99)}@example.com", genero, fake.date_of_birth(minimum_age=25), fake.past_datetime(start_date='-2y'), fake.paragraph(nb_sentences=2)))
            
            
            query_instrutor = "INSERT INTO instrutor (nome, email, genero, data_nascimento, data_cadastro, biografia) VALUES %s RETURNING id;"
            instrutor_ids = inserir_dados(conn, query_instrutor, instrutores_data)
            logging.info(f"-> Inserido {len(instrutor_ids)} instrutores.")

            #Gerar e inserir Especialidades dos Instrutores
            instrutor_espec_data = []
            pares_unicos_espec = set()
            for instrutor_id in instrutor_ids:
                num_especialidades = random.randint(1, 3)
                especialidades_sorteadas = random.sample(especialidade_ids, num_especialidades)
                for especialidade_id in especialidades_sorteadas:
                    if (instrutor_id, especialidade_id) not in pares_unicos_espec:
                        instrutor_espec_data.append((instrutor_id, especialidade_id))
                        pares_unicos_espec.add((instrutor_id, especialidade_id))
            
            
            query_instrutor_espec = "INSERT INTO instrutor_especialidade (instrutor_id, especialidade_id) VALUES %s;"
            inserir_dados(conn, query_instrutor_espec, instrutor_espec_data)
            logging.info(f"-> Inserido {len(instrutor_espec_data)} associações de especialidade.")

            #Gerar e inserir Cursos
            cursos_data = []
            for _ in tqdm(range(QTD_CURSOS), desc="Gerando Cursos"):
                cursos_data.append((fake.bs().title(), fake.paragraph(nb_sentences=4), random.choice(categoria_ids), random.choice(instrutor_ids), round(random.uniform(49.90, 499.90), 2), random.randint(10, 120), random.choice(OPCOES_NIVEL_CURSO), fake.past_datetime(start_date='-2y')))
            
            
            query_curso = "INSERT INTO curso (titulo, descricao, categoria_id, instrutor_id, preco, carga_horaria, nivel, data_criacao) VALUES %s RETURNING id, preco;"
            cursos_com_precos = inserir_dados(conn, query_curso, cursos_data, fetch_multiple=True)
            curso_ids = [c[0] for c in cursos_com_precos]
            logging.info(f"-> Inserido {len(curso_ids)} cursos.")

            #Gerar e inserir Módulos e Aulas
            modulos_data = []
            query_modulo = "INSERT INTO modulo (curso_id, titulo, ordem, descricao) VALUES %s RETURNING id, curso_id;"
            for curso_id in curso_ids:
                for i in range(random.randint(3, 8)):
                    modulos_data.append((curso_id, f"Módulo {i + 1}: {fake.sentence(nb_words=3).replace('.', '')}", i + 1, fake.sentence(nb_words=10)))
            modulo_ids_com_curso_id = inserir_dados(conn, query_modulo, modulos_data, fetch_multiple=True)
            logging.info(f"-> Inserido {len(modulo_ids_com_curso_id)} módulos.")

            aulas_data = []
            query_aula = "INSERT INTO aula (modulo_id, titulo, ordem, duracao_minutos, tipo) VALUES %s RETURNING id, modulo_id;"
            mapa_modulo_para_curso = dict(modulo_ids_com_curso_id)
            for modulo_id, curso_id_do_modulo in tqdm(modulo_ids_com_curso_id, desc="Gerando Aulas"):
                for j in range(random.randint(5, 15)):
                    aulas_data.append((modulo_id, f"Aula {j + 1}: {fake.sentence(nb_words=5).replace('.', '')}", j + 1, random.randint(5, 45), random.choice(OPCOES_TIPO_AULA)))
            aulas_inseridas = inserir_dados(conn, query_aula, aulas_data, fetch_multiple=True)
            aulas_com_ids = [(aula_id, mod_id, mapa_modulo_para_curso.get(mod_id)) for aula_id, mod_id in aulas_inseridas]
            logging.info(f"-> Inserido {len(aulas_com_ids)} aulas.")
            
        #Gerar e inserir Matrículas
        matriculas_data, pares_unicos = [], set()
        
        # Loop 'while' original para gerar os dados
        while len(matriculas_data) < QTD_MATRICULAS:
            aluno_id, curso_id = random.choice(aluno_ids), random.choice(curso_ids)
            if (aluno_id, curso_id) in pares_unicos: 
                continue # Pula se o par já existir
            
            pares_unicos.add((aluno_id, curso_id))
            status = random.choice(OPCOES_STATUS_MATRICULA)
            
            # Linhas originais do Faker (a causa provável do travamento)
            data_matricula = fake.past_date(start_date='-2y')
            data_conclusao = fake.date_between(start_date=data_matricula) if status == 'concluida' else None
            
            matriculas_data.append((aluno_id, curso_id, data_matricula, data_conclusao, status))
        
        # Inserção no banco (ocorre *após* o loop while terminar)
        query_matricula = "INSERT INTO matricula (aluno_id, curso_id, data_matricula, data_conclusao, status) VALUES %s RETURNING id, aluno_id, curso_id, status;"
        matriculas_com_ids = inserir_dados(conn, query_matricula, matriculas_data, fetch_multiple=True)
        logging.info(f"-> Inserido {len(matriculas_com_ids)} matrículas.")
            
            #Gerar e inserir Ações Pós-Matrícula
        pagamentos, progressos, avaliacoes = [], [], []
        precos_por_curso = {curso[0]: curso[1] for curso in cursos_com_precos}
        aulas_por_curso = {}
        for aula_id, modulo_id, curso_id in aulas_com_ids:
                if not curso_id: continue # Pula aulas onde o curso_id não foi encontrado
                if curso_id not in aulas_por_curso: aulas_por_curso[curso_id] = []
                aulas_por_curso[curso_id].append(aula_id)
            
        for matricula_id, aluno_id, curso_id, status in tqdm(matriculas_com_ids, desc="Gerando Ações Pós-Matrícula"):
                preco_real = precos_por_curso.get(curso_id, round(random.uniform(49.90, 499.90), 2))
                pagamentos.append((matricula_id, preco_real, fake.past_datetime(start_date='-1y'), random.choice(OPCOES_METODO_PAGAMENTO), random.choice(OPCOES_STATUS_PAGAMENTO)))
                
                if status != 'cancelada':
                    aulas_do_curso = aulas_por_curso.get(curso_id, [])
                    if aulas_do_curso:
                        aulas_para_progresso = random.sample(aulas_do_curso, random.randint(0, len(aulas_do_curso)))
                        for aula_id in aulas_para_progresso:
                            foi_concluida = random.random() < 0.8
                            data_conclusao_aula = fake.past_datetime(start_date='-1y') if foi_concluida else None
                            progressos.append((matricula_id, aula_id, foi_concluida, data_conclusao_aula, random.randint(5, 60)))
                
                if status == 'concluida' and random.random() < 0.5:
                    avaliacoes.append((matricula_id, curso_id, random.randint(3, 5), fake.paragraph(nb_sentences=2), fake.past_datetime(start_date='-1y')))
            
        query_pagamento = "INSERT INTO pagamento (matricula_id, valor, data_pagamento, metodo_pagamento, status_pagamento) VALUES %s;"
        query_progresso = "INSERT INTO progresso_aula (matricula_id, aula_id, concluida, data_conclusao, tempo_assistido_minutos) VALUES %s;"
        query_avaliacao = "INSERT INTO avaliacoes (matricula_id, curso_id, nota, comentario, data_avaliacao) VALUES %s;"
            
        if pagamentos: inserir_dados(conn, query_pagamento, pagamentos)
        if progressos: inserir_dados(conn, query_progresso, progressos)
        if avaliacoes: inserir_dados(conn, query_avaliacao, avaliacoes)
        logging.info(f"-> Inserido {len(pagamentos)} pagamentos, {len(progressos)} progressos, e {len(avaliacoes)} avaliações.")

        conn.commit()
        logging.info("\n--- POVOAMENTO COMPLETO CONCLUÍDO! ---")
    except psycopg2.Error as e:
        logging.info(f"\n--- ERRO DURANTE O POVOAMENTO ---")
        logging.error(e)
        conn.rollback()
        raise e

def inserir_dados(conn, query, data, fetch_multiple=False):
    """
    Executa uma query de inserção em massa (bulk insert) para múltiplos registros
    e retorna os resultados da cláusula RETURNING.
    """
    if not data: 
        logging.info(" -> Aviso: Nenhuma data para inserir, pulando.")
        return []
    
    with conn.cursor() as cursor:
        try:
            # psycopg2.extras.execute_values é a ferramenta CORRETA para bulk insert com 'VALUES %s'.
            psycopg2.extras.execute_values(cursor, query, data, template=None, page_size=100)
            
            # Se a query não tiver RETURNING, não tentamos buscar resultados
            if "RETURNING" not in query.upper():
                return []
            
            resultados = cursor.fetchall()
            
            if fetch_multiple:
                return resultados # Retorna a lista de tuples completos
            else:
                return [item[0] for item in resultados] # Retorna apenas a primeira coluna (o ID)
        except psycopg2.Error as e:
            logging.info(f"\n--- ERRO AO EXECUTAR QUERY ---")
            logging.info(f"Query: {cursor.query}")
            logging.error(f"Erro: {e}")
            raise e



    
def main():
    #É uma forma de receber parâmetros externos (do terminal) para que o script seja flexível e reutilizável, evitando a necessidade de "dar manutenção" só para mudar um valor.
    parser = argparse.ArgumentParser(description="Popula o banco Edutech com dados fictícios.")
    parser.add_argument("--alunos", type=int, default=100, help="Número de alunos a gerar.")
    parser.add_argument("--instrutores", type=int, default=25, help="Número de instrutores a gerar.")
    parser.add_argument("--cursos", type=int, default=50, help="Número de cursos a gerar.")
    parser.add_argument("--matriculas", type=int, default=200, help="Número de matrículas a gerar.")
    args = parser.parse_args()

    conn = None # Define 'conn' com o tipo importado
    try:
        logging.info("Conectando ao banco de dados PostgreSQL...")
        
        # 1. Pede a conexão para o módulo utilitário
        conn = get_db_connection()

        # 2. Verifica se a conexão falhou
        if conn is None:
            logging.error("Não foi possível conectar ao banco. Abortando.")
            return # Sai da função main
        
        # 3. Define o autocommit (Lógica específica deste script)
        conn.autocommit = False 
        # O log de "sucesso" já é feito pelo get_db_connection()
        
        # 4. Executa as funções 
        recriar_schema_completo(conn)
        popular_banco(conn, args.alunos, args.instrutores, args.cursos, args.matriculas)

    except psycopg2.Error as e:
        logging.info(f"\n--- ERRO FATAL DE BANCO DE DADOS ---")
    except Exception as e:
        logging.info(f"\n--- ERRO INESPERADO NO SCRIPT PYTHON ---")
        logging.error(f"ERRO: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("\nConexão com o banco de dados fechada.")

# --- PONTO DE PARTIDA DO SCRIPT ---
if __name__ == "__main__":
    main()