"""Senhas, sessões de login e controle de tentativas (RF07 / RNF05)."""
import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from .models import Sessao, TentativaLogin, Usuario

_bearer = HTTPBearer(auto_error=False, description="Token recebido em /api/auth/login")


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), senha_hash.encode())
    except ValueError:
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def agora() -> datetime:
    return datetime.now().replace(microsecond=0)


def ip_cliente(request: Request) -> str | None:
    return request.client.host if request.client else None


def login_bloqueado(db: Session, email: str) -> bool:
    """Bloqueia o e-mail após X falhas seguidas dentro da janela de bloqueio."""
    janela = agora() - timedelta(minutes=config.LOGIN_BLOQUEIO_MINUTOS)
    ultimo_sucesso = db.scalar(
        select(func.max(TentativaLogin.criado_em))
        .where(TentativaLogin.email == email, TentativaLogin.sucesso.is_(True))
    )
    inicio = max(janela, ultimo_sucesso) if ultimo_sucesso else janela
    falhas = db.scalar(
        select(func.count()).select_from(TentativaLogin).where(
            TentativaLogin.email == email,
            TentativaLogin.sucesso.is_(False),
            TentativaLogin.criado_em >= inicio,
        )
    )
    return falhas >= config.LOGIN_MAX_TENTATIVAS


def registrar_tentativa(db: Session, email: str, ip: str | None, sucesso: bool) -> None:
    db.add(TentativaLogin(email=email, ip=ip, sucesso=sucesso, criado_em=agora()))
    db.commit()


def criar_sessao(db: Session, usuario: Usuario, ip: str | None) -> tuple[str, datetime]:
    db.execute(delete(Sessao).where(Sessao.expira_em < agora()))  # limpa sessões vencidas
    token = secrets.token_urlsafe(32)
    expira = agora() + timedelta(hours=config.SESSAO_HORAS)
    db.add(Sessao(token_hash=_hash_token(token), usuario_id=usuario.id, expira_em=expira, ip=ip))
    db.commit()
    return token, expira


def encerrar_sessao(db: Session, token: str) -> None:
    db.execute(delete(Sessao).where(Sessao.token_hash == _hash_token(token)))
    db.commit()


def encerrar_sessoes_do_usuario(db: Session, usuario_id: int, exceto_token: str | None = None) -> None:
    q = delete(Sessao).where(Sessao.usuario_id == usuario_id)
    if exceto_token:
        q = q.where(Sessao.token_hash != _hash_token(exceto_token))
    db.execute(q)


def _nao_autenticado(msg="Faça login para continuar") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, msg, headers={"WWW-Authenticate": "Bearer"})


def token_atual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if not cred:
        raise _nao_autenticado()
    return cred.credentials


def usuario_atual(token: str = Depends(token_atual), db: Session = Depends(get_db)) -> Usuario:
    """Dependência que protege as rotas administrativas."""
    sessao = db.get(Sessao, _hash_token(token))
    if not sessao or sessao.expira_em < agora():
        raise _nao_autenticado("Sessão expirada ou inválida. Faça login novamente.")
    if not sessao.usuario.ativo:
        raise _nao_autenticado("Usuário desativado")
    return sessao.usuario
