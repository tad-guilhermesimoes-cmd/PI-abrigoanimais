"""Rotas públicas, sem login: vitrine, página do animal, interesse e dados do abrigo."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from .. import schemas, servicos
from ..database import get_db
from ..models import Animal, Especie, Porte, Sexo, StatusAnimal

router = APIRouter(prefix="/api", tags=["Público"])

STATUS_PUBLICOS = (StatusAnimal.DISPONIVEL, StatusAnimal.EM_PROCESSO)

ROTULOS = {
    "especie": {"CAO": "Cão", "GATO": "Gato"},
    "porte": {"PEQUENO": "Pequeno", "MEDIO": "Médio", "GRANDE": "Grande"},
    "sexo": {"MACHO": "Macho", "FEMEA": "Fêmea"},
    "status": {"DISPONIVEL": "Disponível", "EM_PROCESSO": "Em processo de adoção", "ADOTADO": "Adotado"},
}


def filtrar_animais(q, especie, porte, sexo, castrado, vacinado, status, busca):
    """Filtros da vitrine (RF05), reaproveitados na listagem do admin."""
    if especie:
        q = q.where(Animal.especie == especie)
    if porte:
        q = q.where(Animal.porte.in_(porte))
    if sexo:
        q = q.where(Animal.sexo == sexo)
    if castrado is not None:
        q = q.where(Animal.castrado == castrado)
    if vacinado is not None:
        q = q.where(Animal.vacinado == vacinado)
    if status:
        q = q.where(Animal.status.in_(status))
    if busca:
        termo = f"%{busca.strip()}%"
        q = q.where(or_(Animal.nome.like(termo), Animal.raca.like(termo), Animal.cor.like(termo)))
    return q


def paginar(db: Session, q, pagina: int, por_pagina: int):
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    itens = db.scalars(
        q.options(selectinload(Animal.fotos))
        .order_by(Animal.criado_em.desc(), Animal.id.desc())
        .offset((pagina - 1) * por_pagina).limit(por_pagina)
    ).all()
    return total, itens


@router.get("/opcoes", summary="Valores aceitos nos campos e filtros, com rótulos em português")
def opcoes():
    return ROTULOS


@router.get("/abrigo", response_model=schemas.Abrigo,
            summary="Dados do abrigo: endereço, horários, WhatsApp, como adotar (RF12/RF13)")
def abrigo(db: Session = Depends(get_db)):
    return servicos.obter_config(db)


@router.get("/animais", response_model=schemas.ListaAnimais,
            summary="Vitrine pública com filtros (RF02/RF05). Animais adotados não aparecem.")
def listar(
    request: Request,
    especie: Especie | None = None,
    porte: list[Porte] = Query(default=[]),
    sexo: Sexo | None = None,
    castrado: bool | None = None,
    vacinado: bool | None = None,
    status: list[StatusAnimal] = Query(default=[], description="DISPONIVEL e/ou EM_PROCESSO"),
    busca: str | None = Query(default=None, max_length=80, description="Nome, raça ou cor"),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    status = [s for s in status if s in STATUS_PUBLICOS] or list(STATUS_PUBLICOS)
    q = filtrar_animais(select(Animal), especie, porte, sexo, castrado, vacinado, status, busca)
    total, itens = paginar(db, q, pagina, por_pagina)
    base = str(request.base_url)
    return schemas.ListaAnimais(
        total=total, pagina=pagina, por_pagina=por_pagina,
        itens=[servicos.animal_resumo(a, base) for a in itens],
    )


@router.get("/animais/{animal_id}", response_model=schemas.AnimalDetalhe,
            summary="Página detalhada do animal (RF03)")
def detalhe(animal_id: int, request: Request, db: Session = Depends(get_db)):
    animal = db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(404, "Animal não encontrado")
    return servicos.animal_detalhe(animal, str(request.base_url), servicos.obter_config(db))


@router.post("/animais/{animal_id}/interesse", response_model=schemas.InteresseSaida,
             summary="Registra o clique em 'Tenho interesse' e devolve o link do WhatsApp (RF06)")
def interesse(animal_id: int, db: Session = Depends(get_db)):
    animal = db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(404, "Animal não encontrado")
    if animal.status == StatusAnimal.ADOTADO:
        raise HTTPException(409, "Este animal já foi adotado")
    db.execute(update(Animal).where(Animal.id == animal_id)
               .values(cliques_interesse=Animal.cliques_interesse + 1,
                       atualizado_em=Animal.atualizado_em))  # não mexe na data de atualização
    db.commit()
    links = servicos.links_animal(animal, servicos.obter_config(db))
    return schemas.InteresseSaida(whatsapp_url=links.whatsapp_interesse)
