"""Confere se o que foi gerado faz sentido antes de publicar.

    python scripts/conferir.py

Existe por um motivo concreto: quando fui olhar o site de um projeto
parecido, ele estava no ar, bonito, e com "Nenhum imóvel encontrado". A
coleta tinha falhado em silêncio e o site continuou publicado, vazio.

Aqui a execução para antes de publicar se qualquer coisa estiver errada. A
falha aparece na aba Actions, em vermelho, e o site continua mostrando os
dados bons da véspera — que é o comportamento certo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "site" / "dados"

# Mínimos deliberadamente folgados: eles pegam "a coleta quebrou", não
# "o acervo encolheu um pouco". PE tinha 1.060 imóveis em 30/09/2026.
MINIMO_IMOVEIS = 100
MINIMO_CIDADES = 10


def conferir() -> list[str]:
    problemas = []

    for nome in ("radar.json", "resumo.json", "feed.xml"):
        if not (DADOS / nome).exists():
            problemas.append(f"{nome} não foi gerado")
    if problemas:
        return problemas

    radar = json.loads((DADOS / "radar.json").read_text(encoding="utf-8"))
    imoveis = radar.get("imoveis", [])
    resumo = radar.get("resumo", {})

    if len(imoveis) < MINIMO_IMOVEIS:
        problemas.append(
            f"só {len(imoveis)} imóveis (esperado ao menos "
            f"{MINIMO_IMOVEIS}) — a lista da Caixa provavelmente mudou de "
            f"formato ou veio incompleta"
        )

    cidades = {i["cidade"] for i in imoveis}
    if len(cidades) < MINIMO_CIDADES:
        problemas.append(
            f"só {len(cidades)} cidades distintas — suspeito de erro de "
            f"leitura das colunas"
        )

    sem_preco = sum(1 for i in imoveis if not i.get("preco"))
    if sem_preco > len(imoveis) * 0.05:
        problemas.append(
            f"{sem_preco} imóveis sem preço — a coluna de preço não foi "
            f"lida direito"
        )

    sem_area = sum(1 for i in imoveis if not i.get("area"))
    if sem_area > len(imoveis) * 0.30:
        problemas.append(
            f"{sem_area} imóveis sem área — a descrição mudou de formato e "
            f"as expressões regulares pararam de casar"
        )

    if not resumo.get("data_da_lista") or resumo["data_da_lista"] == "—":
        problemas.append("a data de geração da lista não foi encontrada")

    desconto = resumo.get("desconto_real_mediano")
    if desconto is None or not (-1 < desconto < 1):
        problemas.append(f"desconto real mediano fora do esperado: {desconto}")

    return problemas


def main() -> None:
    problemas = conferir()
    if problemas:
        print("FALHOU — o site NÃO será publicado:\n")
        for p in problemas:
            print(f"  - {p}")
        print("\nO site continua no ar com os dados da última execução boa.")
        sys.exit(1)

    resumo = json.loads((DADOS / "resumo.json").read_text(encoding="utf-8"))
    print(
        f"OK: {resumo['total']} imóveis, {len(resumo['cidades'])} cidades, "
        f"{resumo['destaques']} destaques. "
        f"Lista da Caixa de {resumo['data_da_lista']}."
    )


if __name__ == "__main__":
    main()
