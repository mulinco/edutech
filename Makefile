#Makefile para o Pipeline de Dados EduTech
#
#Foco no Fluxo 2 (Python direto para o banco), que dá menos trabalho por ser automatizado :D
#
#Comandos:
#   make install     - Instala as dependências do Python
#   make run-fluxo2  - Roda o Fluxo 2 (população automática)
#   make relatorios  - Roda a análise e gera o .md
#   make full-fluxo2 - Roda o Fluxo 2 E os relatórios em sequência
#   make clean       - Limpa arquivos gerados (logs, relatórios, caches)

#Garante que os comandos sejam executados mesmo que existam arquivos com esses nomes
.PHONY: install run-fluxo2 relatorios full-fluxo2 clean

# Configuração do Ambiente 

install:
	@echo "Instalando dependências do requirements.txt..."
	pip install -r requirements.txt
	@echo "Instalação concluída."

# Fluxo 2: População Direta (Automática) 

# Define os valores padrão para os argumentos do argparse
# Dá pra mudar os valores como: make run-fluxo2 ALUNOS=500
ALUNOS ?= 100
INSTRUTORES ?= 25
CURSOS ?= 50
MATRICULAS ?= 200

run-fluxo2:
	@echo "Executando Fluxo 2: População direta do banco (Alunos: $(ALUNOS))..."
	python python/fluxo_2_banco_direto/popular_banco.py --alunos $(ALUNOS) --instrutores $(INSTRUTORES) --cursos $(CURSOS) --matriculas $(MATRICULAS)
	@echo "Fluxo 2 concluído."

relatorios:
	@echo "Gerando relatórios de análise do banco..."
	python python/fluxo_2_banco_direto/processador_relatorios.py
	@echo "Relatórios gerados em relatorios/relatorio_edutech.md"

full-fluxo2: run-fluxo2 relatorios
	@echo "Pipeline completo (Fluxo 2 + Relatórios) finalizado."

#Limpeza
clean:
	@echo "Limpando arquivos gerados..."
	@if exist relatorios\relatorio_edutech.md del /F /Q relatorios\relatorio_edutech.md
	@if exist logs\*.log del /F /Q logs\*.log
	@if exist data\*.csv del /F /Q data\*.csv
	@if exist .pytest_cache rmdir /S /Q .pytest_cache
	@del /S /Q *.pyc
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@echo "Limpeza concluída."