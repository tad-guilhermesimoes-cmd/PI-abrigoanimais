import io
from datetime import date

from PIL import Image

from app import config
from app.servicos import idade_texto
from conftest import ADMIN, novo_animal


def imagem(formato="PNG", tamanho=(800, 600)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", tamanho, (200, 100, 50)).save(buf, formato)
    return buf.getvalue()


# ---------- Autenticação (RF07 / RNF05) ----------

def test_rotas_admin_exigem_login(cliente):
    assert cliente.get("/api/admin/painel").status_code == 401
    assert cliente.post("/api/admin/animais", json={}).status_code == 401
    cliente.headers["Authorization"] = "Bearer token-falso"
    assert cliente.get("/api/admin/painel").status_code == 401


def test_login_errado_e_bloqueio_por_tentativas(cliente):
    for _ in range(config.LOGIN_MAX_TENTATIVAS):
        assert cliente.post("/api/auth/login", json={**ADMIN, "senha": "errada"}).status_code == 401
    # mesmo com a senha certa, fica bloqueado
    assert cliente.post("/api/auth/login", json=ADMIN).status_code == 429


def test_logout_invalida_o_token(admin):
    assert admin.get("/api/auth/eu").json()["email"] == ADMIN["email"]
    assert admin.post("/api/auth/logout").status_code == 204
    assert admin.get("/api/auth/eu").status_code == 401


def test_trocar_senha(admin, cliente):
    r = admin.put("/api/auth/senha", json={"senha_atual": ADMIN["senha"], "senha_nova": "nova-senha-123"})
    assert r.status_code == 204
    cliente.headers.pop("Authorization")
    assert cliente.post("/api/auth/login", json=ADMIN).status_code == 401
    assert cliente.post("/api/auth/login", json={**ADMIN, "senha": "nova-senha-123"}).status_code == 200


# ---------- Cadastro, edição e status (RF01 / RF08 / RF09 / RF10) ----------

def test_cadastro_completo_e_edicao(admin):
    a = novo_animal(admin, raca="Labrador", data_nascimento="2023-01-01", cor="Preto",
                    comportamento="Dócil", vacinado=True, vacinas_detalhes="V10",
                    castrado=True, necessidades_especiais="  ", descricao="Muito bom")
    assert a["status"] == "DISPONIVEL"
    assert a["necessidades_especiais"] is None  # texto vazio vira nulo
    assert a["idade"]

    r = admin.patch(f"/api/admin/animais/{a['id']}", json={"nome": "Rex II", "porte": "GRANDE"})
    assert r.status_code == 200
    assert r.json()["nome"] == "Rex II" and r.json()["porte"] == "GRANDE"
    assert r.json()["raca"] == "Labrador"  # campos não enviados continuam iguais


def test_validacoes_do_cadastro(admin):
    assert admin.post("/api/admin/animais", json={"nome": "X"}).status_code == 422
    r = admin.post("/api/admin/animais", json={"nome": "X", "especie": "PEIXE", "sexo": "MACHO", "porte": "MEDIO"})
    assert r.status_code == 422
    r = admin.post("/api/admin/animais", json={"nome": "X", "especie": "CAO", "sexo": "MACHO",
                                               "porte": "MEDIO", "data_nascimento": "2999-01-01"})
    assert r.status_code == 422


def test_status_historico_e_reativacao(admin, cliente):
    a = novo_animal(admin)
    admin.patch(f"/api/admin/animais/{a['id']}/status", json={"status": "EM_PROCESSO"})
    admin.patch(f"/api/admin/animais/{a['id']}/status", json={"status": "ADOTADO", "observacao": "Família Silva"})

    # adotado some da vitrine, mas a página continua acessível
    vitrine = cliente.get("/api/animais").json()
    assert all(x["id"] != a["id"] for x in vitrine["itens"])
    assert cliente.get(f"/api/animais/{a['id']}").json()["status"] == "ADOTADO"

    # reativar
    admin.patch(f"/api/admin/animais/{a['id']}/status", json={"status": "DISPONIVEL"})
    assert any(x["id"] == a["id"] for x in cliente.get("/api/animais").json()["itens"])

    hist = admin.get(f"/api/admin/animais/{a['id']}/historico").json()
    assert [h["status_novo"] for h in hist] == ["DISPONIVEL", "ADOTADO", "EM_PROCESSO", "DISPONIVEL"]
    assert hist[1]["observacao"] == "Família Silva"
    assert hist[1]["usuario_nome"] == "Administrador"


def test_excluir_animal_remove_fotos_e_vitrine(admin, cliente):
    a = novo_animal(admin)
    admin.post(f"/api/admin/animais/{a['id']}/fotos", files={"fotos": ("a.png", imagem(), "image/png")})
    pasta = config.UPLOAD_DIR / "animais" / str(a["id"])
    assert pasta.exists()
    assert admin.delete(f"/api/admin/animais/{a['id']}").status_code == 204
    assert not pasta.exists()
    assert cliente.get(f"/api/animais/{a['id']}").status_code == 404
    assert cliente.get("/api/animais").json()["total"] == 0


# ---------- Fotos (RF04) ----------

def test_upload_reordenar_e_remover_fotos(admin, cliente):
    a = novo_animal(admin)
    r = admin.post(f"/api/admin/animais/{a['id']}/fotos", files=[
        ("fotos", ("1.png", imagem("PNG", (3000, 2000)), "image/png")),
        ("fotos", ("2.jpg", imagem("JPEG"), "image/jpeg")),
        ("fotos", ("3.webp", imagem("WEBP"), "image/webp")),
    ])
    assert r.status_code == 201, r.text
    fotos = r.json()["fotos"]
    assert len(fotos) == 3

    # foto grande foi reduzida e a miniatura gerada, sem distorcer a proporção
    grande = Image.open(io.BytesIO(cliente.get(fotos[0]["url"]).content))
    assert grande.size == (config.FOTO_LADO_MAX, round(config.FOTO_LADO_MAX / 1.5))
    mini = Image.open(io.BytesIO(cliente.get(fotos[0]["miniatura_url"]).content))
    assert max(mini.size) == config.MINIATURA_LADO_MAX

    ids = [f["id"] for f in fotos]
    r = admin.put(f"/api/admin/animais/{a['id']}/fotos/ordem", json={"ids": ids[::-1]})
    assert [f["id"] for f in r.json()["fotos"]] == ids[::-1]
    resumo = cliente.get("/api/animais").json()["itens"][0]
    assert resumo["foto_principal"]["id"] == ids[-1]

    assert admin.put(f"/api/admin/animais/{a['id']}/fotos/ordem", json={"ids": ids[:2]}).status_code == 400

    assert admin.delete(f"/api/admin/fotos/{ids[0]}").status_code == 204
    assert len(admin.get(f"/api/admin/animais/{a['id']}").json()["fotos"]) == 2


def test_upload_rejeita_arquivos_invalidos(admin):
    a = novo_animal(admin)
    url = f"/api/admin/animais/{a['id']}/fotos"
    assert admin.post(url, files={"fotos": ("x.png", b"nao sou imagem", "image/png")}).status_code == 415
    assert admin.post(url, files={"fotos": ("x.gif", imagem("GIF"), "image/gif")}).status_code == 415
    grande = b"\0" * (config.FOTO_TAMANHO_MAX_MB * 1024 * 1024 + 1)
    assert admin.post(url, files={"fotos": ("x.png", grande, "image/png")}).status_code == 413
    # se uma do lote falha, nenhuma é salva
    r = admin.post(url, files=[("fotos", ("ok.png", imagem(), "image/png")),
                               ("fotos", ("ruim.png", b"xx", "image/png"))])
    assert r.status_code == 415
    assert admin.get(f"/api/admin/animais/{a['id']}").json()["fotos"] == []
    assert list((config.UPLOAD_DIR / "animais" / str(a["id"])).glob("*")) == []


# ---------- Vitrine e filtros (RF02 / RF03 / RF05) ----------

def test_vitrine_publica_e_filtros(admin, cliente):
    novo_animal(admin, nome="Thor", especie="CAO", porte="GRANDE", castrado=True, vacinado=True)
    novo_animal(admin, nome="Mia", especie="GATO", sexo="FEMEA", porte="PEQUENO")
    novo_animal(admin, nome="Bob", porte="PEQUENO", status="EM_PROCESSO")
    novo_animal(admin, nome="Zeca", status="ADOTADO")

    def nomes(**params):
        r = cliente.get("/api/animais", params=params)
        assert r.status_code == 200
        return sorted(x["nome"] for x in r.json()["itens"])

    assert nomes() == ["Bob", "Mia", "Thor"]
    assert nomes(especie="GATO") == ["Mia"]
    assert nomes(porte=["PEQUENO", "GRANDE"]) == ["Bob", "Mia", "Thor"]
    assert nomes(porte="PEQUENO") == ["Bob", "Mia"]
    assert nomes(castrado="true") == ["Thor"]
    assert nomes(vacinado="false") == ["Bob", "Mia"]
    assert nomes(status="EM_PROCESSO") == ["Bob"]
    assert nomes(status="ADOTADO") == ["Bob", "Mia", "Thor"]  # adotado nunca é exposto
    assert nomes(busca="th") == ["Thor"]
    assert cliente.get("/api/animais", params={"por_pagina": 2}).json()["total"] == 3
    assert len(cliente.get("/api/animais", params={"por_pagina": 2, "pagina": 2}).json()["itens"]) == 1


def test_pagina_do_animal_tem_links(admin, cliente):
    a = novo_animal(admin)
    d = cliente.get(f"/api/animais/{a['id']}").json()
    assert d["links"]["pagina"].endswith(f"id={a['id']}")
    assert d["links"]["compartilhar_whatsapp"].startswith("https://wa.me/?text=")
    assert d["links"]["whatsapp_interesse"] is None  # WhatsApp do abrigo ainda não configurado
    assert "cliques_interesse" not in d  # dado interno não vaza na rota pública


# ---------- Interesse (RF06) e painel (RF14) ----------

def test_interesse_conta_clique_e_monta_whatsapp(admin, cliente):
    admin.put("/api/admin/abrigo", json={"whatsapp": "5543999998888"})
    a = novo_animal(admin, nome="Thor")
    r = cliente.post(f"/api/animais/{a['id']}/interesse")
    url = r.json()["whatsapp_url"]
    assert url.startswith("https://wa.me/5543999998888?text=")
    assert "Thor" in url and f"%23{a['id']}" in url
    cliente.post(f"/api/animais/{a['id']}/interesse")
    assert admin.get(f"/api/admin/animais/{a['id']}").json()["cliques_interesse"] == 2

    admin.patch(f"/api/admin/animais/{a['id']}/status", json={"status": "ADOTADO"})
    assert cliente.post(f"/api/animais/{a['id']}/interesse").status_code == 409


def test_painel(admin, cliente):
    a = novo_animal(admin)
    novo_animal(admin, status="EM_PROCESSO")
    novo_animal(admin, status="ADOTADO")
    novo_animal(admin, status="ADOTADO")
    cliente.post(f"/api/animais/{a['id']}/interesse")
    p = admin.get("/api/admin/painel").json()
    assert (p["total"], p["disponiveis"], p["em_processo"], p["adotados"]) == (4, 1, 1, 2)
    assert p["cliques_interesse_total"] == 1
    assert p["mais_procurados"][0]["id"] == a["id"]


# ---------- Dados do abrigo (RF12 / RF13) ----------

def test_dados_do_abrigo(admin, cliente):
    assert cliente.get("/api/abrigo").json()["nome_abrigo"] == "Abrigo Toca de Assis"
    r = admin.put("/api/admin/abrigo", json={"endereco": "Rua X, 10", "horario_funcionamento": "8h às 17h"})
    assert r.status_code == 200
    publico = cliente.get("/api/abrigo").json()
    assert publico["endereco"] == "Rua X, 10" and publico["horario_funcionamento"] == "8h às 17h"
    assert admin.put("/api/admin/abrigo", json={"whatsapp": "43 9999-8888"}).status_code == 422


# ---------- Usuários ----------

def test_gerenciar_administradores(admin, cliente):
    r = admin.post("/api/admin/usuarios", json={"nome": "Talita", "email": "Talita@Abrigo.com", "senha": "12345678"})
    assert r.status_code == 201
    novo = r.json()
    assert novo["email"] == "talita@abrigo.com"
    assert admin.post("/api/admin/usuarios", json={"nome": "X", "email": "talita@abrigo.com",
                                                   "senha": "12345678"}).status_code == 409

    eu = admin.get("/api/auth/eu").json()
    assert admin.delete(f"/api/admin/usuarios/{eu['id']}").status_code == 400
    assert admin.patch(f"/api/admin/usuarios/{eu['id']}", json={"ativo": False}).status_code == 400

    # desativar derruba a sessão do usuário e impede novo login
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as outro:
        tk = outro.post("/api/auth/login", json={"email": "talita@abrigo.com", "senha": "12345678"}).json()["token"]
        outro.headers["Authorization"] = "Bearer " + tk
        assert outro.get("/api/auth/eu").status_code == 200
        admin.patch(f"/api/admin/usuarios/{novo['id']}", json={"ativo": False})
        assert outro.get("/api/auth/eu").status_code == 401
        assert outro.post("/api/auth/login", json={"email": "talita@abrigo.com",
                                                    "senha": "12345678"}).status_code == 401

    assert admin.delete(f"/api/admin/usuarios/{novo['id']}").status_code == 204


# ---------- Unidade ----------

def test_idade_texto():
    hoje = date(2026, 10, 19)
    assert idade_texto(None, hoje) is None
    assert idade_texto(date(2026, 10, 1), hoje) == "Menos de 1 mês"
    assert idade_texto(date(2026, 9, 1), hoje) == "1 mês"
    assert idade_texto(date(2026, 4, 1), hoje) == "6 meses"
    assert idade_texto(date(2025, 10, 1), hoje) == "1 ano"
    assert idade_texto(date(2023, 7, 1), hoje) == "3 anos e 3 meses"
