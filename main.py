from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import get_settings
from core.database import Base, engine
from core.exceptions import AppException
import models  # noqa: F401
from routers import admin, announcements, artists, auth, feed, likes, notifications, orders, payments, products, upload, users, websockets

settings = get_settings()

os.makedirs(settings.upload_dir, exist_ok=True)


from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria todas as tabelas no PostgreSQL/SQLite se ainda não existirem
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas da base de dados verificadas/criadas com sucesso.")
    except Exception as e:
        print(f"Aviso ao verificar tabelas: {e}")

    # Atribui permissões de Admin no startup via instrução SQL para o email/username da variável de ambiente ADMIN
    admin_val = (
        os.getenv("ADMIN")
        or os.getenv("ADMIN_EMAIL")
        or getattr(settings, "admin", None)
        or getattr(settings, "admin_email", None)
    )
    if admin_val:
        admin_identifier = admin_val.strip()
        try:
            with engine.begin() as conn:
                res = conn.execute(
                    text(
                        "UPDATE users SET is_admin = TRUE, is_verified = TRUE, is_active = TRUE "
                        "WHERE LOWER(email) = LOWER(:val) OR LOWER(username) = LOWER(:val)"
                    ),
                    {"val": admin_identifier},
                )
                if res.rowcount > 0:
                    print(
                        f"SQL Startup: Permissões de Administrador concedidas com sucesso a '{admin_identifier}' ({res.rowcount} conta(s) promovida(s))."
                    )
                else:
                    print(
                        f"SQL Startup: Utilizador com email/username '{admin_identifier}' ainda não se registou."
                    )
        except Exception as exc:
            print(f"Aviso SQL Startup ao atribuir Admin: {exc}")

    yield


app = FastAPI(
    title=settings.app_name,
    description="API REST do marketplace UpileStore — venda de obras de arte",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.mount(f"/{settings.upload_dir}", StaticFiles(directory=settings.upload_dir), name="uploads")

# Origens padrão permitidas para CORS
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://upile-store-moz.vercel.app",
]

cors_origins = list(set(DEFAULT_CORS_ORIGINS + settings.cors_origins_list))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def get_cors_headers(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if origin and ("vercel.app" in origin or "localhost" in origin or "127.0.0.1" in origin):
        return {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"}
    return {"Access-Control-Allow-Origin": "*"}


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message},
        headers=get_cors_headers(request),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Dados inválidos"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": message},
        headers=get_cors_headers(request),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_msg = str(exc)
    print(f"Erro interno não tratado: {error_msg}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Ocorreu um erro no servidor. Por favor, tente novamente em breve.",
        },
        headers=get_cors_headers(request),
    )



@app.get("/", tags=["Health"])
def root() -> dict:
    return {"success": True, "data": {"app": settings.app_name, "status": "ok"}}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(artists.router)
app.include_router(upload.router)
app.include_router(feed.router)
app.include_router(products.router)
app.include_router(likes.router)
app.include_router(announcements.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(notifications.router)
app.include_router(websockets.router)
app.include_router(admin.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app")    