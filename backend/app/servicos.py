"""Regras de negócio compartilhadas entre as rotas."""
from datetime import date
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import schemas
from .models import Animal, Configuracao, Foto, HistoricoStatus, StatusAnimal, Usuario

# Valores iniciais dos dados do abrigo. O admin edita depois em /api/admin/abrigo.
CONFIG_PADRAO = {
    "nome_abrigo": "Abrigo Toca de Assis",
    "endereco": "[Preencher: rua, número e bairro do abrigo]",
    "cidade": "Ivaiporã - PR",
    "horario_funcionamento": "[Preencher: ex. Segunda a sábado, das 8h às 17h]",
    "whatsapp": "",
    "instagram": "",
    "como_adotar": (
        "1. Escolha um animal na vitrine e clique em \"Tenho interesse\".\n"
        "2. Converse com o abrigo pelo WhatsApp para tirar dúvidas e agendar uma visita.\n"
        "3. Visite o abrigo e conheça o animal.\n"
        "4. Assine o termo de adoção responsável e leve seu novo amigo para casa."
    ),
    "documentos_adocao": (
        "- Documento com foto (RG ou CNH)\n"
        "- CPF\n"
        "- Comprovante de residência"
    ),
    "mensagem_interesse": (
        "Olá! Tenho interesse em adotar o(a) {nome} (código #{id}) que vi no AmparaPet: {link}"
    ),
    "url_pagina_animal": "http://localhost:8000/teste/animal.html?id={id}",
}


def obter_config(db: Session) -> dict[str, str]:
    valores = dict(CONFIG_PADRAO)
    valores.update({c.chave: c.valor for c in db.scalars(select(Configuracao))})
    return valores


def salvar_config(db: Session, novos: dict[str, str]) -> None:
    for chave, valor in novos.items():
        if chave not in CONFIG_PADRAO:
            continue
        item = db.get(Configuracao, chave)
        if item:
            item.valor = valor
        else:
            db.add(Configuracao(chave=chave, valor=valor))
    db.commit()


def idade_texto(nascimento: date | None, hoje: date | None = None) -> str | None:
    if not nascimento:
        return None
    hoje = hoje or date.today()
    meses = (hoje.year - nascimento.year) * 12 + (hoje.month - nascimento.month)
    if hoje.day < nascimento.day:
        meses -= 1
    if meses < 1:
        return "Menos de 1 mês"
    anos, meses = divmod(meses, 12)
    partes = []
    if anos:
        partes.append(f"{anos} ano" + ("s" if anos > 1 else ""))
    if meses:
        partes.append(f"{meses} " + ("meses" if meses > 1 else "mês"))
    return " e ".join(partes)


def _foto_saida(foto: Foto, base_url: str) -> schemas.FotoSaida:
    return schemas.FotoSaida(
        id=foto.id,
        url=f"{base_url}uploads/{foto.arquivo}",
        miniatura_url=f"{base_url}uploads/{foto.miniatura}",
        ordem=foto.ordem,
    )


def links_animal(animal: Animal, cfg: dict[str, str]) -> schemas.LinksAnimal:
    pagina = cfg["url_pagina_animal"].replace("{id}", str(animal.id))
    whatsapp = None
    if cfg.get("whatsapp"):
        msg = (cfg["mensagem_interesse"]
               .replace("{nome}", animal.nome)
               .replace("{id}", str(animal.id))
               .replace("{link}", pagina))
        whatsapp = f"https://wa.me/{cfg['whatsapp']}?text={quote(msg)}"
    texto_compartilhar = f"Conheça o(a) {animal.nome}, que está esperando um lar no {cfg['nome_abrigo']}! {pagina}"
    return schemas.LinksAnimal(
        pagina=pagina,
        whatsapp_interesse=whatsapp,
        compartilhar_whatsapp=f"https://wa.me/?text={quote(texto_compartilhar)}",
    )


def animal_resumo(animal: Animal, base_url: str) -> schemas.AnimalResumo:
    principal = animal.fotos[0] if animal.fotos else None
    return schemas.AnimalResumo(
        id=animal.id, nome=animal.nome, especie=animal.especie, raca=animal.raca,
        sexo=animal.sexo, porte=animal.porte, idade=idade_texto(animal.data_nascimento),
        castrado=animal.castrado, vacinado=animal.vacinado, status=animal.status,
        foto_principal=_foto_saida(principal, base_url) if principal else None,
    )


def _campos_detalhe(animal: Animal, base_url: str, cfg: dict[str, str]) -> dict:
    return dict(
        id=animal.id, nome=animal.nome, especie=animal.especie, raca=animal.raca,
        sexo=animal.sexo, porte=animal.porte, data_nascimento=animal.data_nascimento,
        idade=idade_texto(animal.data_nascimento), cor=animal.cor,
        comportamento=animal.comportamento, vacinado=animal.vacinado,
        vacinas_detalhes=animal.vacinas_detalhes, castrado=animal.castrado,
        necessidades_especiais=animal.necessidades_especiais, descricao=animal.descricao,
        status=animal.status, fotos=[_foto_saida(f, base_url) for f in animal.fotos],
        links=links_animal(animal, cfg),
        criado_em=animal.criado_em, atualizado_em=animal.atualizado_em,
    )


def animal_detalhe(animal: Animal, base_url: str, cfg: dict[str, str]) -> schemas.AnimalDetalhe:
    return schemas.AnimalDetalhe(**_campos_detalhe(animal, base_url, cfg))


def animal_admin(animal: Animal, base_url: str, cfg: dict[str, str]) -> schemas.AnimalAdmin:
    return schemas.AnimalAdmin(
        **_campos_detalhe(animal, base_url, cfg), cliques_interesse=animal.cliques_interesse
    )


def mudar_status(db: Session, animal: Animal, novo: StatusAnimal,
                 usuario: Usuario | None, observacao: str | None = None) -> None:
    """Altera o status e registra no histórico (RF08 / RF10)."""
    anterior = animal.status if animal.id else None
    if anterior == novo:
        return
    animal.status = novo
    animal.historico.append(HistoricoStatus(
        status_anterior=anterior, status_novo=novo,
        usuario_id=usuario.id if usuario else None, observacao=observacao,
    ))
