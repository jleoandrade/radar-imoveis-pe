"""Catálogo geográfico de Pernambuco usado pelo radar.

Três coisas:

* ``BAIRROS`` — os 93 bairros do Recife com a RPA (Região
  Político-Administrativa) de cada um. Serve para reconhecer o bairro que a
  Caixa escreve em caixa alta e sem acento (``VARZEA`` -> ``Várzea``) e para
  agrupar por região.
* ``RMR`` — os 15 municípios da Região Metropolitana do Recife. É a divisão
  que separa o mercado com liquidez do interior.
* ``NOMES_RPA`` — o nome usual de cada RPA.

Os bairros fora do Recife ficam como a Caixa escreveu: não temos catálogo
dos outros municípios, e inventar seria pior que não ter.
"""

from __future__ import annotations

import unicodedata

# Os 15 municípios da Região Metropolitana do Recife.
# A composição é definida por lei estadual e já mudou várias vezes desde a
# criação pela Lei Complementar federal 14/1973 — confira na Agência
# CONDEPE/FIDEM antes de usar para qualquer coisa formal.
RMR = (
    "Recife", "Olinda", "Jaboatão dos Guararapes", "Paulista", "Camaragibe",
    "São Lourenço da Mata", "Abreu e Lima", "Cabo de Santo Agostinho",
    "Igarassu", "Itapissuma", "Ilha de Itamaracá", "Araçoiaba", "Moreno",
    "Ipojuca", "Goiana",
)

BAIRROS = [
    # ------------------------------------------------ RPA 1 - Centro
    ("Recife",                1, -8.0630, -34.8711, "medio_alto"),
    ("Santo Amaro",           1, -8.0470, -34.8830, "medio"),
    ("Boa Vista",             1, -8.0570, -34.8850, "medio"),
    ("Cabanga",               1, -8.0790, -34.8790, "medio"),
    ("Ilha do Leite",         1, -8.0680, -34.8890, "medio_alto"),
    ("Paissandu",             1, -8.0530, -34.8880, "medio"),
    ("Santo Antônio",         1, -8.0650, -34.8790, "medio"),
    ("São José",              1, -8.0700, -34.8790, "popular"),
    ("Coelhos",               1, -8.0670, -34.8910, "popular"),
    ("Soledade",              1, -8.0560, -34.8880, "medio"),
    ("Ilha Joana Bezerra",    1, -8.0760, -34.8900, "popular"),

    # ------------------------------------------------ RPA 2 - Norte
    ("Arruda",                2, -8.0230, -34.8850, "medio"),
    ("Campina do Barreto",    2, -8.0180, -34.8800, "popular"),
    ("Campo Grande",          2, -8.0270, -34.8790, "medio"),
    ("Encruzilhada",          2, -8.0330, -34.8900, "medio_alto"),
    ("Hipódromo",             2, -8.0300, -34.8880, "medio"),
    ("Peixinhos",             2, -8.0120, -34.8700, "popular"),
    ("Ponto de Parada",       2, -8.0190, -34.8900, "popular"),
    ("Rosarinho",             2, -8.0350, -34.8850, "medio_alto"),
    ("Torreão",               2, -8.0300, -34.8830, "medio"),
    ("Água Fria",             2, -8.0140, -34.8830, "popular"),
    ("Alto Santa Terezinha",  2, -8.0120, -34.8900, "popular"),
    ("Bomba do Hemetério",    2, -8.0150, -34.8940, "popular"),
    ("Cajueiro",              2, -8.0080, -34.8850, "popular"),
    ("Fundão",                2, -8.0110, -34.8760, "popular"),
    ("Porto da Madeira",      2, -8.0060, -34.8780, "popular"),
    ("Beberibe",              2, -8.0000, -34.8880, "popular"),
    ("Dois Unidos",           2, -7.9950, -34.9050, "popular"),
    ("Linha do Tiro",         2, -8.0050, -34.8950, "popular"),

    # ------------------------------------------------ RPA 3 - Noroeste
    ("Aflitos",               3, -8.0380, -34.8970, "alto_padrao"),
    ("Alto do Mandu",         3, -8.0200, -34.9230, "popular"),
    ("Alto José Bonifácio",   3, -8.0100, -34.8980, "popular"),
    ("Alto José do Pinho",    3, -8.0160, -34.9010, "popular"),
    ("Apipucos",              3, -8.0180, -34.9300, "medio_alto"),
    ("Brejo da Guabiraba",    3, -7.9850, -34.9350, "popular"),
    ("Brejo de Beberibe",     3, -7.9900, -34.9250, "popular"),
    ("Casa Amarela",          3, -8.0220, -34.9110, "medio"),
    ("Casa Forte",            3, -8.0330, -34.9150, "alto_padrao"),
    ("Córrego do Jenipapo",   3, -8.0080, -34.9250, "popular"),
    ("Derby",                 3, -8.0530, -34.8950, "alto_padrao"),
    ("Dois Irmãos",           3, -8.0060, -34.9350, "medio"),
    ("Espinheiro",            3, -8.0430, -34.8930, "alto_padrao"),
    ("Graças",                3, -8.0430, -34.9000, "alto_padrao"),
    ("Guabiraba",             3, -7.9800, -34.9450, "popular"),
    ("Jaqueira",              3, -8.0390, -34.9030, "alto_padrao"),
    ("Macaxeira",             3, -8.0130, -34.9190, "popular"),
    ("Mangabeira",            3, -8.0230, -34.9250, "popular"),
    ("Monteiro",              3, -8.0280, -34.9250, "alto_padrao"),
    ("Nova Descoberta",       3, -8.0080, -34.9180, "popular"),
    ("Parnamirim",            3, -8.0340, -34.9080, "alto_padrao"),
    ("Passarinho",            3, -7.9750, -34.9300, "popular"),
    ("Pau Ferro",             3, -7.9900, -34.9400, "popular"),
    ("Poço da Panela",        3, -8.0300, -34.9200, "alto_padrao"),
    ("Santana",               3, -8.0280, -34.9130, "medio_alto"),
    ("Sítio dos Pintos",      3, -8.0000, -34.9280, "popular"),
    ("Tamarineira",           3, -8.0270, -34.9050, "medio_alto"),
    ("Vasco da Gama",         3, -8.0130, -34.9080, "popular"),

    # ------------------------------------------------ RPA 4 - Oeste
    ("Caxangá",               4, -8.0380, -34.9420, "medio"),
    ("Cidade Universitária",  4, -8.0500, -34.9500, "medio"),
    ("Cordeiro",              4, -8.0480, -34.9200, "medio"),
    ("Engenho do Meio",       4, -8.0470, -34.9350, "medio"),
    ("Ilha do Retiro",        4, -8.0600, -34.9050, "medio_alto"),
    ("Iputinga",              4, -8.0380, -34.9250, "medio"),
    ("Madalena",              4, -8.0560, -34.9080, "medio_alto"),
    ("Prado",                 4, -8.0600, -34.9140, "medio"),
    ("Torre",                 4, -8.0480, -34.9110, "medio_alto"),
    ("Torrões",               4, -8.0550, -34.9300, "popular"),
    ("Várzea",                4, -8.0450, -34.9600, "medio"),
    ("Zumbi",                 4, -8.0530, -34.9150, "medio"),

    # ------------------------------------------------ RPA 5 - Sudoeste
    ("Afogados",              5, -8.0750, -34.9050, "medio"),
    ("Areias",                5, -8.0900, -34.9250, "popular"),
    ("Barro",                 5, -8.0900, -34.9450, "popular"),
    ("Bongi",                 5, -8.0700, -34.9280, "popular"),
    ("Caçote",                5, -8.1050, -34.9300, "popular"),
    ("Coqueiral",             5, -8.1000, -34.9250, "popular"),
    ("Curado",                5, -8.0850, -34.9600, "popular"),
    ("Estância",              5, -8.0900, -34.9350, "popular"),
    ("Jardim São Paulo",      5, -8.0950, -34.9200, "medio"),
    ("Jiquiá",                5, -8.0820, -34.9100, "medio"),
    ("Mangueira",             5, -8.0760, -34.9150, "popular"),
    ("Mustardinha",           5, -8.0700, -34.9180, "popular"),
    ("San Martin",            5, -8.0820, -34.9200, "popular"),
    ("Sancho",                5, -8.1000, -34.9450, "popular"),
    ("Tejipió",               5, -8.0950, -34.9500, "popular"),
    ("Totó",                  5, -8.0980, -34.9350, "popular"),

    # ------------------------------------------------ RPA 6 - Sul
    ("Boa Viagem",            6, -8.1200, -34.9000, "alto_padrao"),
    ("Brasília Teimosa",      6, -8.0800, -34.8720, "popular"),
    ("Cohab",                 6, -8.1450, -34.9400, "popular"),
    ("Ibura",                 6, -8.1350, -34.9350, "popular"),
    ("Imbiribeira",           6, -8.1050, -34.9050, "medio"),
    ("Ipsep",                 6, -8.1150, -34.9150, "medio"),
    ("Jordão",                6, -8.1250, -34.9250, "popular"),
    ("Pina",                  6, -8.0880, -34.8830, "alto_padrao"),
]

