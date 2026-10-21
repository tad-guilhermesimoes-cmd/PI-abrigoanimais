"""Processamento das fotos: validação, compressão e miniatura (RF04 / RNF04 / RNF07)."""
import io
import shutil
import uuid

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

from . import config

FORMATOS_ACEITOS = {"JPEG", "PNG", "WEBP"}

# Evita "bombas" de descompressão (imagens gigantes em poucos bytes)
Image.MAX_IMAGE_PIXELS = 50_000_000


def _pasta_animal(animal_id: int):
    return config.UPLOAD_DIR / "animais" / str(animal_id)


def _salvar_webp(img: Image.Image, lado_max: int, destino) -> None:
    copia = img.copy()
    copia.thumbnail((lado_max, lado_max), Image.Resampling.LANCZOS)  # mantém proporção, sem distorcer
    copia.save(destino, "WEBP", quality=82, method=4)


def processar_foto(conteudo: bytes, nome_original: str, animal_id: int) -> tuple[str, str]:
    """Valida a imagem e grava a versão grande e a miniatura em WEBP.
    Retorna os caminhos relativos (dentro de uploads/) da foto e da miniatura."""
    limite = config.FOTO_TAMANHO_MAX_MB * 1024 * 1024
    if len(conteudo) > limite:
        raise HTTPException(413, f"'{nome_original}' passa de {config.FOTO_TAMANHO_MAX_MB} MB")
    try:
        img = Image.open(io.BytesIO(conteudo))
        formato = img.format
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(415, f"'{nome_original}' não é uma imagem válida")
    if formato not in FORMATOS_ACEITOS:
        raise HTTPException(415, f"'{nome_original}': formato não aceito. Use JPG, PNG ou WEBP")

    img = ImageOps.exif_transpose(img)  # corrige fotos de celular deitadas
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")

    pasta = _pasta_animal(animal_id)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = uuid.uuid4().hex
    _salvar_webp(img, config.FOTO_LADO_MAX, pasta / f"{nome}.webp")
    _salvar_webp(img, config.MINIATURA_LADO_MAX, pasta / f"{nome}_mini.webp")
    base = f"animais/{animal_id}"
    return f"{base}/{nome}.webp", f"{base}/{nome}_mini.webp"


def remover_arquivos(*caminhos: str) -> None:
    for c in caminhos:
        (config.UPLOAD_DIR / c).unlink(missing_ok=True)


def remover_pasta_animal(animal_id: int) -> None:
    shutil.rmtree(_pasta_animal(animal_id), ignore_errors=True)
