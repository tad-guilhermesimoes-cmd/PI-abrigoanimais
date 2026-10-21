"""Gera docs/der.svg (DER em notação pé-de-galinha).

Se o banco mudar, atualize TABELAS abaixo e rode:  python scripts/gerar_der.py docs/der.svg
Para gerar o PNG, abra o SVG no navegador ou use o Edge em modo headless (ver docs/banco-de-dados.md).
"""
import math
import sys
from html import escape

ROW, HEAD, PAD = 22, 34, 8

TABELAS = {
    "usuarios": dict(x=40, y=70, w=380, cols=[
        ("PK", "id", "INT"), ("", "nome", "VARCHAR(100)"), ("UK", "email", "VARCHAR(150)"),
        ("", "senha_hash", "VARCHAR(100)"), ("", "ativo", "TINYINT(1)"),
        ("", "criado_em", "DATETIME"), ("", "atualizado_em", "DATETIME")]),
    "sessoes": dict(x=40, y=360, w=380, cols=[
        ("PK", "token_hash", "VARCHAR(64)"), ("FK", "usuario_id", "INT"),
        ("", "criado_em", "DATETIME"), ("", "expira_em", "DATETIME"), ("", "ip", "VARCHAR(45)?")]),
    "tentativas_login": dict(x=40, y=600, w=380, cols=[
        ("PK", "id", "INT"), ("", "email", "VARCHAR(150)"), ("", "ip", "VARCHAR(45)?"),
        ("", "sucesso", "TINYINT(1)"), ("", "criado_em", "DATETIME")]),
    "historico_status": dict(x=500, y=70, w=380, cols=[
        ("PK", "id", "INT"), ("FK", "animal_id", "INT"), ("", "status_anterior", "ENUM?"),
        ("", "status_novo", "ENUM"), ("FK", "usuario_id", "INT?"), ("", "observacao", "VARCHAR(255)?"),
        ("", "criado_em", "DATETIME")]),
    "fotos": dict(x=500, y=360, w=380, cols=[
        ("PK", "id", "INT"), ("FK", "animal_id", "INT"), ("", "arquivo", "VARCHAR(255)"),
        ("", "miniatura", "VARCHAR(255)"), ("", "ordem", "INT"), ("", "criado_em", "DATETIME")]),
    "configuracoes": dict(x=500, y=600, w=380, cols=[
        ("PK", "chave", "VARCHAR(50)"), ("", "valor", "TEXT"), ("", "atualizado_em", "DATETIME")]),
    "animais": dict(x=960, y=70, w=400, cols=[
        ("PK", "id", "INT"), ("", "nome", "VARCHAR(80)"), ("", "especie", "ENUM"),
        ("", "raca", "VARCHAR(80)"), ("", "sexo", "ENUM"), ("", "porte", "ENUM"),
        ("", "data_nascimento", "DATE?"), ("", "cor", "VARCHAR(60)?"), ("", "comportamento", "TEXT?"),
        ("", "vacinado", "TINYINT(1)"), ("", "vacinas_detalhes", "TEXT?"), ("", "castrado", "TINYINT(1)"),
        ("", "necessidades_especiais", "TEXT?"), ("", "descricao", "TEXT?"), ("", "status", "ENUM"),
        ("", "cliques_interesse", "INT"), ("", "criado_em", "DATETIME"), ("", "atualizado_em", "DATETIME")]),
}

C = dict(borda="#2b4a6f", cab="#2b4a6f", cabtxt="#ffffff", fundo="#ffffff", zebra="#f2f6fa",
         pk="#b7791f", fk="#2f7d4f", uk="#6b46c1", texto="#1f2933", tipo="#5f6b7a", linha="#33475b")


def altura(t):
    return HEAD + len(t["cols"]) * ROW + PAD


def y_col(nome_tab, col):
    t = TABELAS[nome_tab]
    i = [c[1] for c in t["cols"]].index(col)
    return t["y"] + HEAD + PAD / 2 + i * ROW + ROW / 2


