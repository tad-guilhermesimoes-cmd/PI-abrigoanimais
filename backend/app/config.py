"""Configurações lidas do arquivo .env na raiz do projeto."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROJETO / ".env")


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip()]


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://amparapet:amparapet@127.0.0.1:3307/amparapet?charset=utf8mb4",
)

# Pasta onde ficam as fotos enviadas (servidas em /uploads)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(RAIZ_PROJETO / "uploads")))

# Origens liberadas para o front-end chamar a API (CORS). "*" libera todas.
CORS_ORIGENS = _lista(os.getenv("CORS_ORIGENS", "*"))

# Duração da sessão de login, em horas
SESSAO_HORAS = int(os.getenv("SESSAO_HORAS", "8"))

# Controle de tentativas de login (RNF05)
LOGIN_MAX_TENTATIVAS = int(os.getenv("LOGIN_MAX_TENTATIVAS", "5"))
LOGIN_BLOQUEIO_MINUTOS = int(os.getenv("LOGIN_BLOQUEIO_MINUTOS", "15"))

# Fotos (RF04 / RNF07)
FOTO_TAMANHO_MAX_MB = 5
FOTO_LADO_MAX = 1600       # px do maior lado da foto grande
MINIATURA_LADO_MAX = 400   # px do maior lado da miniatura

# Administrador criado na primeira inicialização do banco
ADMIN_INICIAL_NOME = os.getenv("ADMIN_INICIAL_NOME", "Administrador")
ADMIN_INICIAL_EMAIL = os.getenv("ADMIN_INICIAL_EMAIL", "admin@amparapet.local")
ADMIN_INICIAL_SENHA = os.getenv("ADMIN_INICIAL_SENHA", "trocar123")

# Serve a interface de teste em /teste (desligar em produção)
SERVIR_INTERFACE_TESTE = os.getenv("SERVIR_INTERFACE_TESTE", "1") == "1"
