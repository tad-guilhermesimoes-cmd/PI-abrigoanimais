"""Tabelas do banco de dados (MySQL)."""
import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Especie(str, enum.Enum):
    CAO = "CAO"
    GATO = "GATO"


class Porte(str, enum.Enum):
    PEQUENO = "PEQUENO"
    MEDIO = "MEDIO"
    GRANDE = "GRANDE"


class Sexo(str, enum.Enum):
    MACHO = "MACHO"
    FEMEA = "FEMEA"


class StatusAnimal(str, enum.Enum):
    DISPONIVEL = "DISPONIVEL"
    EM_PROCESSO = "EM_PROCESSO"
    ADOTADO = "ADOTADO"


def _enum(cls):
    # Guarda o valor do enum (ex.: "CAO") como ENUM nativo do MySQL
    return Enum(cls, values_callable=lambda e: [m.value for m in e], native_enum=True)


# DEFAULT + ON UPDATE no próprio MySQL, para valer também em alterações feitas direto por SQL
_ATUALIZADO_EM = text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(100))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=_ATUALIZADO_EM, onupdate=func.now()
    )


class Sessao(Base):
    """Sessões de login ativas. Guarda só o hash do token."""
    __tablename__ = "sessoes"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expira_em: Mapped[datetime] = mapped_column(DateTime, index=True)
    ip: Mapped[str | None] = mapped_column(String(45))

    usuario: Mapped[Usuario] = relationship()


class TentativaLogin(Base):
    __tablename__ = "tentativas_login"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(150), index=True)
    ip: Mapped[str | None] = mapped_column(String(45))
    sucesso: Mapped[bool] = mapped_column(Boolean)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class Animal(Base):
    __tablename__ = "animais"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    especie: Mapped[Especie] = mapped_column(_enum(Especie), index=True)
    raca: Mapped[str] = mapped_column(String(80), default="SRD", server_default="SRD")
    sexo: Mapped[Sexo] = mapped_column(_enum(Sexo))
    porte: Mapped[Porte] = mapped_column(_enum(Porte), index=True)
    # Data aproximada (o abrigo normalmente só sabe mês/ano). A idade é calculada.
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    cor: Mapped[str | None] = mapped_column(String(60))
    comportamento: Mapped[str | None] = mapped_column(Text)
    vacinado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("0"), index=True)
    vacinas_detalhes: Mapped[str | None] = mapped_column(Text)
    castrado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("0"), index=True)
    necessidades_especiais: Mapped[str | None] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusAnimal] = mapped_column(
        _enum(StatusAnimal), default=StatusAnimal.DISPONIVEL, server_default="DISPONIVEL", index=True
    )
    cliques_interesse: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=_ATUALIZADO_EM, onupdate=func.now()
    )

    fotos: Mapped[list["Foto"]] = relationship(
        back_populates="animal", order_by="Foto.ordem, Foto.id",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    historico: Mapped[list["HistoricoStatus"]] = relationship(
        back_populates="animal", order_by="HistoricoStatus.id.desc()",
        cascade="all, delete-orphan", passive_deletes=True,
    )


class Foto(Base):
    __tablename__ = "fotos"

    id: Mapped[int] = mapped_column(primary_key=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animais.id", ondelete="CASCADE"), index=True)
    arquivo: Mapped[str] = mapped_column(String(255))      # caminho relativo dentro de uploads/
    miniatura: Mapped[str] = mapped_column(String(255))
    ordem: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))  # a de menor ordem é a foto principal
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    animal: Mapped[Animal] = relationship(back_populates="fotos")


class HistoricoStatus(Base):
    __tablename__ = "historico_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animais.id", ondelete="CASCADE"), index=True)
    status_anterior: Mapped[StatusAnimal | None] = mapped_column(_enum(StatusAnimal))
    status_novo: Mapped[StatusAnimal] = mapped_column(_enum(StatusAnimal))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    observacao: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    animal: Mapped[Animal] = relationship(back_populates="historico")
    usuario: Mapped[Usuario | None] = relationship()


class Configuracao(Base):
    """Dados do abrigo editáveis pelo admin (endereço, WhatsApp, horários...)."""
    __tablename__ = "configuracoes"

    chave: Mapped[str] = mapped_column(String(50), primary_key=True)
    valor: Mapped[str] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=_ATUALIZADO_EM, onupdate=func.now()
    )
