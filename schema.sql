-- Primeiro, eu defini todos os meus tipos ENUM customizados. Decidi usar ENUMs em vez de
-- tabelas de consulta ou constraints CHECK para garantir a integridade dos dados e
-- otimizar o armazenamento, já que essas são listas de valores que raramente mudam.

CREATE TYPE tipo_fonte_conhecimento AS ENUM ('Redes Sociais', 'Anúncio Google', 'Indicação de amigos', 'Youtube', 'Outro');
CREATE TYPE tipo_nivel_curso AS ENUM ('iniciante', 'intermediario', 'avancado');
CREATE TYPE tipo_aula AS ENUM ('video', 'texto', 'quiz');
CREATE TYPE tipo_status_matricula AS ENUM ('ativa', 'concluida', 'cancelada', 'pendente');
CREATE TYPE tipo_metodo_pagamento AS ENUM ('Cartão de Crédito','Pix','Boleto');
CREATE TYPE tipo_status_pagamento AS ENUM ('Pendente','Aprovado','Recusado','Estornado');
CREATE TYPE tipo_genero AS ENUM ('Masculino', 'Feminino', 'Não Binário', 'Outros', 'Prefiro Não Informar');

-- Tabelas de Apoio e Referência

CREATE TABLE categoria(
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT
);

CREATE TABLE especialidade (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
);

-- Abaixo, eu implemento a arquitetura de Supertipo/Subtipo para os usuários.
-- A tabela 'pessoa' guarda os dados comuns a todos (nome, email, etc.). Escolhi essa
-- abordagem para evitar a duplicação de colunas e facilitar a adição de novos papéis no futuro.


-- Tabelas de Entidades Principais

CREATE TABLE aluno (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(60) NOT NULL UNIQUE,
    genero tipo_genero,
    data_nascimento DATE, 
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    como_nos_conheceu tipo_fonte_conhecimento
);

CREATE TABLE instrutor (
     id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(60) NOT NULL UNIQUE,
    genero tipo_genero,
    data_nascimento DATE, 
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    biografia TEXT
);

-- Tabelas Centrais do Sistema 

-- Tabela principal que armazena as informações de cada curso.
-- Aqui eu referencio as chaves estrangeiras e uso os meus tipos ENUM.
CREATE TABLE curso (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    categoria_id INT NOT NULL REFERENCES categoria(id),
    instrutor_id INT NOT NULL REFERENCES instrutor(id),
    preco NUMERIC(10, 2) NOT NULL CHECK (preco >= 0),
    carga_horaria INT NOT NULL CHECK (carga_horaria > 0),
    nivel tipo_nivel_curso NOT NULL,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE modulo (
    id SERIAL PRIMARY KEY,
    curso_id INT NOT NULL REFERENCES curso(id),
    titulo VARCHAR(200) NOT NULL,
    ordem INT NOT NULL CHECK (ordem > 0),
    descricao TEXT
);


CREATE TABLE aula (
    id SERIAL PRIMARY KEY,
    modulo_id INT NOT NULL REFERENCES modulo(id),
    titulo VARCHAR(200) NOT NULL,
    ordem INT NOT NULL CHECK (ordem > 0),
    duracao_minutos INT CHECK (duracao_minutos > 0),
    tipo tipo_aula NOT NULL
);



-- Tabelas de Ações e Detalhes 

-- 'matricula' é a tabela que conecta um aluno a um curso.
-- A constraint UNIQUE em (aluno_id, curso_id) garante que um aluno não possa se matricular duas vezes no mesmo curso.
CREATE TABLE matricula (
    id SERIAL PRIMARY KEY,
    aluno_id INT NOT NULL REFERENCES aluno(id),
    curso_id INT NOT NULL REFERENCES curso(id),
    data_matricula DATE NOT NULL DEFAULT CURRENT_DATE,
    data_conclusao DATE,
    status status_matricula NOT NULL,
    UNIQUE (aluno_id, curso_id)
);

CREATE TABLE progresso_aula (
    id SERIAL PRIMARY KEY,
    matricula_id INT NOT NULL REFERENCES matricula(id),
    aula_id INT NOT NULL REFERENCES aula(id),
    concluida BOOLEAN NOT NULL DEFAULT FALSE,
    data_conclusao TIMESTAMPTZ,
    tempo_assistido_minutos INT,
    UNIQUE (matricula_id, aula_id)
);

-- Separei os dados de pagamento em uma tabela própria para permitir, no futuro, o registro de múltiplos pagamentos por matrícula (como parcelas).
-- Optei por TIMESTAMPTZ e NOW() para 'data_pagamento', pois é a melhor prática para registrar timestamps, garantindo a consistência entre diferentes fusos horários.
CREATE TABLE pagamento (
    id SERIAL PRIMARY KEY,
    matricula_id INT NOT NULL REFERENCES matricula(id),
    valor NUMERIC(10, 2) NOT NULL CHECK (valor >= 0),
    data_pagamento TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metodo_pagamento tipo_metodo_pagamento NOT NULL,
    status_pagamento tipo_status_pagamento NOT NULL
);

CREATE TABLE avaliacoes (
	id SERIAL PRIMARY KEY,
	matricula_id INT NOT NULL REFERENCES matricula(id),
	curso_id INT NOT NULL REFERENCES curso(id),
	nota INT NOT NULL CHECK (nota >=1 AND nota <= 5),
	comentario TEXT,
	data_avaliacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	UNIQUE (matricula_id, curso_id)
	);


-- Tabela de Junção
-- Com ela, um instrutor pode ter várias especialidades e uma especialidade pode pertencer a vários instrutores.
CREATE TABLE instrutor_especialidade (
    instrutor_id INT NOT NULL REFERENCES instrutor(id),
    especialidade_id INT NOT NULL REFERENCES especialidade(id),
    -- A PK composta garante que um instrutor não possa ter a mesma especialidade duas vezes.
    PRIMARY KEY (instrutor_id, especialidade_id)
);