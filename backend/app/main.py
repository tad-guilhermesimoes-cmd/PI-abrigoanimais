"""AmparaPet — API do sistema de adoção do Abrigo Toca de Assis.

Rodar (na pasta backend):  uvicorn app.main:app --reload
Documentação interativa:   http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .init_db import criar_estrutura
from .routers import admin, auth, publico, usuarios


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    criar_estrutura()
    yield


app = FastAPI(
    title="AmparaPet API",
    version="1.0.0",
    description=(
        "API do AmparaPet. Rotas em **Público** não exigem login. "
        "Para as demais, faça login em `/api/auth/login` e clique em **Authorize** "
        "colando o token recebido."
    ),
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGENS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(publico.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(usuarios.router)

config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

if config.SERVIR_INTERFACE_TESTE:
    pasta_teste = config.RAIZ_PROJETO / "frontend-teste"
    app.mount("/teste", StaticFiles(directory=pasta_teste, html=True), name="teste")

    @app.get("/", include_in_schema=False)
    def raiz():
        return RedirectResponse("/teste/")


@app.get("/api/saude", tags=["Público"], summary="Verifica se a API está no ar")
def saude():
    return {"status": "ok"}