NOMES_RPA = {
    1: "RPA 1 - Centro",
    2: "RPA 2 - Norte",
    3: "RPA 3 - Noroeste",
    4: "RPA 4 - Oeste",
    5: "RPA 5 - Sudoeste",
    6: "RPA 6 - Sul",
}



def sem_acento(texto: str) -> str:
    """'VARZEA' e 'Várzea' viram a mesma chave de busca."""
    texto = unicodedata.normalize("NFKD", str(texto))
    limpo = "".join(c for c in texto if not unicodedata.combining(c))
    return limpo.lower().strip()


_RMR = {sem_acento(m) for m in RMR}
_BAIRROS = {sem_acento(nome): (nome, r) for nome, r, *_ in BAIRROS}


def na_rmr(cidade: str) -> bool:
    return sem_acento(cidade) in _RMR


def reconhecer_bairro(cidade: str, bairro: str) -> tuple[str, int]:
    """Devolve (nome com acento, RPA). RPA 0 = fora do catálogo do Recife."""
    if sem_acento(cidade) != "recife":
        return bairro.strip().title(), 0

    chave = sem_acento(bairro)
    achado = _BAIRROS.get(chave)
    if achado is None:
        # "Boa Viagem (Setor A)" e variações com sufixo
        for alvo, valor in _BAIRROS.items():
            if chave.startswith(alvo) or alvo.startswith(chave):
                achado = valor
                break
    if achado is None:
        return bairro.strip().title(), 0
    return achado
