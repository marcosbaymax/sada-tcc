# Comandos executados a partir da raiz do projeto (diretório que contém manage.py).
# Linux/macOS; no Windows, use  .venv\Scripts\activate  e  set VARIAVEL=valor.

# 1) ambiente virtual e dependências
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) verificação sem Django nem banco (somente Python, NumPy e pandas)
python -m unittest tests.test_regras tests.test_matricula tests.test_grade tests.test_modulos
python scripts/conferir_resultados.py

# 3) banco PostgreSQL 16 da aplicação (--createdb: o pytest cria um banco de teste)
sudo -u postgres createuser sada --pwprompt --createdb
sudo -u postgres createdb sada --owner sada
export SADA_DB_PASSWORD='defina-uma-senha'

# 4) migrações e carga dos dados simulados (semente 42)
python manage.py makemigrations academico
python manage.py migrate
python manage.py gerar_dados --semente 42 --senha 'senha-de-teste'

# 5) servidor de desenvolvimento: http://localhost:8000
#    usuários: coordenador, docente01 ... docente22 (senha informada no passo 4)
python manage.py runserver

# 6) testes de integração do Django (exigem o passo 3 e as migrações do passo 4)
pytest -q

# 7) validação do esquema SQL em um PostgreSQL descartável (usuário superusuário)
PGHOST=localhost PGUSER=postgres PGPASSWORD='senha-do-postgres' python scripts/validar_pg.py
