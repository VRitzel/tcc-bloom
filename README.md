# Classificação cognitiva de materiais didáticos de programação

Ferramenta desenvolvida como Trabalho de Conclusão de Curso em Ciência da Computação na
Universidade do Vale do Itajaí (UNIVALI).

A ferramenta recebe materiais didáticos de programação, identifica os tópicos de conteúdo,
classifica cada tópico segundo a Taxonomia de Bloom Revisada (Anderson e Krathwohl, 2001) e
gera um roteiro de aprendizagem com relatório de distribuição cognitiva e lacunas.

Autor: Vinícius Wentz Ritzel
Orientador: Prof. Jhonatan Alves
Novembro de 2026

## Como executar

Requisitos: Python 3.12 e [uv](https://github.com/astral-sh/uv).

```bash
uv sync
uv run python -m spacy download pt_core_news_lg
uv run python main.py
```

O `main.py` abre a interface gráfica em Tkinter. A ferramenta não tem modo de linha de
comando.

Formatos de entrada aceitos: PDF, DOCX, ODT, RTF e TXT.

### Consumo de memória

A leitura de PDF usa a biblioteca Marker, que carrega modelos de aprendizado profundo para
detecção de layout. Três documentos em uma mesma execução atingem pico próximo de 8 GB de
RAM. Em ambientes com memória limitada, prefira entradas em DOCX ou ODT, que passam pelo
pypandoc e consomem poucos megabytes.

## Organização do código

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Monta a janela e faz a navegação entre as telas |
| `analysis.py` | Núcleo do processamento, na classe `CurriculumProcessor` |
| `title_cleaner.py` | Normalização dos títulos extraídos do documento |
| `report_export.py` | Exportação do roteiro em CSV e PDF |
| `frames/` | As quatro telas da interface |
| `experiments/` | Scripts de calibração usados durante a pesquisa |

## Como o processamento funciona

O pipeline tem cinco fases.

1. **Ingestão.** Converte o documento para Markdown. Marker no caminho de PDF, pypandoc nos
   demais formatos.
2. **Coleta.** `collect_topics` localiza os cabeçalhos, delimita o bloco de conteúdo de cada
   um e absorve os subníveis de H3 a H6 no tópico principal anterior.
3. **Consolidação.** `filter_similar_topics` funde tópicos equivalentes pelo índice de
   Jaccard sobre os lemas dos títulos.
4. **Classificação.** `classify_bloom_by_content` calcula a densidade de verbos instrucionais
   por nível cognitivo. A atribuição exige piso mínimo de densidade e margem sobre o segundo
   nível mais frequente. Quando nenhuma das duas condições se cumpre, a ferramenta se abstém
   em vez de atribuir nível com evidência frágil.
5. **Roteiro.** `generate_learning_path` ordena os tópicos por nível cognitivo e, dentro de
   cada nível, pela ordem original do documento. `build_analytics_report` produz a
   distribuição e aponta os níveis ausentes.

A identificação dos verbos usa o modelo `pt_core_news_lg` do spaCy para lematização e
análise sintática. O léxico de verbos instrucionais tem 59 entradas distribuídas pelos seis
níveis da taxonomia.

## Limitações conhecidas

Estas limitações foram observadas durante a validação e estão documentadas no texto do TCC.

- O conversor promove rótulos em negrito à condição de cabeçalho, o que infla a contagem de
  tópicos.
- O descarte de blocos curtos elimina seções legítimas de pouca extensão.
- A consolidação por Jaccard não reconhece títulos equivalentes que não compartilham
  vocabulário.
- A classificação é cega a enunciados interrogativos, frequentes nos níveis de analisar e
  avaliar em português.
- A classificação é insensível ao complemento do verbo. "Definir um conceito" e "definir um
  tipo abstrato de dados" recebem o mesmo tratamento, apesar da diferença de exigência
  cognitiva.
- A ordenação por nível cognitivo não modela dependência conceitual, o que produz roteiros
  em que um tópico aparece antes de outro que ele pressupõe.
- A fase de ingestão permanece acoplada à tela de carregamento, por causa da barra de
  progresso.

## O que não está neste repositório

Os materiais didáticos usados como entrada nos testes são obra de terceiros e por isso não
foram versionados.

Os cadernos preenchidos pelos docentes que participaram da validação contêm dados de pessoas
identificáveis e também ficaram fora do repositório. Os resultados agregados dessa validação
estão no texto do TCC.

Pelo mesmo motivo, os artefatos derivados desses materiais, como os fragmentos selecionados
para a avaliação e as planilhas de classificação, não acompanham o código.

## Convenções

As mensagens de log e os rótulos da interface estão em português. O segundo nível da
taxonomia aparece como `ENTENDER` em todo o código, em acordo com o texto do trabalho. O
produto gerado pela ferramenta chama-se roteiro de aprendizagem.