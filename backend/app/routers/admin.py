"""Área administrativa (exige login): animais, fotos, painel e dados do abrigo."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import imagens, schemas, servicos
from ..database import get_db
from ..models import Animal, Especie, Foto, HistoricoStatus, Porte, Sexo, StatusAnimal, Usuario
from ..security import usuario_atual
from .publico import filtrar_animais, paginar

router = APIRouter(prefix="/api/admin", tags=["Administração"],
                   dependencies=[Depends(usuario_atual)])

MAX_FOTOS_POR_ANIMAL = 20


def _buscar(db: Session, animal_id: int) -> Animal:
    animal = db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(404, "Animal não encontrado")
    return animal


def _saida(animal: Animal, request: Request, db: Session) -> schemas.AnimalAdmin:
    db.refresh(animal)
    return servicos.animal_admin(animal, str(request.base_url), servicos.obter_config(db))


# ---------- Painel (RF14) ----------

@router.get("/painel", response_model=schemas.Painel, summary="Resumo do painel administrativo")
def painel(db: Session = Depends(get_db)):
    contagem = dict(db.execute(
        select(Animal.status, func.count()).group_by(Animal.status)
    ).all())
    cliques = db.scalar(select(func.coalesce(func.sum(Animal.cliques_interesse), 0)))
    top = db.execute(
        select(Animal.id, Animal.nome, Animal.cliques_interesse)
        .where(Animal.status != StatusAnimal.ADOTADO, Animal.cliques_interesse > 0)
        .order_by(Animal.cliques_interesse.desc()).limit(5)
    ).all()
    return schemas.Painel(
        total=sum(contagem.values()),
        disponiveis=contagem.get(StatusAnimal.DISPONIVEL, 0),
        em_processo=contagem.get(StatusAnimal.EM_PROCESSO, 0),
        adotados=contagem.get(StatusAnimal.ADOTADO, 0),
        cliques_interesse_total=int(cliques),
        mais_procurados=[{"id": i, "nome": n, "cliques": c} for i, n, c in top],
    )


# ---------- Animais (RF01 / RF08 / RF09) ----------

@router.get("/animais", response_model=schemas.ListaAnimaisAdmin,
            summary="Todos os animais, inclusive adotados")
def listar(
    request: Request,
    especie: Especie | None = None,
    porte: list[Porte] = Query(default=[]),
    sexo: Sexo | None = None,
    castrado: bool | None = None,
    vacinado: bool | None = None,
    status: list[StatusAnimal] = Query(default=[]),
    busca: str | None = Query(default=None, max_length=80),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = filtrar_animais(select(Animal), especie, porte, sexo, castrado, vacinado, status, busca)
    total, itens = paginar(db, q, pagina, por_pagina)
    base, cfg = str(request.base_url), servicos.obter_config(db)
    return schemas.ListaAnimaisAdmin(
        total=total, pagina=pagina, por_pagina=por_pagina,
        itens=[servicos.animal_admin(a, base, cfg) for a in itens],
    )


@router.get("/animais/{animal_id}", response_model=schemas.AnimalAdmin)
def detalhe(animal_id: int, request: Request, db: Session = Depends(get_db)):
    return _saida(_buscar(db, animal_id), request, db)


@router.post("/animais", response_model=schemas.AnimalAdmin, status_code=201,
             summary="Cadastrar animal. Depois envie as fotos em /animais/{id}/fotos")
def criar(dados: schemas.AnimalCriar, request: Request,
          usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    animal = Animal(**dados.model_dump(exclude={"status"}))
    servicos.mudar_status(db, animal, dados.status, usuario, "Cadastro")
    db.add(animal)
    db.commit()
    return _saida(animal, request, db)


@router.patch("/animais/{animal_id}", response_model=schemas.AnimalAdmin,
              summary="Editar animal. Envie só os campos que mudaram.")
def editar(animal_id: int, dados: schemas.AnimalAtualizar, request: Request,
           usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    animal = _buscar(db, animal_id)
    campos = dados.model_dump(exclude_unset=True)
    for obrigatorio in ("nome", "especie", "raca", "sexo", "porte", "vacinado", "castrado"):
        if obrigatorio in campos and campos[obrigatorio] is None:
            raise HTTPException(422, f"O campo '{obrigatorio}' não pode ficar vazio")
    novo_status = campos.pop("status", None)
    for campo, valor in campos.items():
        setattr(animal, campo, valor)
    if novo_status:
        servicos.mudar_status(db, animal, novo_status, usuario, "Alterado na edição")
    db.commit()
    return _saida(animal, request, db)


@router.patch("/animais/{animal_id}/status", response_model=schemas.AnimalAdmin,
              summary="Mudar status: Disponível / Em processo / Adotado (RF08). Reativar = voltar para DISPONIVEL.")
def alterar_status(animal_id: int, dados: schemas.AlterarStatus, request: Request,
                   usuario: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    animal = _buscar(db, animal_id)
    servicos.mudar_status(db, animal, dados.status, usuario, dados.observacao)
    db.commit()
    return _saida(animal, request, db)


@router.get("/animais/{animal_id}/historico", response_model=list[schemas.HistoricoSaida],
            summary="Histórico de mudanças de status")
def historico(animal_id: int, db: Session = Depends(get_db)):
    animal = _buscar(db, animal_id)
    return [
        schemas.HistoricoSaida(
            id=h.id, status_anterior=h.status_anterior, status_novo=h.status_novo,
            observacao=h.observacao, usuario_nome=h.usuario.nome if h.usuario else None,
            criado_em=h.criado_em,
        )
        for h in db.scalars(select(HistoricoStatus).where(HistoricoStatus.animal_id == animal.id)
                            .order_by(HistoricoStatus.id.desc()))
    ]


@router.delete("/animais/{animal_id}", status_code=204,
               summary="Excluir animal definitivamente (fotos e histórico juntos). "
                       "A confirmação deve ser feita no front-end.")
def excluir(animal_id: int, db: Session = Depends(get_db)):
    animal = _buscar(db, animal_id)
    db.delete(animal)
    db.commit()
    imagens.remover_pasta_animal(animal_id)


# ---------- Fotos (RF04) ----------

@router.post("/animais/{animal_id}/fotos", response_model=schemas.AnimalAdmin, status_code=201,
             summary="Enviar uma ou mais fotos (JPG, PNG ou WEBP, até 5 MB cada)")
async def enviar_fotos(animal_id: int, request: Request,
                       fotos: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    animal = _buscar(db, animal_id)
    if len(animal.fotos) + len(fotos) > MAX_FOTOS_POR_ANIMAL:
        raise HTTPException(400, f"Cada animal pode ter no máximo {MAX_FOTOS_POR_ANIMAL} fotos")
    proxima_ordem = max((f.ordem for f in animal.fotos), default=-1) + 1
    gravadas: list[str] = []
    try:
        for i, arquivo in enumerate(fotos):
            conteudo = await arquivo.read()
            caminho, mini = imagens.processar_foto(conteudo, arquivo.filename or "foto", animal_id)
            gravadas += [caminho, mini]
            animal.fotos.append(Foto(arquivo=caminho, miniatura=mini, ordem=proxima_ordem + i))
        db.commit()
    except Exception:
        db.rollback()
        imagens.remover_arquivos(*gravadas)  # se uma falhar, nenhuma é salva
        raise
    return _saida(animal, request, db)


@router.put("/animais/{animal_id}/fotos/ordem", response_model=schemas.AnimalAdmin,
            summary="Reorganizar fotos. A primeira da lista vira a foto principal.")
def reordenar_fotos(animal_id: int, dados: schemas.OrdemFotos, request: Request,
                    db: Session = Depends(get_db)):
    animal = _buscar(db, animal_id)
    por_id = {f.id: f for f in animal.fotos}
    if sorted(dados.ids) != sorted(por_id):
        raise HTTPException(400, "Envie todos os IDs das fotos deste animal, cada um uma vez")
    for ordem, foto_id in enumerate(dados.ids):
        por_id[foto_id].ordem = ordem
    db.commit()
    db.expire(animal, ["fotos"])
    return _saida(animal, request, db)


@router.delete("/fotos/{foto_id}", status_code=204, summary="Remover uma foto")
def remover_foto(foto_id: int, db: Session = Depends(get_db)):
    foto = db.get(Foto, foto_id)
    if not foto:
        raise HTTPException(404, "Foto não encontrada")
    arquivos = (foto.arquivo, foto.miniatura)
    db.delete(foto)
    db.commit()
    imagens.remover_arquivos(*arquivos)


# ---------- Dados do abrigo (RF12 / RF13) ----------

@router.get("/abrigo", response_model=schemas.Abrigo)
def ver_abrigo(db: Session = Depends(get_db)):
    return servicos.obter_config(db)


@router.put("/abrigo", response_model=schemas.Abrigo,
            summary="Editar endereço, horários, WhatsApp, textos de 'Como adotar' etc.")
def editar_abrigo(dados: schemas.AbrigoAtualizar, db: Session = Depends(get_db)):
    servicos.salvar_config(db, {k: v for k, v in dados.model_dump(exclude_unset=True).items()
                                if v is not None})
    return servicos.obter_config(db)
