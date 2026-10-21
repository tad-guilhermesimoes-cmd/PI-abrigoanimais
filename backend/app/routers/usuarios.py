"""Cadastro de administradores. Todos têm o mesmo nível de acesso."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import schemas, security
from ..database import get_db
from ..models import Usuario
from ..security import usuario_atual

router = APIRouter(prefix="/api/admin/usuarios", tags=["Usuários"],
                   dependencies=[Depends(usuario_atual)])


def _email_em_uso(db: Session, email: str, exceto_id: int | None = None) -> bool:
    q = select(Usuario.id).where(Usuario.email == email)
    if exceto_id:
        q = q.where(Usuario.id != exceto_id)
    return db.scalar(q) is not None


def _buscar(db: Session, usuario_id: int) -> Usuario:
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    return u


@router.get("", response_model=list[schemas.UsuarioSaida])
def listar(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.nome)).all()


@router.post("", response_model=schemas.UsuarioSaida, status_code=201)
def criar(dados: schemas.UsuarioCriar, db: Session = Depends(get_db)):
    email = dados.email.lower()
    if _email_em_uso(db, email):
        raise HTTPException(409, "Já existe um usuário com este e-mail")
    u = Usuario(nome=dados.nome.strip(), email=email, senha_hash=security.hash_senha(dados.senha))
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.patch("/{usuario_id}", response_model=schemas.UsuarioSaida,
              summary="Editar nome, e-mail, senha ou ativar/desativar")
def editar(usuario_id: int, dados: schemas.UsuarioAtualizar,
           logado: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    u = _buscar(db, usuario_id)
    campos = dados.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in campos:
        campos["email"] = campos["email"].lower()
        if _email_em_uso(db, campos["email"], exceto_id=u.id):
            raise HTTPException(409, "Já existe um usuário com este e-mail")
    if campos.get("ativo") is False:
        if u.id == logado.id:
            raise HTTPException(400, "Você não pode desativar a si mesmo")
        security.encerrar_sessoes_do_usuario(db, u.id)
    if "senha" in campos:
        u.senha_hash = security.hash_senha(campos.pop("senha"))
        if u.id != logado.id:
            security.encerrar_sessoes_do_usuario(db, u.id)
    for campo, valor in campos.items():
        setattr(u, campo, valor.strip() if isinstance(valor, str) else valor)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{usuario_id}", status_code=204)
def excluir(usuario_id: int, logado: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    u = _buscar(db, usuario_id)
    if u.id == logado.id:
        raise HTTPException(400, "Você não pode excluir a si mesmo")
    ativos = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.ativo.is_(True)))
    if u.ativo and ativos <= 1:
        raise HTTPException(400, "O sistema precisa de pelo menos um administrador ativo")
    db.delete(u)
    db.commit()
