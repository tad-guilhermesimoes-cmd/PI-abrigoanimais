"""Cria as tabelas, o administrador inicial e os dados padrão do abrigo.

Uso (na pasta backend):
    python -m app.init_db              cria o que estiver faltando
    python -m app.init_db --exemplos   também cadastra animais de exemplo com fotos geradas
"""
import io
import random
import sys
from datetime import date

from PIL import Image, ImageDraw
from sqlalchemy import func, select

from . import config, imagens, security, servicos
from .database import Base, SessionLocal, engine
from .models import Animal, Configuracao, Especie, Foto, Porte, Sexo, StatusAnimal, Usuario


def criar_estrutura() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        existentes = set(db.scalars(select(Configuracao.chave)))
        for chave, valor in servicos.CONFIG_PADRAO.items():
            if chave not in existentes:
                db.add(Configuracao(chave=chave, valor=valor))
        if not db.scalar(select(func.count()).select_from(Usuario)):
            db.add(Usuario(
                nome=config.ADMIN_INICIAL_NOME,
                email=config.ADMIN_INICIAL_EMAIL.lower(),
                senha_hash=security.hash_senha(config.ADMIN_INICIAL_SENHA),
            ))
            print(f"Administrador inicial criado: {config.ADMIN_INICIAL_EMAIL}")
        db.commit()


EXEMPLOS = [
    ("Thor", Especie.CAO, "SRD", Sexo.MACHO, Porte.GRANDE, date(2022, 3, 1), "Caramelo",
     "Brincalhão e muito carinhoso. Se dá bem com outros cães.", True, True, StatusAnimal.DISPONIVEL),
    ("Mel", Especie.CAO, "SRD", Sexo.FEMEA, Porte.MEDIO, date(2023, 8, 1), "Preta e branca",
     "Calma, gosta de colo. Um pouco tímida no começo.", True, True, StatusAnimal.DISPONIVEL),
    ("Pipoca", Especie.CAO, "Poodle", Sexo.FEMEA, Porte.PEQUENO, date(2019, 1, 1), "Branca",
     "Tranquila, ideal para apartamento.", True, False, StatusAnimal.EM_PROCESSO),
    ("Frajola", Especie.GATO, "SRD", Sexo.MACHO, Porte.PEQUENO, date(2024, 5, 1), "Preto e branco",
     "Curioso e brincalhão.", False, False, StatusAnimal.DISPONIVEL),
    ("Luna", Especie.GATO, "Siamês", Sexo.FEMEA, Porte.PEQUENO, date(2021, 10, 1), "Creme",
     "Independente, mas adora carinho no fim do dia.", True, True, StatusAnimal.DISPONIVEL),
    ("Bob", Especie.CAO, "Vira-lata", Sexo.MACHO, Porte.MEDIO, date(2020, 6, 1), "Marrom",
     "Já encontrou um lar!", True, True, StatusAnimal.ADOTADO),
]


def _imagem_exemplo(texto: str) -> bytes:
    cor = tuple(random.randint(90, 220) for _ in range(3))
    img = Image.new("RGB", (1200, 900), cor)
    d = ImageDraw.Draw(img)
    d.ellipse((400, 250, 800, 650), fill=(255, 255, 255))
    d.text((560, 440), texto, fill=(40, 40, 40), font_size=48)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def criar_exemplos() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Animal)):
            print("Já existem animais cadastrados; exemplos não foram criados.")
            return
        admin = db.scalar(select(Usuario).order_by(Usuario.id))
        for (nome, esp, raca, sexo, porte, nasc, cor, comp, vac, cast, status) in EXEMPLOS:
            a = Animal(nome=nome, especie=esp, raca=raca, sexo=sexo, porte=porte,
                       data_nascimento=nasc, cor=cor, comportamento=comp, vacinado=vac,
                       vacinas_detalhes="V10 e antirrábica" if vac and esp == Especie.CAO else None,
                       castrado=cast, descricao=f"{nome} foi resgatado(a) e está pronto(a) para um novo lar.")
            servicos.mudar_status(db, a, StatusAnimal.DISPONIVEL, admin, "Cadastro")
            db.add(a)
            db.flush()
            if status != StatusAnimal.DISPONIVEL:
                servicos.mudar_status(db, a, status, admin, "Exemplo")
            for i in range(2):
                arq, mini = imagens.processar_foto(_imagem_exemplo(f"{nome[0]}{i + 1}"), "exemplo.jpg", a.id)
                a.fotos.append(Foto(arquivo=arq, miniatura=mini, ordem=i))
        db.commit()
        print(f"{len(EXEMPLOS)} animais de exemplo criados.")


if __name__ == "__main__":
    criar_estrutura()
    print("Tabelas e dados padrão OK.")
    if "--exemplos" in sys.argv:
        criar_exemplos()
