"""Login, logout e dados do usuário logado (RF07 / RNF05)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config, schemas, security
from ..database import get_db
from ..models import Usuario

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=schemas.LoginSaida,
             summary="Entrar com e-mail e senha. Use o token como 'Authorization: Bearer <token>'")
def login(dados: schemas.LoginEntrada, request: Request, db: Session = Depends(get_db)):
    email = dados.email.strip().lower()
    ip = security.ip_cliente(request)
    if security.login_bloqueado(db, email):
        raise HTTPException(
            429, f"Muitas tentativas erradas. Tente de novo em {config.LOGIN_BLOQUEIO_MINUTOS} minutos."
        )
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if not usuario or not usuario.ativo or not security.verificar_senha(dados.senha, usuario.senha_hash):
        security.registrar_tentativa(db, email, ip, False)
        raise HTTPException(401, "E-mail ou senha incorretos")
    security.registrar_tentativa(db, email, ip, True)
    token, expira = security.criar_sessao(db, usuario, ip)
    return schemas.LoginSaida(token=token, expira_em=expira, usuario=usuario)


@router.post("/logout", status_code=204, summary="Encerrar a sessão atual")
def logout(token: str = Depends(security.token_atual), db: Session = Depends(get_db)):
    security.encerrar_sessao(db, token)


@router.get("/eu", response_model=schemas.UsuarioSaida, summary="Usuário logado")
def eu(usuario: Usuario = Depends(security.usuario_atual)):
    return usuario


@router.put("/senha", status_code=204,
            summary="Trocar a própria senha (encerra as outras sessões abertas)")
def trocar_senha(
    dados: schemas.TrocarSenha,
    token: str = Depends(security.token_atual),
    usuario: Usuario = Depends(security.usuario_atual),
    db: Session = Depends(get_db),
):
    if not security.verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(400, "Senha atual incorreta")
    usuario.senha_hash = security.hash_senha(dados.senha_nova)
    security.encerrar_sessoes_do_usuario(db, usuario.id, exceto_token=token)
    db.commit()
