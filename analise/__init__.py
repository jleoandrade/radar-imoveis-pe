"""Núcleo de análise do Radar de Imóveis PE.

Cada módulo com uma responsabilidade, e nenhum deles depende de interface
gráfica: o pacote roda num GitHub Actions em poucos segundos, com pandas
e requests e mais nada.

* ``caixa``     — lê a lista oficial da Caixa (CSV latin-1, com um campo
                  de texto livre que carrega metade da informação) e
                  devolve uma tabela limpa.
* ``tipos``     — normaliza a tipologia, que a Caixa escreve de várias
                  formas, em cinco categorias.
* ``geografia`` — reconhece bairro do Recife e separa RMR de interior.
* ``custos``    — o que o imóvel custa além do preço: ITBI, cartório,
                  leiloeiro, reforma, provisão de desocupação.
* ``ocupacao``  — lê na página da Caixa se o imóvel existe e se está
                  ocupado, e guarda o roteiro de desocupação.
* ``parecer``   — desconto real, nota, classe e ressalvas.
"""
