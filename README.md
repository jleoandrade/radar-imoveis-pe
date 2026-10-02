# Radar Imóveis Pernambuco

Site estático que lê a lista oficial de imóveis retomados da **Caixa
Econômica Federal** em Pernambuco, calcula **quanto de desconto realmente
sobra** depois de todo o custo, e se atualiza sozinho todo dia às 06:10.

**→ [jleoandrade.github.io/radar-imoveis-pe](https://jleoandrade.github.io/radar-imoveis-pe/)**

Para instalar ou reconstruir sem saber nada de programação, leia o
**[GUIA.md](GUIA.md)**.

---

## O problema

Todo radar de imóveis da Caixa mostra o **desconto anunciado**: preço
dividido pela avaliação do banco. Esse número ignora tudo que você ainda
vai gastar depois de comprar.

Aqui o **desconto real** compara a avaliação com o custo que você de fato
desembolsa para ter o imóvel pronto:

```
custo real    = preço + reforma + provisão de desocupação + comissão
desconto real = 1 − (custo real ÷ avaliação da Caixa)
```

Na lista de PE de 01/10/2026, com 1.058 imóveis:

| | |
|---|---|
| Desconto anunciado, mediana | **45,0%** |
| Desconto real, mediana | **28,0%** |

Dezessete pontos percentuais. É a diferença entre uma planilha bonita e
uma conta que fecha.

---

## O que ele faz que os outros não fazem

**Veta imóvel pedido acima da avaliação da própria Caixa.** São 42 dos
1.058, todos Leilão SFI — ali o preço mínimo é o saldo da dívida do antigo
mutuário, não uma avaliação de venda. Saem com nota zero, nos dois
caminhos de classificação.

**Confere, uma a uma, se o imóvel ainda existe.** A lista é a fotografia
do dia em que foi gerada; entre ela e agora, imóvel é arrematado e leilão
encerra. A mesma visita que lê a ocupação confere se a página ainda
responde. Quem a Caixa negar existir sai do site — mas continua no
histórico, para voltar com a data original se o leilão não arrematar.

**Só remove com negação explícita.** A regra é de três estados: vivo,
morto e indefinido. Erro de rede, lentidão ou página estranha devolvem
indefinido e não tiram ninguém. Apagar um imóvel bom por causa de um
soluço de rede seria pior do que mostrar um que acabou de sair.

**Trata a ocupação como o que ela é: desconhecida.** O arquivo que a Caixa
publica não informa ocupação — conferido, zero menções em 1.058 registros.
A página de cada imóvel às vezes informa, e o robô vai lá ver. Mas em 898
das 900 páginas já conferidas a palavra sequer aparece. Por isso a conta
reserva provisão de desocupação em todo imóvel não confirmado como vazio:
tratar "não sei" como "vazio" é assumir o melhor cenário no item mais
caro, e é o que faz toda lista de leilão parecer barata no papel.

**Explica como se desocupa.** Quando o imóvel está ocupado, os detalhes
trazem o roteiro: acordo antes de processo, o que muda conforme a retomada
tenha sido por alienação fiduciária (art. 30 da Lei 9.514/97 — reintegração
concedida liminarmente, 60 dias) ou por execução hipotecária (imissão na
posse, sem liminar automática), prazos e o que costuma travar.

**Marca lotes de unidades idênticas.** Onze apartamentos de 41,79 m² no
mesmo bairro são um empreendimento retomado em bloco, não onze
oportunidades: quem compra um concorre com os outros dez na revenda.

**Compara com os pares.** R$/m² contra a mediana da mesma cidade e
tipologia dentro da própria lista.

**Não publica lista quebrada.** Se a coleta falhar, a execução para antes
de publicar e o site continua mostrando os dados bons da véspera, em vez
de uma página vazia.

---

## Como roda

```
GitHub Actions, todo dia às 06:10 de Brasília
  ├── baixa     venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_PE.csv
  ├── analisa   lê, calcula custos, dá o parecer de cada imóvel
  ├── confere   300 páginas da Caixa: o imóvel existe? está ocupado?
  ├── analisa   de novo, agora com o que descobriu nas páginas
  ├── trava     scripts/conferir.py para tudo se o resultado não fizer sentido
  ├── grava     o histórico de volta no repositório
  └── publica   envia site/ empacotado para o GitHub Pages
```

Sem token, sem senha, sem servidor. A fila das páginas anda 300 por
execução, cobre o acervo em quatro dias e depois reconfere os mais antigos
a cada sete — e os marcados como fora do ar, todo dia, porque é isso que
permite um imóvel voltar.

Para rodar na hora: **Actions → Atualizar radar → Run workflow**. Se você
voltar ao site enquanto roda, uma tarja mostra o andamento e os dados
trocam sozinhos ao terminar, sem recarregar a página e sem perder os
filtros.

> Não há botão de disparo no site, de propósito: disparar exigiria uma
> credencial de escrita guardada dentro da página, que qualquer visitante
> leria no código-fonte.

---

## A página

`site/index.html` é a página inteira, num arquivo só, sem biblioteca
externa nenhuma. Duas abas:

- **Lista** — todos os imóveis com o parecer, filtros, 20 por vez
- **Comparar** — até três imóveis lado a lado, linha por linha

Cada linha traz **Detalhes**, **+ comparar** e **Página da Caixa**. A
ordenação tem os dois sentidos de cada critério.

Ela se adapta ao aparelho: no computador os filtros ficam numa coluna; no
tablet e no celular viram gaveta, com um contador de quantos estão ligados.
Os alvos de toque crescem quando a tela é tocada com o dedo
(`pointer: coarse`) em vez do mouse.

---

## Estrutura

| Pasta | O que tem |
|---|---|
| `site/` | a página e os dados publicados |
| `analise/` | o núcleo: leitor da Caixa, custos, geografia, ocupação, parecer |
| `scripts/` | gerador dos dados, conferência e prévias |
| `dados/` | histórico, leituras das páginas e as datas importadas |
| `.github/workflows/` | a automação diária |

Dois arquivos de `dados/` **não dão para reconstruir**: `historico.json`
guarda quando cada imóvel apareceu e o último preço visto; `ocupacao.json`
guarda o que foi lido em cada página da Caixa. A lista da Caixa é uma
fotografia do dia — se esses dois sumirem, todo imóvel volta a contar como
novidade e o robô tem de revisitar o acervo inteiro.

---

## As premissas, e onde mudá-las

Tudo em `analise/custos.py`, no alto do arquivo, cada constante com um
comentário dizendo de onde veio.

| Premissa | Valor |
|---|---|
| ITBI | 3% do preço |
| Escritura e registro | 1,8% + R$ 800 |
| Comissão do leiloeiro | 5%, só em leilão e licitação |
| Reforma declarada | R$ 1.200/m², até 30% do preço |
| Acerto mínimo | R$ 450/m², até 12% do preço |
| Provisão de desocupação | 8% do preço, mínimo R$ 15.000 |

Os **tetos percentuais da reforma** existem por um motivo: calcular reforma
só por m² quebra em imóvel barato. Uma casa de 58 m² a R$ 1.000/m² custa
R$ 58 mil, e R$ 450/m² de acerto daria R$ 26 mil — 45% do valor do imóvel.
Ninguém gasta isso num banho de loja. Sem o teto, o modelo condena
sistematicamente o imóvel barato e o interior, que é justamente onde os
descontos aparecem — e a conclusão sobre investir no interior de
Pernambuco se inverte conforme esse teto exista ou não.

---

## Rodar no seu computador

Opcional — o site funciona sem isto.

```bash
pip install -r scripts/requirements.txt

python scripts/gerar_dados.py PE              # baixa a lista e gera os dados
python scripts/gerar_dados.py Lista_PE.csv    # ou usa um CSV já baixado
python scripts/ocupacao.py --limite 50        # confere algumas páginas
python scripts/conferir.py                    # valida o resultado
python scripts/gerar_previa.py                # gera uma prévia offline

python -m http.server 8000 --directory site   # e abra localhost:8000
```

---

## Limites

- A referência de valor é a **avaliação da Caixa**, que é número interno do
  banco e não preço praticado. Avaliação de mercado de verdade exige
  transação registrada (ITBI), e isso ainda não está aqui.
- A comparação com pares usa o próprio acervo retomado, não o mercado.
- A ocupação é lida da página por leitura automática de texto. O site
  mostra o trecho original justamente porque pode errar, e o roteiro de
  desocupação é orientação geral, não consultoria jurídica.
- Débitos de condomínio e IPTU, estado real do imóvel e locação averbada
  na matrícula não estão em lugar nenhum do que este projeto lê. Nenhuma
  coluna aqui substitui ler o edital e a matrícula.
- A lista muda toda semana. Imóvel some, preço cai, modalidade troca.

---

## Fonte

Lista pública da Caixa Econômica Federal:
<https://venda-imoveis.caixa.gov.br/sistema/download-lista.asp>

**Projeto independente, sem vínculo oficial com a CAIXA.** O parecer, a
nota e os cálculos de custo são deste projeto, não da Caixa. Confirme
disponibilidade, condições, edital, matrícula, ocupação e débitos nos
canais oficiais antes de qualquer decisão. Nada aqui é recomendação de
investimento.

Código sob licença MIT — veja [LICENSE](LICENSE).
