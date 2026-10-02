"""Descobre na página da Caixa se cada imóvel está ocupado, com cache.

    python scripts/ocupacao.py                # só os que faltam, até 300
    python scripts/ocupacao.py --limite 50
    python scripts/ocupacao.py --revisar 30   # reconfere os mais antigos

POR QUE PRECISA DISTO
---------------------
O arquivo que a Caixa publica para download não traz ocupação — zero
menções em 1.060 imóveis de PE. A informação está na página individual de
cada imóvel, aquela mesma do botão "Página da Caixa" no site.

Ocupação é o item mais caro da conta depois da reforma. Sem ela, o modelo
reserva uma provisão cega em todo imóvel; com ela, o imóvel comprovadamente
vazio sai da provisão e o ocupado entra com aviso na tela.

COMO SE COMPORTA
----------------
Lê uma página por vez, com pausa de pouco mais de um segundo, com
User-Agent que identifica o projeto, e guarda o resultado em
``dados/ocupacao.json`` para nunca pedir duas vezes o mesmo imóvel. É por
isso que existe limite por execução: 1.060 páginas de uma vez levariam uns
20 minutos. A 300 por dia, em quatro dias o acervo inteiro está lido, e daí
em diante só os imóveis novos precisam de consulta.

Se a Caixa recusar, demorar ou mudar a página, o script PARA sem quebrar
nada: quem não foi lido continua como "não informada", que é exatamente o
que o site já mostrava antes. Nada regride.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import date
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from analise.ocupacao import (  # noqa: E402
    INDEFINIDO,
    MORTO,
    NAO_INFORMADA,
    VIVO,
    ler_pagina,
)

CACHE = RAIZ / "dados" / "ocupacao.json"
RADAR = RAIZ / "site" / "dados" / "radar.json"

LIMITE_PADRAO = 300
PAUSA = 1.2            # segundos entre páginas; nada de rajada
ESPERA_RESPOSTA = 20   # segundos até desistir de uma página
FALHAS_SEGUIDAS = 5    # tantas falhas em sequência e o script desiste

# De quantos em quantos dias vale reconferir um imóvel já lido. Ocupação
# quase não muda; existência muda toda hora. Por isso a releitura existe:
# sem ela, um imóvel lido hoje nunca mais seria conferido e continuaria
# no site depois de arrematado.
DIAS_PARA_RECONFERIR = 7

AGENTE = (
    "radar-imoveis-pe/1.0 (projeto pessoal de analise do acervo publico "
    "da Caixa; contato pelo GitHub)"
)
CABECALHOS = {
    "User-Agent": AGENTE,
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def carregar_cache() -> dict:
    """Lê o cache já com as chaves limpas.

    As primeiras leituras foram gravadas com o número sujo da Caixa
    (" 8444411406630 "). O limpar aqui não é cosmético: sem ele, o
    escolher() não reconheceria essas páginas como já lidas e mandaria
    visitar de novo as mesmas 300 — seis minutos e trezentas requisições
    jogadas fora, todo dia.
    """
    if not CACHE.exists():
        return {}
    try:
        dados = json.loads(CACHE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(dados, dict):
        return {}

    limpo, sujas = {}, 0
    for chave, valor in dados.items():
        if str(chave).startswith("_"):
            limpo[chave] = valor       # metadados passam intactos
            continue
        k = str(chave).strip()
        sujas += k != chave
        anterior = limpo.get(k)
        if anterior and (anterior.get("lido_em") or "") >= (
                (valor or {}).get("lido_em") or ""):
            continue
        limpo[k] = valor
    if sujas:
        print(f"  {sujas} chaves antigas limpas (vinham com espaço)")
    return limpo


def gravar_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0),
                     encoding="utf-8")


def consultar(sessao: requests.Session, url: str) -> dict:
    """Lê a página do imóvel e devolve situação + trecho que a embasou."""
    resposta = sessao.get(url, headers=CABECALHOS, timeout=ESPERA_RESPOSTA)
    resposta.raise_for_status()
    # a página da Caixa é latin-1; o requests às vezes adivinha errado
    if not resposta.encoding or resposta.encoding.lower() == "iso-8859-1":
        resposta.encoding = "latin-1"
    return ler_pagina(resposta.text)


def escolher(imoveis: list, cache: dict, limite: int, hoje: str) -> list:
    """Monta a fila da execução, em três camadas de prioridade.

    1. OS MARCADOS COMO FORA DO AR, sempre e todos. São poucos e a
       releitura é o que permite o imóvel RESSUSCITAR: leilão não
       arrematado volta para o acervo, e seria péssimo deixá-lo apagado
       para sempre por causa de uma leitura de ontem.
    2. OS NUNCA LIDOS, do melhor para o pior. É onde a informação nova
       vale mais.
    3. OS LIDOS HÁ MAIS TEMPO, para reconferir se ainda existem.
    """
    com_link = [i for i in imoveis if i.get("link")]
    dentro, vistos = [], set()

    def juntar(candidatos):
        for i in candidatos:
            if len(dentro) >= limite:
                return
            if i["id"] in vistos:
                continue
            vistos.add(i["id"])
            dentro.append(i)

    juntar([i for i in com_link
            if (cache.get(i["id"]) or {}).get("existe") == MORTO])
    juntar(sorted([i for i in com_link if i["id"] not in cache],
                  key=lambda i: -(i.get("nota") or 0)))

    vencidos = [i for i in com_link if i["id"] in cache
                and _dias(cache[i["id"]].get("lido_em", ""), hoje)
                >= DIAS_PARA_RECONFERIR]
    juntar(sorted(vencidos, key=lambda i: cache[i["id"]].get("lido_em", "")))
    return dentro


def _dias(de: str, ate: str) -> int:
    try:
        return (date.fromisoformat(ate) - date.fromisoformat(de)).days
    except (ValueError, TypeError):
        return 10**6      # data estranha conta como vencida há muito tempo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limite", type=int, default=LIMITE_PADRAO,
                        help=f"páginas por execução (padrão {LIMITE_PADRAO})")
    argumentos = parser.parse_args()

    if not RADAR.exists():
        raise SystemExit("Rode antes: python scripts/gerar_dados.py PE")

    imoveis = json.loads(RADAR.read_text(encoding="utf-8"))["imoveis"]
    cache = carregar_cache()
    hoje = date.today().isoformat()
    alvo = escolher(imoveis, cache, argumentos.limite, hoje)

    faltam = sum(1 for i in imoveis if i["id"] not in cache and i.get("link"))
    print(f"{len(cache)} imóveis já lidos, {faltam} ainda sem leitura.")
    if not alvo:
        print("Nada a fazer.")
        return
    print(f"Lendo {len(alvo)} páginas, uma a cada {PAUSA}s "
          f"(~{len(alvo) * PAUSA / 60:.0f} min).")

    sessao = requests.Session()
    contagem = {"ocupado": 0, "desocupado": 0, NAO_INFORMADA: 0}
    vida = {VIVO: 0, MORTO: 0, INDEFINIDO: 0}
    saiu, voltou, amostras = [], [], []
    seguidas = 0

    for n, imovel in enumerate(alvo, start=1):
        try:
            achado = consultar(sessao, imovel["link"])
            seguidas = 0
        except Exception as erro:  # noqa: BLE001
            seguidas += 1
            print(f"  ! {imovel['id']}: {type(erro).__name__}")
            if seguidas >= FALHAS_SEGUIDAS:
                print(f"\n! {FALHAS_SEGUIDAS} falhas seguidas. Parando por "
                      f"aqui — quem não foi lido fica como 'não informada', "
                      f"que é o que o site já mostrava. Nada se perde.")
                break
            time.sleep(PAUSA * 2)
            continue

        anterior = cache.get(imovel["id"]) or {}
        antes, agora = anterior.get("existe"), achado["existe"]

        # INDEFINIDO nunca sobrescreve uma resposta que já foi clara.
        # Página lenta, estranha ou meio carregada não pode apagar nem
        # ressuscitar imóvel nenhum.
        if agora == INDEFINIDO and antes in (VIVO, MORTO):
            agora = antes

        if antes != MORTO and agora == MORTO:
            saiu.append(imovel)
        elif antes == MORTO and agora == VIVO:
            voltou.append(imovel)

        cache[imovel["id"]] = {
            # ocupação lida de página morta não vale nada: guarda a antiga
            "situacao": (anterior.get("situacao", NAO_INFORMADA)
                         if agora == MORTO else achado["situacao"]),
            "trecho": (anterior.get("trecho", "")
                       if agora == MORTO else achado["trecho"]),
            "existe": agora,
            "lido_em": hoje,
        }
        contagem[achado["situacao"]] = contagem.get(achado["situacao"], 0) + 1
        vida[agora] = vida.get(agora, 0) + 1

        # guarda até 8 trechos DIFERENTES do que a página diz perto de
        # "ocupa" quando nada foi concluído. É o que vai dizer, na
        # próxima execução, se as páginas calam ou se os padrões erram.
        a = achado.get("amostra")
        if a and len(amostras) < 8 and a not in amostras:
            amostras.append(a)

        if n % 25 == 0 or n == len(alvo):
            print(f"  {n}/{len(alvo)} · {contagem['ocupado']} ocupados · "
                  f"{contagem['desocupado']} vazios · "
                  f"{vida[MORTO]} fora do ar")
            gravar_cache(cache)

        # jitter pequeno: ritmo exatamente constante é desnecessário e
        # parece mais com robô do que com gente lendo anúncio
        time.sleep(PAUSA + random.uniform(0, 0.4))

    if amostras:
        cache["_amostras"] = {"lido_em": hoje, "trechos": amostras}
    gravar_cache(cache)

    if amostras:
        print(f"\nO QUE AS PÁGINAS DIZEM PERTO DE \"OCUPA\" quando a leitura "
              f"não conclui ({len(amostras)} exemplos diferentes):")
        for a in amostras:
            print(f"   · {a}")
        print("   (se houver aí um padrão que os filtros não pegam, dá para "
              "ensiná-lo em analise/ocupacao.py)")

    total = sum(1 for k in cache if not str(k).startswith("_"))
    reais = [v for k, v in cache.items() if not str(k).startswith("_")]
    ocupados = sum(1 for v in reais if v.get("situacao") == "ocupado")
    vazios = sum(1 for v in reais if v.get("situacao") == "desocupado")
    mortos = sum(1 for v in reais if v.get("existe") == MORTO)
    print(f"\nCache: {total} imóveis · {ocupados} ocupados · "
          f"{vazios} desocupados · {total - ocupados - vazios} sem informação")
    print(f"       {mortos} marcados como fora do ar no site da Caixa")

    if saiu:
        print(f"\nSAÍRAM do site da Caixa nesta execução ({len(saiu)}):")
        for i in saiu[:12]:
            print(f"  {i['id']}  {i['tipo']} · {i['bairro']}, {i['cidade']}"
                  f"  R$ {i['preco']:,.0f}".replace(",", "."))
        if len(saiu) > 12:
            print(f"  ... e mais {len(saiu) - 12}")
    if voltou:
        print(f"\nVOLTARAM ao site da Caixa ({len(voltou)}):")
        for i in voltou[:12]:
            print(f"  {i['id']}  {i['tipo']} · {i['bairro']}, {i['cidade']}")

    print("\nRode scripts/gerar_dados.py de novo para a conta usar isto.")


if __name__ == "__main__":
    main()
