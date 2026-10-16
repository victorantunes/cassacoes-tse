# Eleitos cassados no Brasil por partido e espectro ideológico (1989–2025)

Quantos e quais políticos eleitos perderam o mandato por cassação ou impeachment desde a redemocratização, em quais partidos, e como isso se distribui entre esquerda e direita. O relatório completo está em [`index.html`](index.html) e pode ser publicado no GitHub Pages.

## Resultado em uma linha

Com taxas por mil mandatos eleitos, a direita ampla tem 14,3 casos e a esquerda ampla 11,2 (razão de taxas 1,28; IC 95%: 1,01 a 1,62; Fisher p = 0,038; Cochran-Mantel-Haenszel por cargo p = 0,06). A diferença é pequena e não se sustenta em nenhum cargo isolado. Em números absolutos o MDB (PMDB) lidera, com 111 casos. Leia a seção de limitações antes de citar.

## Fontes

- **TSE**, [Portal de Dados Abertos](https://dadosabertos.tse.jus.br/): arquivos `consulta_cand` (1994 a 2024) e `motivo_cassacao_2024` (licença CC BY).
- **Classificação ideológica:** Bolognesi, Ribeiro e Codato (2023), *Dados* 66(2), [doi:10.1590/dados.2023.66.2.303](https://doi.org/10.1590/dados.2023.66.2.303). O União Brasil, que não está nesse artigo, vem de Bolognesi, Ribeiro, Codato e Silva (2025), *Opinião Pública* 31, [doi:10.1590/1807-0191202531120](https://doi.org/10.1590/1807-0191202531120). Esse artigo também fornece a classificação alternativa (rodada de 2022) usada na análise de robustez. O PRD (fusão de PTB e Patriota, 2023), ausente nos dois artigos, recebe a média simples das notas de PTB e Patriota.
- **Presidentes, governadores, senadores e deputados federais:** listas da Wikipédia, CNN Brasil, IstoÉ Dinheiro, Sedep e Congresso em Foco (ver `data/altos_cargos_cassados.csv`, coluna `fonte`). Não foram conferidas contra as decisões originais.

## Como a contagem é feita

1. **Prefeitos (ciclos 2004–2024):** município com eleição suplementar para prefeito; o prefeito afastado é o eleito no ciclo anterior no mesmo município. Inclui cassações, mas também indeferimento de registro e outras vacâncias.
2. **Vice-prefeitos e vereadores:** somente o marcador de cassação do TSE (existente em 8 eleições). Não entram nas taxas.
3. **Presidentes, governadores, senadores e deputados federais:** lista manual. Presidentes e deputados eleitos antes de 1994 ficam fora das taxas por falta de denominador.
4. **Taxa:** casos divididos por mandatos eleitos (resultado "eleito" nos arquivos do TSE), por mil. Testes: razão de taxas, Fisher exato e Cochran-Mantel-Haenszel por cargo.

## Estrutura

```
index.html                       relatório (GitHub Pages)
data/
  altos_cargos_cassados.csv      lista manual com fonte (entrada)
  altos_cargos_classificados.csv lista com partido agrupado e categoria
  prefeitos_eleicao_suplementar.csv
  eleitos_municipais_marcador_tse.csv
  resultados_por_partido.csv
  resultados.json                todos os números usados na página
scripts/
  partidos.py                    notas, categorias e sucessão de siglas
  01_baixar_tse.py               baixa os arquivos do TSE para ./cache
  02_analise.py                  gera os CSVs e resultados.json
  03_gerar_site.py               gera index.html a partir de modelo.html
  modelo.html                    texto e layout da página
```

## Reproduzir

Requer Python 3.10 ou superior, só biblioteca padrão. Os arquivos do TSE somam cerca de 700 MB.

```bash
python scripts/01_baixar_tse.py cache
python scripts/02_analise.py cache
python scripts/03_gerar_site.py
```

## Publicar no GitHub Pages

Envie o repositório e, em *Settings → Pages*, escolha a branch principal e a pasta raiz. O arquivo `.nojekyll` evita o processamento do Jekyll. A pasta `cache/` está no `.gitignore`.

## Limitações principais

- A eleição suplementar é um indicador aproximado de perda de mandato de prefeito; 148 suplementares ficaram sem partido identificado.
- As listas de alto nível são não oficiais e podem estar incompletas.
- A classificação é de partidos, não de políticos, e vem de surveys de 2018 e 2022.
- Análise exploratória, sem revisão por pares.

## Licença

A definir pelo autor do repositório. Os dados do TSE são CC BY e exigem atribuição.
