"""Gera versões dos layouts com os dados embutidos, para prévia offline.

    python scripts/gerar_previa.py

Cada layout, no site de verdade, busca ``dados/radar.json`` com ``fetch``.
Isso só funciona servido por um servidor web. Para você poder abrir o
arquivo com dois cliques e ver como fica, este script embute um recorte dos
dados direto no HTML, trocando a linha

    const DADOS_EMBUTIDOS = null;

pelo recorte. Sai em ``previa/``, que não vai para o site.
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "site"
DESTINO = RAIZ / "previa"
MARCADOR = "const DADOS_EMBUTIDOS = null;"

# quantos imóveis entram na prévia. A lista inteira deixaria o arquivo
# grande demais para abrir confortável; 160 é mais que o suficiente para
# ver filtros, ordenação e paginação funcionando.
QUANTOS = 160


def recortar(dados: dict) -> dict:
    """Pega os melhores, mais alguns vetados e alguns de interior.

    A prévia precisa mostrar os casos ruins também: um layout que só foi
    visto com imóveis bons esconde como ficam o aviso de armadilha e as
    ressalvas longas.
    """
    imoveis = dados["imoveis"]
    escolhidos, vistos = [], set()

    def juntar(candidatos, quantos):
        for i in candidatos:
            if len(escolhidos) >= QUANTOS or quantos <= 0:
                return
            if i["id"] in vistos:
                continue
            vistos.add(i["id"])
            escolhidos.append(i)
            quantos -= 1

    juntar([i for i in imoveis if i["classe"] == "vetado"], 12)
    juntar([i for i in imoveis if i["lote"] >= 5], 12)
    juntar([i for i in imoveis if not i["na_rmr"]], 40)
    juntar(imoveis, QUANTOS)

    resumo = dict(dados["resumo"])
    resumo["aviso_previa"] = (
        f"Prévia com {len(escolhidos)} dos {resumo['total']} imóveis."
    )
    return {"resumo": resumo, "imoveis": escolhidos}


def main() -> None:
    radar = ORIGEM / "dados" / "radar.json"
    if not radar.exists():
        raise SystemExit(
            "Rode primeiro: python scripts/gerar_dados.py <arquivo.csv>"
        )

    recorte = recortar(json.loads(radar.read_text(encoding="utf-8")))
    embutido = "const DADOS_EMBUTIDOS = " + json.dumps(
        recorte, ensure_ascii=False, separators=(",", ":")) + ";"

    DESTINO.mkdir(exist_ok=True)
    for pagina in sorted(ORIGEM.glob("*.html")):
        html = pagina.read_text(encoding="utf-8")
        if MARCADOR not in html:
            print(f"! {pagina.name} não tem o marcador DADOS_EMBUTIDOS")
            continue
        saida = DESTINO / pagina.name
        saida.write_text(html.replace(MARCADOR, embutido), encoding="utf-8")
        print(f"  {saida.name:28} {saida.stat().st_size / 1024:7.0f} KB")

    print(f"\n{len(recorte['imoveis'])} imóveis na prévia. "
          f"Abra os arquivos de {DESTINO.name}/ no navegador.")


if __name__ == "__main__":
    main()
