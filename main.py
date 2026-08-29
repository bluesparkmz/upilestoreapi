import os
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import get_settings
from core.exceptions import AppException
from routers import admin, announcements, artists, auth, feed, likes, notifications, orders, payments, products, upload, users, websockets

settings = get_settings()

os.makedirs(settings.upload_dir, exist_ok=True)

app = FastAPI(
    title=settings.app_name,
    description="API REST do marketplace UpileStore — venda de obras de arte",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.mount(f"/{settings.upload_dir}", StaticFiles(directory=settings.upload_dir), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Dados inválidos"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": message},
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