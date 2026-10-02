"""O parecer de cada imóvel: desconto real, nota, classe e ressalvas.

A lógica é deliberadamente simples e explicável. Cada imóvel responde três
perguntas, nesta ordem:

1. **Tem algum impedimento?** Preço acima da avaliação do próprio banco é
   veto — em Leilão SFI o preço é o saldo da dívida, não um desconto.
2. **Quanto sobra de desconto depois do custo real?** Preço mais reforma,
   provisão de desocupação e comissão, comparado com a avaliação da Caixa.
3. **Está fora da curva em relação aos pares?** R$/m² contra a mediana dos
   imóveis da mesma cidade e tipologia na própria lista.

A nota sai disso, de 0 a 1, e o rótulo diz em uma frase o porquê. Nada aqui
é avaliação de mercado: a referência é o laudo do banco, que é número
interno da Caixa. Avaliação de mercado exige transação registrada, e isso
só existe onde há dado de ITBI.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# pares mínimos na própria lista para a comparação de R$/m² valer
MINIMO_PARES = 5

# faixas de desconto real que definem a classe
FAIXA_ALTO = 0.45
FAIXA_MEDIO = 0.30
FAIXA_BAIXO = 0.15

# lote de unidades quase idênticas que já conta como "empreendimento em bloco"
LOTE_RELEVANTE = 5

CLASSES = {
    "vetado": ("Vetado", "bloqueio"),
    "alto": ("Desconto alto", "positivo"),
    "medio": ("Desconto médio", "neutro"),
    "baixo": ("Desconto baixo", "neutro"),
    "sem": ("Sem desconto", "atencao"),
    "indefinido": ("Sem referência", "atencao"),
}


@dataclass
class Parecer:
    classe: str
    nota: float
    rotulo: str
    cor: str
    desconto_real: float | None
    vs_pares: float | None
    ressalvas: list[str] = field(default_factory=list)


def _faixa(desconto: float) -> tuple[str, float]:
    if desconto >= FAIXA_ALTO:
        return "alto", 0.80
    if desconto >= FAIXA_MEDIO:
        return "medio", 0.60
    if desconto >= FAIXA_BAIXO:
        return "baixo", 0.40
    return "sem", 0.20


def ressalvas_do_imovel(imovel: dict) -> list[str]:
    """O que o comprador precisa saber antes de olhar a nota.

    A ordem importa: o que invalida a leitura vem primeiro.
    """
    avisos = []

    if imovel["preco_acima_da_avaliacao"]:
        avisos.append(
            "Armadilha: o preço pedido está acima da avaliação da própria "
            "Caixa. Em Leilão SFI o preço é o saldo da dívida, não um "
            "desconto — aqui não há desconto nenhum."
        )
    if imovel["lote"] >= LOTE_RELEVANTE:
        avisos.append(
            f"{imovel['lote']} unidades quase idênticas nesta mesma lista: é "
            "empreendimento retomado em bloco, não escassez. Quem compra uma "
            "concorre com as outras na revenda."
        )
    if imovel["ocupacao_desconhecida"]:
        avisos.append(
            "A ocupação não consta no arquivo da Caixa nem foi afirmada na "
            "página do imóvel, então a provisão de desocupação é estimativa "
            "cega. O edital responde — leia antes de dar lance."
        )
    elif imovel["ocupado"]:
        avisos.append(
            "Imóvel ocupado: a desocupação corre por sua conta. Tente "
            "acordo antes de processo; veja o roteiro nos detalhes."
        )
    if imovel["reforma_declarada"]:
        avisos.append("A própria descrição da Caixa diz que necessita reforma.")
    if imovel["leilao"]:
        avisos.append(
            "Leilão ou licitação: há comissão de leiloeiro e o prazo de "
            "pagamento é curto."
        )
    if not imovel["aceita_financiamento"]:
        avisos.append("Não aceita financiamento — precisa do valor à vista.")
    if imovel["tipo"] == "Terreno":
        avisos.append(
            "Terreno: confira muro, posse, acesso e se há ocupação por "
            "terceiros, que não aparece em coluna nenhuma."
        )
    if not imovel["area"]:
        avisos.append("Área não informada na descrição: R$/m² indisponível.")
    if not imovel["na_rmr"]:
        avisos.append(
            "Fora da Região Metropolitana: mercado mais raso e revenda mais "
            "lenta. Confira quem seria o comprador quando você quiser sair."
        )

    return avisos


def avaliar(imovel: dict, custo_real: float,
            referencia_m2: float | None, pares: int) -> Parecer:
    """Monta o parecer de um imóvel."""
    ressalvas = ressalvas_do_imovel(imovel)

    if imovel["preco_acima_da_avaliacao"]:
        return Parecer(
            classe="vetado", nota=0.0, cor="bloqueio",
            rotulo="Preço acima da avaliação da própria Caixa",
            desconto_real=None, vs_pares=None, ressalvas=ressalvas,
        )

    avaliacao = imovel["avaliacao"]
    if not avaliacao:
        return Parecer(
            classe="indefinido", nota=0.0, cor="atencao",
            rotulo="Sem avaliação da Caixa no arquivo — não há como medir "
                   "desconto",
            desconto_real=None, vs_pares=None, ressalvas=ressalvas,
        )

    desconto = 1 - custo_real / avaliacao
    classe, nota = _faixa(desconto)

    partes = [
        f"{desconto:.0%} abaixo da avaliação da Caixa já descontando "
        f"reforma, provisão de desocupação e comissão"
    ]

    vs_pares = None
    if referencia_m2 and imovel["area"]:
        preco_m2 = imovel["preco"] / imovel["area"]
        vs_pares = preco_m2 / referencia_m2 - 1
        lado = "abaixo" if vs_pares < 0 else "acima"
        partes.append(
            f"R$/m² {abs(vs_pares):.0%} {lado} dos {pares} pares da mesma "
            f"cidade e tipologia nesta lista"
        )
        # concordar com os pares reforça o sinal; discordar derruba
        if vs_pares <= -0.15:
            nota = min(1.0, nota + 0.10)
        elif vs_pares >= 0.15:
            nota = max(0.0, nota - 0.15)
    else:
        partes.append("sem pares suficientes nesta lista para comparar R$/m²")

    # cada ressalva de peso tira um pouco da nota: elas são risco, não enfeite
    if imovel["lote"] >= LOTE_RELEVANTE:
        nota = max(0.0, nota - 0.10)
    if not imovel["na_rmr"]:
        nota = max(0.0, nota - 0.05)

    return Parecer(
        classe=classe, nota=round(nota, 3), cor=CLASSES[classe][1],
        rotulo=". ".join(partes) + ".",
        desconto_real=round(desconto, 4),
        vs_pares=round(vs_pares, 4) if vs_pares is not None else None,
        ressalvas=ressalvas,
    )


def referencias_por_cidade(imoveis: list[dict]) -> dict:
    """Mediana de R$/m² por (cidade, tipo) e por cidade, na própria lista.

    Não é preço de mercado: é o preço que a Caixa pede por imóvel parecido.
    Serve para achar quem está fora da curva dentro do próprio acervo.
    """
    baldes: dict[tuple[str, str], list[float]] = {}
    for i in imoveis:
        if not i["area"] or not i["preco"]:
            continue
        m2 = i["preco"] / i["area"]
        baldes.setdefault((i["cidade"], i["tipo"]), []).append(m2)
        baldes.setdefault((i["cidade"], "*"), []).append(m2)

    def mediana(valores: list[float]) -> float:
        ordenado = sorted(valores)
        meio = len(ordenado) // 2
        if len(ordenado) % 2:
            return ordenado[meio]
        return (ordenado[meio - 1] + ordenado[meio]) / 2

    return {chave: (mediana(v), len(v)) for chave, v in baldes.items()}


def referencia_do_imovel(imovel: dict, referencias: dict
                         ) -> tuple[float | None, int]:
    """A melhor referência interna disponível para este imóvel."""
    for tipo in (imovel["tipo"], "*"):
        achado = referencias.get((imovel["cidade"], tipo))
        if not achado:
            continue
        mediana, total = achado
        pares = total - 1          # o próprio imóvel entra na mediana
        if pares >= MINIMO_PARES:
            return mediana, pares
    return None, 0
