# SADA – Sistema de Acompanhamento do Desempenho Acadêmico

Protótipo desenvolvido como Trabalho de Conclusão de Curso (TCC) do curso de Sistemas de Informação da Faculdade Professor Miguel Ângelo da Silva Santos (FeMASS), Macaé/RJ.

- **Autor:** Marcos Emanuel Duarte Cordeiro
- **Orientador:** Prof. Alan Galante
- **Ano:** 2026

O SADA é uma aplicação web **somente de leitura e análise**: calcula indicadores de desempenho (aprovação, média, frequência, estudantes em risco, coeficiente de rendimento) a partir de uma base **simulada**, com dois perfis de acesso (coordenador e professor). Ele não grava notas nem faltas.

> **Importante:** todos os dados são **fictícios**, gerados por um programa com semente fixa (42). Nenhum dado real de estudantes, docentes ou da instituição é usado neste repositório.

## Funcionalidades

| Funcionalidade | Descrição | Rota | Quem acessa |
|---|---|---|---|
| Login e perfis | Autenticação por sessão, com perfis de coordenador e de professor | `/accounts/login/` | Todos |
| Painel | Quatro indicadores (taxa de aprovação, média geral, frequência média e estudantes em risco) e gráficos interativos: aprovação por disciplina, evolução por período, distribuição das médias e situação por coorte de ingresso | `/` | Todos (o gráfico de coortes só aparece para o coordenador) |
| Filtros | Filtro por período letivo e por disciplina, que atualiza o painel e a consulta | `/` e `/consulta/` | Todos |
| Consulta de desempenho | Tabela paginada (50 linhas por página) com os registros de diário, ordenada do período mais recente para o mais antigo, com destaque para valores fora dos limites | `/consulta/` | Todos |
| Estudantes em risco | Sinalização em dois níveis (crítico e atenção) nos diários em andamento | Painel e consulta | Todos |
| Histórico do estudante | Disciplinas cursadas por período, média, nota final, frequência, resultado e Coeficiente de Rendimento (CR) | `/estudantes/<matrícula>/` | Todos, dentro do escopo de acesso |
| Exportação | Exporta o resultado filtrado em CSV (até 2.000 linhas) e em PDF | `/exportar/csv/` e `/exportar/pdf/` | Todos |
| Qualidade dos dados | Lista os diários cujo resultado armazenado difere do recalculado pelas regras | `/divergencias/` | Só o coordenador |
| Área administrativa | Gestão de usuários e grupos do Django | `/admin/` | Administrador |

**Controle de acesso.** O coordenador vê o curso inteiro. O professor vê apenas as suas turmas: ao tentar abrir `/divergencias/` recebe erro 403, e ao tentar abrir o histórico de um estudante que não está nas suas turmas recebe erro 404.

**Regras de negócio aplicadas** (`academico/regras.py`): média semestral, aprovação com média de 7,0 ou mais, exame final para média de 4,0 a 6,9 com nota de aprovação 5,0, frequência mínima de 75%, reprovação por nota ou por falta, Coeficiente de Rendimento e nível de risco. Algumas regras são interpretações do autor, ainda não confirmadas com a secretaria acadêmica; ver o TCC, Capítulo 5.

**Fora do escopo.** O SADA não lança nem altera notas e faltas, e não se conecta ao banco real da instituição.

## Tecnologias

| Tecnologia | Versão usada na reprodução do autor |
|---|---|
| Python | 3.13.17 |
| Django | 5.2.19 |
| PostgreSQL | 16.15-5 |
| psycopg / psycopg-binary | 3.3.8 |
| pandas | 3.1.1 |
| NumPy | 2.5.4 |
| Plotly | 7.1.0 |
| Faker | 40.44.0 |
| ReportLab | 5.1.0 |
| pytest / pytest-django | 9.2.0 / 4.14.0 |

O `requirements.txt` aceita faixas de versões. As versões exatas usadas estão na Tabela 4 do TCC.

## Como executar (Windows 11 Pro 25H2 (OS build 26200.9711), PowerShell)

Pré-requisitos: Python 3.12 ou superior e PostgreSQL 16 instalados. O `psql` deve estar acessível.

1. **Ambiente virtual e dependências**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Banco de dados** (no `psql`, como `postgres`; troque a senha)
   ```sql
   psql -h localhost -U postgres
   CREATE ROLE sada LOGIN PASSWORD 'defina-uma-senha' CREATEDB;
   CREATE DATABASE sada OWNER sada ENCODING 'UTF8' TEMPLATE template0;
   ```

3. **Senha do banco** (vale só para a janela atual do terminal)
   ```powershell
   $env:SADA_DB_PASSWORD = "defina-uma-senha"
   ```
   Outras variáveis opcionais: `SADA_DB_NAME`, `SADA_DB_USER`, `SADA_DB_HOST`, `SADA_DB_PORT` (padrão 5432).

4. **Tabelas e dados simulados**
   ```powershell
   python manage.py makemigrations academico   # só se a pasta academico\migrations não existir
   python manage.py migrate
   python manage.py gerar_dados --semente 42 --senha "senha-de-teste"
   ```
   Ao final deve aparecer: `Base simulada carregada: 456 estudantes, 14184 registros de diário.`
   A `senha-de-teste` é a senha dos usuários de demonstração (`coordenador` e `docente01` a `docente22`).

5. **Ligar o sistema**
   ```powershell
   python manage.py runserver
   ```
   Abra `http://localhost:8000` e entre como `coordenador`.

## Verificação

Testes unitários (não precisam de banco):
```powershell
python -m unittest tests.test_regras tests.test_matricula tests.test_grade tests.test_modulos
```
Esperado: `Ran 82 tests` e `OK`.

Conferência dos números do TCC (não precisa de banco):
```powershell
python scripts/conferir_resultados.py
```
Esperado: `Todos os valores conferem.`

Testes de integração do Django (precisam do PostgreSQL e do usuário `sada` com permissão `CREATEDB`):
```powershell
python -m pytest
```

Valores de referência com a semente 42: 456 estudantes, 51 disciplinas, 426 turmas, 14.184 diários, aprovação 84,4%, média geral 7,47, frequência média 88,9%, 215 estudantes em risco (35 críticos e 180 em atenção), 0 divergências de resultado.

## Estrutura

| Pasta ou arquivo | Conteúdo |
|---|---|
| `academico/` | Modelos, regras de negócio (`regras.py`), matrícula, grade curricular, simulação, serviços, visões e exportação |
| `painel/` | Indicadores em pandas, consultas, gráficos e modelos de página |
| `sada/` | Configuração do projeto Django |
| `sql/` | Esquema físico, papéis de banco e consultas de indicadores |
| `scripts/` | Conferência dos valores e validação do esquema no PostgreSQL |
| `tests/` | Testes unitários e de integração |
| `templates/` | Páginas base e de login |
| `docs/` | Comandos e estrutura de referência |

## Uso de inteligência artificial

O código e os testes do TCC foram desenvolvidos com participação de uma ferramenta de IA generativa (claude-sonnet-5-5, da Anthropic), sob a direção do autor. O uso está declarado na seção 2.10 do TCC, conforme a Deliberação CONSUP nº 06/2026 da FeMASS. O autor é responsável pela versão final.
