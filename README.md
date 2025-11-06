# 🚀 Projeto EduTech - Pipeline de Dados

**Autora:** Maria Clara Rodrigues  
**Data:** 26 de Outubro de 2025  
**Curso:** Desenvolvimento Full Stack - Casa Digital 2  
**Iniciativa:** Instituto Consuelo - Projeto Casa Digital 2

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)  
![Status](https://img.shields.io/badge/status-concluído-brightgreen?style=for-the-badge)

Este projeto implementa um pipeline de dados automatizado para a plataforma de cursos online fictícia **EduTech**, com foco em PostgreSQL e Python. Ele gera dados fictícios e popula o banco de dados diretamente, sendo automatizado via `Makefile`.

➡️ **Para detalhes completos sobre a modelagem do banco de dados, decisões de arquitetura e justificativas, por favor, consulte o ficheiro [`docs/documentacao.md`](docs/documentacao.md).**

---

## 🛠️ Pré-requisitos

1.  **Python** (versão 3.9 ou superior)
2.  **PostgreSQL** (servidor ativo)
3.  **(Recomendado)** `make` (veja `docs/documentacao.md` para detalhes de instalação)

---

## ⚙️ Instalação e Configuração

### 1. Clone o Repositório

#### Substitua pelo URL real

```bash
git clone https://github.com/mulinco/edutech.git
```

```bash
cd edutech
```

**2. Configure o Ambiente (.env)**

**Copie o ficheiro de exemplo:**

No PowerShell:
 ```bash  
copy .env.example .env
``` 

No Linux/Mac/Git: 
```bash 
cp .env.example .env
```
Edite o novo .env e preencha a sua DB_PASSWORD (e ajuste DB_USER, DB_HOST, DB_PORT, DB_NAME se necessário).

**3. Crie o Banco de Dados**

    Crie um banco de dados vazio no seu PostgreSQL chamado edutech_db.

**4. Instale as Dependências**


```pip install -r requirements.txt``` 
# Ou: make install


## ▶️ Como Executar (Automação com Makefile)

Use os seguintes comandos make no seu terminal (na raiz do projeto):

```make full-fluxo2```: **(Comando Principal)** Popula o banco com dados fictícios (limpando o anterior) e gera os relatórios de análise.

Exemplo com 20 alunos: ```make full-fluxo2 ALUNOS=20```

```make run-fluxo2```: Apenas popula o banco de dados.

Exemplo: ```make run-fluxo2 ALUNOS=500 CURSOS=10```

```make relatorios```: Apenas gera o relatório (relatorios/relatorio_edutech.md) com base nos dados atuais do banco.

```make clean```: Apaga ficheiros gerados (logs, relatórios, caches).

## 📂 Fluxo Alternativo (Manual - Geração de CSVs)

A pasta [`python/fluxo_1_csv`](python/fluxo_1_csv) contém scripts para um fluxo manual (geração de CSVs para importação).   
Este fluxo não é automatizado pelo [`edutech/Makefile`](/makefile).   
Consulte o [`docs/documentacao.md`](docs/documentacao.md) para detalhes sobre como executar este fluxo manualmente.