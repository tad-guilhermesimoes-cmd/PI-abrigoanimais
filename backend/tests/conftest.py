import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

# Os testes usam outro banco e outra pasta de fotos, para não mexer nos dados reais.
os.environ["DATABASE_URL"] = os.environ.get(
    "DATABASE_URL_TESTE",
    "mysql+pymysql://amparapet:amparapet@127.0.0.1:3307/amparapet_teste?charset=utf8mb4",
)
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="amparapet_fotos_")
os.environ["ADMIN_INICIAL_EMAIL"] = "admin@teste.com"
os.environ["ADMIN_INICIAL_SENHA"] = "senha-do-admin"
sys.path.insert(0, str(RAIZ / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.init_db import criar_estrutura  # noqa: E402
from app.main import app  # noqa: E402

ADMIN = {"email": "admin@teste.com", "senha": "senha-do-admin"}


@pytest.fixture(scope="session", autouse=True)
def _estrutura():
    Base.metadata.drop_all(engine)
    criar_estrutura()
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _banco_limpo():
    """Esvazia as tabelas antes de cada teste e recria admin e configurações."""
    with engine.begin() as con:
        con.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for tabela in Base.metadata.sorted_tables:
            con.execute(text(f"TRUNCATE TABLE {tabela.name}"))
        con.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    shutil.rmtree(os.environ["UPLOAD_DIR"] + "/animais", ignore_errors=True)
    criar_estrutura()


@pytest.fixture
def cliente():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin(cliente):
    """Cliente já logado como administrador."""
    r = cliente.post("/api/auth/login", json=ADMIN)
    assert r.status_code == 200, r.text
    cliente.headers["Authorization"] = "Bearer " + r.json()["token"]
    return cliente


def novo_animal(cliente, **campos):
    dados = {"nome": "Rex", "especie": "CAO", "sexo": "MACHO", "porte": "MEDIO", **campos}
    r = cliente.post("/api/admin/animais", json=dados)
    assert r.status_code == 201, r.text
    return r.json()
