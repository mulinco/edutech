-- aqui estão primeiro as tabelas que não dependem de nenhuma outra.
CREATE TABLE genero (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE categoria(
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT
);

-- Tabela Supertipo (a base de todos os usuários)
CREATE TABLE pessoa (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(60) NOT NULL UNIQUE,
    genero_id INT REFERENCES genero(id),
    data_nascimento DATE, 
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabelas Subtipo  

CREATE TABLE aluno (
    id SERIAL PRIMARY KEY,
    pessoa_id INT NOT NULL UNIQUE REFERENCES pessoa(id),
    como_nos_conheceu VARCHAR(50) CHECK (como_nos_conheceu IN ('Redes Sociais', 'Anúncio Google', 'Indicação de amigos', 'Youtube', 'Outro'))
);

CREATE TABLE instrutor (
    id SERIAL PRIMARY KEY,
    pessoa_id INT NOT NULL UNIQUE REFERENCES pessoa(id),
    especialidade VARCHAR(100),
    biografia TEXT
);

CREATE TABLE monitor (
    id SERIAL PRIMARY KEY,
    pessoa_id INT NOT NULL UNIQUE REFERENCES pessoa(id)
);


-- Tabelas Centrais do Sistema 

CREATE TABLE curso (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    categoria_id INT NOT NULL REFERENCES categoria(id),
    instrutor_id INT NOT NULL REFERENCES instrutor(id),
    preco NUMERIC(10, 2) NOT NULL CHECK (preco >= 0),
    carga_horaria INT NOT NULL CHECK (carga_horaria > 0),
    nivel VARCHAR(20) NOT NULL CHECK (nivel IN ('iniciante', 'intermediario', 'avancado')),
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE modulo (
    id SERIAL PRIMARY KEY,
    curso_id INT NOT NULL REFERENCES curso(id),
    titulo VARCHAR(200) NOT NULL,
    ordem INT NOT NULL CHECK (ordem > 0)
);

CREATE TABLE aula (
    id SERIAL PRIMARY KEY,
    modulo_id INT NOT NULL REFERENCES modulo(id),
    titulo VARCHAR(200) NOT NULL,
    ordem INT NOT NULL CHECK (ordem > 0),
    duracao_minutos INT CHECK (duracao_minutos > 0),
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('video', 'texto', 'quiz'))
);


-- Tabelas de Ações e Detalhes 

CREATE TABLE matricula (
    id SERIAL PRIMARY KEY,
    aluno_id INT NOT NULL REFERENCES aluno(id),
    curso_id INT NOT NULL REFERENCES curso(id),
    data_matricula DATE NOT NULL DEFAULT CURRENT_DATE,
    data_conclusao DATE,
    status VARCHAR(15) NOT NULL CHECK (status IN ('ativa', 'concluida', 'cancelada', 'pendente')),
    UNIQUE (aluno_id, curso_id)
);

CREATE TABLE progresso_aula (
    id SERIAL PRIMARY KEY,
    matricula_id INT NOT NULL REFERENCES matricula(id),
    aula_id INT NOT NULL REFERENCES aula(id),
    concluida BOOLEAN NOT NULL DEFAULT FALSE,
    data_conclusao TIMESTAMP,
    UNIQUE (matricula_id, aula_id)
);

CREATE TABLE pagamento (
    id SERIAL PRIMARY KEY,
    matricula_id INT NOT NULL REFERENCES matricula(id),
    valor NUMERIC(10, 2) NOT NULL CHECK (valor >= 0),
    data_pagamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metodo_pagamento VARCHAR(50) NOT NULL CHECK (metodo_pagamento IN ('Cartão de Crédito', 'Pix', 'Boleto')),
    cupom_desconto VARCHAR(50),
    status_pagamento VARCHAR(20) NOT NULL CHECK (status_pagamento IN ('Pendente', 'Aprovado', 'Recusado', 'Estornado'))
);

CREATE TABLE avaliacoes (
	id SERIAL PRIMARY KEY,
	matricula_id INT NOT NULL REFERENCES matricula(id),
	curso_id INT NOT NULL REFERENCES curso(id),
	nota INT NOT NULL CHECK (nota >=1 AND nota <= 5),
	comentario TEXT,
	data_avaliacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	UNIQUE (matricula_id, curso_id)
	);

CREATE TABLE curso_monitor (
    curso_id INT NOT NULL REFERENCES curso(id),
    monitor_id INT NOT NULL REFERENCES monitor(id),
    data_atribuicao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (curso_id, monitor_id)
);