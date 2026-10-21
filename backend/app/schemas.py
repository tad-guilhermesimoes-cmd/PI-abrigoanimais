"""Formatos de entrada e saída da API (validação com Pydantic)."""
from datetime import date, datetime

from typing import Annotated

from pydantic import (
    AfterValidator, BaseModel, BeforeValidator, ConfigDict, EmailStr, Field,
)

from .models import Especie, Porte, Sexo, StatusAnimal


def _strip(v):
    return v.strip() if isinstance(v, str) else v


def _vazio_vira_nulo(v):
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def _nao_futura(v):
    if v and v > date.today():
        raise ValueError("A data de nascimento não pode ser no futuro")
    return v


Texto = Annotated[str, BeforeValidator(_strip)]
TextoOpcional = Annotated[str | None, BeforeValidator(_vazio_vira_nulo)]
DataPassada = Annotated[date | None, AfterValidator(_nao_futura)]


# ---------- Animais ----------

class AnimalCampos(BaseModel):
    nome: Texto = Field(min_length=1, max_length=80)
    especie: Especie
    raca: Texto = Field(default="SRD", min_length=1, max_length=80)
    sexo: Sexo
    porte: Porte
    data_nascimento: DataPassada = Field(
        default=None, description="Data aproximada. Se só souber mês/ano, use o dia 01."
    )
    cor: TextoOpcional = Field(default=None, max_length=60)
    comportamento: TextoOpcional = None
    vacinado: bool = False
    vacinas_detalhes: TextoOpcional = None
    castrado: bool = False
    necessidades_especiais: TextoOpcional = None
    descricao: TextoOpcional = None


class AnimalCriar(AnimalCampos):
    status: StatusAnimal = StatusAnimal.DISPONIVEL


class AnimalAtualizar(BaseModel):
    """Todos os campos opcionais: só os enviados são alterados."""
    nome: Texto | None = Field(default=None, min_length=1, max_length=80)
    especie: Especie | None = None
    raca: Texto | None = Field(default=None, min_length=1, max_length=80)
    sexo: Sexo | None = None
    porte: Porte | None = None
    data_nascimento: DataPassada = None
    cor: TextoOpcional = Field(default=None, max_length=60)
    comportamento: TextoOpcional = None
    vacinado: bool | None = None
    vacinas_detalhes: TextoOpcional = None
    castrado: bool | None = None
    necessidades_especiais: TextoOpcional = None
    descricao: TextoOpcional = None
    status: StatusAnimal | None = None


class AlterarStatus(BaseModel):
    status: StatusAnimal
    observacao: str | None = Field(default=None, max_length=255)


class FotoSaida(BaseModel):
    id: int
    url: str
    miniatura_url: str
    ordem: int


class AnimalResumo(BaseModel):
    """Card da vitrine (RF02)."""
    id: int
    nome: str
    especie: Especie
    raca: str
    sexo: Sexo
    porte: Porte
    idade: str | None
    castrado: bool
    vacinado: bool
    status: StatusAnimal
    foto_principal: FotoSaida | None


class LinksAnimal(BaseModel):
    pagina: str                 # link copiável da página do animal (RF11)
    whatsapp_interesse: str | None  # conversa com o abrigo já com o animal identificado (RF06)
    compartilhar_whatsapp: str  # compartilhar o animal com amigos (RF11)


class AnimalDetalhe(AnimalCampos):
    """Página do animal (RF03)."""
    id: int
    idade: str | None
    status: StatusAnimal
    fotos: list[FotoSaida]
    links: LinksAnimal
    criado_em: datetime
    atualizado_em: datetime


class AnimalAdmin(AnimalDetalhe):
    cliques_interesse: int


class Pagina(BaseModel):
    total: int
    pagina: int
    por_pagina: int


class ListaAnimais(Pagina):
    itens: list[AnimalResumo]


class ListaAnimaisAdmin(Pagina):
    itens: list[AnimalAdmin]


class HistoricoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status_anterior: StatusAnimal | None
    status_novo: StatusAnimal
    observacao: str | None
    usuario_nome: str | None
    criado_em: datetime


class OrdemFotos(BaseModel):
    ids: list[int] = Field(description="IDs das fotos na nova ordem. A primeira vira a foto principal.")


class InteresseSaida(BaseModel):
    whatsapp_url: str | None


# ---------- Painel (RF14) ----------

class Painel(BaseModel):
    total: int
    disponiveis: int
    em_processo: int
    adotados: int
    cliques_interesse_total: int
    mais_procurados: list[dict]


# ---------- Autenticação e usuários ----------

class LoginEntrada(BaseModel):
    email: str = Field(max_length=150)  # sem validar formato: basta bater com o cadastro
    senha: str = Field(max_length=200)


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: str
    ativo: bool
    criado_em: datetime


class LoginSaida(BaseModel):
    token: str
    expira_em: datetime
    usuario: UsuarioSaida


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)


class UsuarioAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    senha: str | None = Field(default=None, min_length=8, max_length=72)
    ativo: bool | None = None


class TrocarSenha(BaseModel):
    senha_atual: str
    senha_nova: str = Field(min_length=8, max_length=72)


# ---------- Dados do abrigo (RF12 / RF13) ----------

class Abrigo(BaseModel):
    nome_abrigo: str
    endereco: str
    cidade: str
    horario_funcionamento: str
    whatsapp: str = Field(description="Só números, com DDI e DDD. Ex.: 5543999998888")
    instagram: str
    como_adotar: str
    documentos_adocao: str
    mensagem_interesse: str = Field(
        description="Texto enviado no WhatsApp. Variáveis: {nome}, {id}, {link}"
    )
    url_pagina_animal: str = Field(
        description="Endereço da página do animal no front-end. Use {id} no lugar do código."
    )


class AbrigoAtualizar(BaseModel):
    nome_abrigo: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    horario_funcionamento: str | None = None
    whatsapp: str | None = Field(default=None, pattern=r"^\d{12,13}$|^$")
    instagram: str | None = None
    como_adotar: str | None = None
    documentos_adocao: str | None = None
    mensagem_interesse: str | None = None
    url_pagina_animal: str | None = None
