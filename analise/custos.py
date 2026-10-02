"""O que o imóvel custa além do preço anunciado.

Esta é a parte que separa este radar dos outros. O desconto que a Caixa
anuncia compara o preço com a avaliação dela. Só que entre assinar e ter a
chave na mão você ainda paga ITBI, cartório, às vezes comissão de leiloeiro,
quase sempre alguma reforma, e com frequência uma ação para desocupar. O
desconto real é o que sobra depois disso.

Todas as premissas abaixo são estimativas de ordem de grandeza, estão
documentadas com a fonte quando existe, e aparecem na página para quem
quiser conferir. Troque pelos seus números quando tiver orçamento de
verdade.
"""

from __future__ import annotations

from dataclasses import dataclass

# ------------------------------------------------------------ tributos
# Alíquota de ITBI do Recife para transmissão onerosa. Outros municípios de
# PE têm alíquotas próprias (em geral entre 2% e 3%); usamos 3% como teto
# conservador para todos. Fonte: legislação municipal do ITBI, Recife.
ALIQUOTA_ITBI = 0.03

# ------------------------------------------------------- custo de cartório
# Escritura + registro variam com a tabela de custas do TJPE e com a faixa
# de valor. Estes percentuais são a ordem de grandeza praticada; para um
# imóvel específico, peça o cálculo ao cartório.
CUSTO_ESCRITURA = 0.010
CUSTO_REGISTRO = 0.008
CUSTO_CERTIDOES = 800.00

# Comissão do leiloeiro em leilão e licitação (praxe de 5% sobre a
# arrematação). NÃO está no desconto que a Caixa anuncia.
COMISSAO_LEILOEIRO = 0.05

# ------------------------------------------------------------- reforma
# Custo por m² quando a Caixa declara "necessita reforma", e o acerto
# mínimo no restante (pintura, louça, elétrica aparente).
REFORMA_M2_DECLARADA = 1_200.00
REFORMA_M2_MINIMA = 450.00

# POR QUE EXISTE UM TETO AQUI
# ---------------------------
# Reforma calculada só por m² quebra em imóvel barato. Uma casa de 58 m² a
# R$ 1.000/m² custa R$ 58 mil; R$ 450/m² de "banho de loja" daria R$ 26 mil,
# ou 45% do valor do imóvel. Ninguém gasta 45% do valor de uma casa para dar
# um acerto básico — o orçamento de obra acompanha o padrão do imóvel, não
# só a metragem. Sem este teto, o modelo condena sistematicamente o imóvel
# barato e o interior, que é exatamente onde os descontos aparecem.
TETO_REFORMA_DECLARADA = 0.30      # % do preço
TETO_REFORMA_MINIMA = 0.12

# -------------------------------------------------------- desocupação
# A lista da Caixa NÃO informa se o imóvel está ocupado (conferido: zero
# menções em 1.060 registros de PE e 18.266 do Brasil). Tratar "não
# informado" como desocupado seria assumir o melhor cenário justamente no
# item mais caro. Então entra provisão, marcada como tal.
DESOCUPACAO_PCT = 0.08
DESOCUPACAO_MINIMO = 15_000.00
# O piso não escala para baixo de propósito: advogado e custas judiciais
# custam quase o mesmo num imóvel de R$ 40 mil e num de R$ 400 mil. É por
# isso que imóvel barato E ocupado raramente compensa — e o número precisa
# mostrar isso, não esconder.


@dataclass
class Custos:
    """A conta completa de um imóvel."""

    preco: float
    reforma: float
    desocupacao: float
    comissao: float
    itbi: float
    cartorio: float

    @property
    def custo_real(self) -> float:
        """O que o imóvel custa de verdade: preço + o que falta gastar nele.

        É contra ESTE número, não contra o preço, que qualquer referência de
        valor deve ser comparada.
        """
        return self.preco + self.reforma + self.desocupacao + self.comissao

    @property
    def desembolso(self) -> float:
        """O cheque que sai da conta: custo real + tributo + cartório."""
        return self.custo_real + self.itbi + self.cartorio

    def como_dict(self) -> dict:
        return {
            "preco": round(self.preco, 2),
            "reforma": round(self.reforma, 2),
            "desocupacao": round(self.desocupacao, 2),
            "comissao": round(self.comissao, 2),
            "itbi": round(self.itbi, 2),
            "cartorio": round(self.cartorio, 2),
            "custo_real": round(self.custo_real, 2),
            "desembolso": round(self.desembolso, 2),
        }


