# UpileStore API

API REST do marketplace UpileStore — venda de obras de arte.

## Stack

- Python 3.12+
- FastAPI
- SQLAlchemy + Alembic
- SQLite (preparado para PostgreSQL)
- JWT + bcrypt

## Estrutura

```text
upilestore_api/
├── main.py
├── core/
├── models/
├── schemas/
├── routers/
├── controllers/
├── dependencies/
├── alembic/
├── tests/
├── requirements.txt
└── .env
```

## Instalação

```bash
cd upilestore_api
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` e altere `JWT_SECRET_KEY` antes de usar em produção.

## Migrations

```bash
alembic upgrade head
```

## Executar

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Documentação:

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testes

```bash
pytest -v
```

## Endpoints principais

| Grupo | Prefixo |
|-------|---------|
| Auth | `/auth` |
| Users | `/users` |
| Products | `/products` |
| Announcements | `/announcements` |
| Likes | `/products/{id}/like` |
| Orders | `/orders` |
| Payments | `/payments` |

## Migrar para PostgreSQL

Altere `DATABASE_URL` no `.env`:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/upilestore
```

Depois execute `alembic upgrade head`.