def tabela_svg(nome, t):
    x, y, w = t["x"], t["y"], t["w"]
    h = altura(t)
    s = [f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{C["fundo"]}" stroke="{C["borda"]}" stroke-width="1.5"/>',
         f'<path d="M{x},{y + HEAD} v{-HEAD - 0 + 6} q0,-6 6,-6 h{w - 12} q6,0 6,6 v{HEAD - 6} z" fill="{C["cab"]}"/>',
         f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" font-weight="700" font-size="15" fill="{C["cabtxt"]}">{nome}</text>']
    for i, (chave, col, tipo) in enumerate(t["cols"]):
        ry = y + HEAD + PAD / 2 + i * ROW
        if i % 2:
            s.append(f'<rect x="{x + 1}" y="{ry}" width="{w - 2}" height="{ROW}" fill="{C["zebra"]}"/>')
        cy = ry + ROW / 2 + 4.5
        if chave:
            cor = {"PK": C["pk"], "FK": C["fk"], "UK": C["uk"]}[chave]
            s.append(f'<text x="{x + 12}" y="{cy}" font-size="11" font-weight="700" fill="{cor}">{chave}</text>')
        peso = ' font-weight="700"' if chave == "PK" else ""
        sub = ' text-decoration="underline"' if chave == "PK" else ""
        s.append(f'<text x="{x + 44}" y="{cy}" font-size="13" fill="{C["texto"]}"{peso}{sub}>{escape(col)}</text>')
        s.append(f'<text x="{x + w - 12}" y="{cy}" text-anchor="end" font-size="12" font-family="Consolas, monospace" fill="{C["tipo"]}">{escape(tipo)}</text>')
    s.append("</g>")
    return "\n".join(s)


def marcador(px, py, ux, uy, tipo):
    """Desenha a cardinalidade na ponta (px,py) da linha; (ux,uy) aponta para fora da entidade."""
    vx, vy = -uy, ux  # perpendicular
    out = []

    def barra(d):
        cx, cy = px + ux * d, py + uy * d
        out.append(f'<line x1="{cx + vx * 7}" y1="{cy + vy * 7}" x2="{cx - vx * 7}" y2="{cy - vy * 7}"/>')

    def circulo(d):
        out.append(f'<circle cx="{px + ux * d}" cy="{py + uy * d}" r="5" fill="#fff"/>')

    def pe():
        bx, by = px + ux * 16, py + uy * 16
        for k in (-1, 0, 1):
            out.append(f'<line x1="{bx}" y1="{by}" x2="{px + vx * 8 * k}" y2="{py + vy * 8 * k}"/>')

    if tipo == "1":        # exatamente um
        barra(8); barra(14)
    elif tipo == "0..1":   # zero ou um
        barra(8); circulo(20)
    elif tipo == "0..N":   # zero ou muitos
        pe(); circulo(23)
    elif tipo == "1..N":
        pe(); barra(20)
    return "\n".join(out)


def ligacao(pontos, card_a, card_b, rotulo, rot_xy):
    (ax, ay), (bx, by) = pontos[0], pontos[-1]
    (a2x, a2y), (b2x, b2y) = pontos[1], pontos[-2]

    def unit(x1, y1, x2, y2):
        d = math.hypot(x2 - x1, y2 - y1)
        return (x2 - x1) / d, (y2 - y1) / d

    caminho = " ".join(f"{x},{y}" for x, y in pontos)
    s = [f'<polyline points="{caminho}" fill="none"/>',
         marcador(ax, ay, *unit(ax, ay, a2x, a2y), card_a),
         marcador(bx, by, *unit(bx, by, b2x, b2y), card_b)]
    rx, ry = rot_xy
    s.append(f'<text x="{rx}" y="{ry}" font-size="12" font-style="italic" fill="{C["tipo"]}" stroke="none" text-anchor="middle">{rotulo}</text>')
    return "\n".join(s)


def main(destino):
    u, se, h, f, a = (TABELAS[n] for n in ("usuarios", "sessoes", "historico_status", "fotos", "animais"))
    rel = []
    # usuarios 1 ── 0..N sessoes
    xr = u["x"] + 190
    rel.append(ligacao([(xr, u["y"] + altura(u)), (xr, se["y"])], "1", "0..N", "possui", (xr + 34, (u["y"] + altura(u) + se["y"]) / 2 + 4)))
    # usuarios 0..1 ── 0..N historico_status
    yy = y_col("historico_status", "usuario_id")
    rel.append(ligacao([(u["x"] + u["w"], yy), (h["x"], yy)], "0..1", "0..N", "registra", ((u["x"] + u["w"] + h["x"]) / 2, yy - 10)))
    # animais 1 ── 0..N historico_status
    yy = y_col("historico_status", "animal_id")
    rel.append(ligacao([(a["x"], yy), (h["x"] + h["w"], yy)], "1", "0..N", "tem", ((a["x"] + h["x"] + h["w"]) / 2, yy - 10)))
    # animais 1 ── 0..N fotos
    yy = y_col("fotos", "animal_id")
    rel.append(ligacao([(a["x"], yy), (f["x"] + f["w"], yy)], "1", "0..N", "tem", ((a["x"] + f["x"] + f["w"]) / 2, yy - 10)))

    largura, alt = 1400, 800
    leg_y = 720
    legenda = f'''
<g font-size="12" fill="{C["texto"]}">
  <rect x="960" y="{leg_y - 140}" width="400" height="185" rx="6" fill="#fafbfc" stroke="#c9d3dd"/>
  <text x="976" y="{leg_y - 116}" font-weight="700" font-size="13">Legenda</text>
  <text x="976" y="{leg_y - 92}"><tspan fill="{C["pk"]}" font-weight="700">PK</tspan> chave primária</text>
  <text x="1100" y="{leg_y - 92}"><tspan fill="{C["fk"]}" font-weight="700">FK</tspan> chave estrangeira</text>
  <text x="1245" y="{leg_y - 92}"><tspan fill="{C["uk"]}" font-weight="700">UK</tspan> valor único</text>
  <text x="976" y="{leg_y - 70}">Tipo terminado em <tspan font-family="Consolas, monospace">?</tspan> = aceita nulo (NULL)</text>
  <g stroke="{C["linha"]}" stroke-width="1.5" fill="none">
    <line x1="976" y1="{leg_y - 40}" x2="1036" y2="{leg_y - 40}"/>{marcador(1036, leg_y - 40, -1, 0, "1")}
    <line x1="976" y1="{leg_y - 10}" x2="1036" y2="{leg_y - 10}"/>{marcador(1036, leg_y - 10, -1, 0, "0..1")}
    <line x1="976" y1="{leg_y + 20}" x2="1036" y2="{leg_y + 20}"/>{marcador(1036, leg_y + 20, -1, 0, "0..N")}
  </g>
  <text x="1052" y="{leg_y - 36}">exatamente um</text>
  <text x="1052" y="{leg_y - 6}">zero ou um</text>
  <text x="1052" y="{leg_y + 24}">zero ou muitos</text>
</g>'''
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {alt}" width="{largura}" height="{alt}" font-family="Segoe UI, Arial, sans-serif">
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="40" y="40" font-size="22" font-weight="700" fill="{C["texto"]}">AmparaPet — Diagrama Entidade-Relacionamento (DER)</text>
<text x="1360" y="40" font-size="12" text-anchor="end" fill="{C["tipo"]}">MySQL 8.4 · banco amparapet · notação pé-de-galinha</text>
<g stroke="{C["linha"]}" stroke-width="1.5" fill="none">
{chr(10).join(rel)}
</g>
{chr(10).join(tabela_svg(n, t) for n, t in TABELAS.items())}
<text x="230" y="{TABELAS["tentativas_login"]["y"] + altura(TABELAS["tentativas_login"]) + 18}" font-size="11" text-anchor="middle" fill="{C["tipo"]}" font-style="italic">sem relacionamento (registro de segurança)</text>
<text x="690" y="{TABELAS["configuracoes"]["y"] + altura(TABELAS["configuracoes"]) + 18}" font-size="11" text-anchor="middle" fill="{C["tipo"]}" font-style="italic">sem relacionamento (chave-valor do abrigo)</text>
{legenda}
</svg>'''
    open(destino, "w", encoding="utf-8").write(svg)


if __name__ == "__main__":
    main(sys.argv[1])