def estimar_reforma(preco: float, area: float, tipo: str,
                    declarada: bool) -> float:
    """Reforma por m², limitada a um teto percentual do preço."""
    if tipo == "Terreno" or area <= 0 or preco <= 0:
        return 0.0
    por_m2 = REFORMA_M2_DECLARADA if declarada else REFORMA_M2_MINIMA
    teto = TETO_REFORMA_DECLARADA if declarada else TETO_REFORMA_MINIMA
    return round(min(area * por_m2, preco * teto), 2)


def estimar_desocupacao(preco: float, ocupado: bool,
                        desconhecido: bool) -> float:
    """Provisão para desocupar. Zero só quando a Caixa diz que está vago."""
    if not (ocupado or desconhecido):
        return 0.0
    return round(max(preco * DESOCUPACAO_PCT, DESOCUPACAO_MINIMO), 2)


def calcular(preco: float, area: float, tipo: str, *, reforma_declarada: bool,
             ocupado: bool, ocupacao_desconhecida: bool,
             leilao: bool) -> Custos:
    """Monta a conta completa de um imóvel da lista."""
    return Custos(
        preco=preco,
        reforma=estimar_reforma(preco, area, tipo, reforma_declarada),
        desocupacao=estimar_desocupacao(preco, ocupado, ocupacao_desconhecida),
        comissao=round(preco * COMISSAO_LEILOEIRO, 2) if leilao else 0.0,
        itbi=round(preco * ALIQUOTA_ITBI, 2),
        cartorio=round(preco * (CUSTO_ESCRITURA + CUSTO_REGISTRO)
                       + CUSTO_CERTIDOES, 2),
    )


# As premissas vão para a página, para quem quiser conferir de onde saiu
# cada número. A ordem é a que faz sentido ler.
PREMISSAS = [
    ("ITBI", f"{ALIQUOTA_ITBI:.0%} do preço",
     "Alíquota do Recife para transmissão onerosa. Outros municípios de PE "
     "variam, em geral entre 2% e 3% — usamos 3% como teto conservador."),
    ("Escritura e registro",
     f"{CUSTO_ESCRITURA + CUSTO_REGISTRO:.1%} + R$ {CUSTO_CERTIDOES:,.0f}"
     .replace(",", "."),
     "Ordem de grandeza da tabela de custas do TJPE, mais certidões e "
     "despachante. Peça o cálculo exato ao cartório."),
    ("Comissão do leiloeiro", f"{COMISSAO_LEILOEIRO:.0%} da arrematação",
     "Só em Leilão e Licitação. Não está no desconto que a Caixa anuncia."),
    ("Reforma declarada",
     f"R$ {REFORMA_M2_DECLARADA:,.0f}/m², até {TETO_REFORMA_DECLARADA:.0%} "
     f"do preço".replace(",", "."),
     "Quando a descrição da Caixa diz que o imóvel necessita reforma."),
    ("Acerto mínimo",
     f"R$ {REFORMA_M2_MINIMA:,.0f}/m², até {TETO_REFORMA_MINIMA:.0%} do preço"
     .replace(",", "."),
     "Pintura, louça e elétrica nos demais. Zero em terreno. O teto existe "
     "porque orçamento de obra acompanha o padrão do imóvel, não só a "
     "metragem — sem ele, o modelo condena todo imóvel barato."),
    ("Provisão de desocupação",
     f"{DESOCUPACAO_PCT:.0%} do preço, mínimo R$ "
     f"{DESOCUPACAO_MINIMO:,.0f}".replace(",", "."),
     "A lista da Caixa NÃO informa ocupação — conferido, zero menções em "
     "1.060 imóveis de PE. Confira na página do imóvel e no edital. O piso "
     "não diminui em imóvel barato porque advogado e custas custam o mesmo."),
]
