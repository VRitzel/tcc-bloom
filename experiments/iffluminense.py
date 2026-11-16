"""
Numeros reais para o capitulo de Testes Preliminares (apostila IFFluminense).

PASSOS:
1. Baixe a apostila (link no chat) e processe-a com a sua ferramenta (main.py),
   de modo que ela apareca como uma pasta dentro de files/.
2. Rode, na raiz do projeto, no venv que ja tem o pt_core_news_lg:
       uv run python experiments/iffluminense.py
3. Cole TODA a saida de volta no chat.

Observacao: a parte 2 (similaridade da tabela da Fase 4) NAO depende do material,
pois calcula a similaridade de cosseno das strings exatas que estao no capitulo.
As partes 1 (agrupamento) e 3 (Bloom) usam o material processado em files/.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import CurriculumProcessor, HEADING_LOCATOR

proc = CurriculumProcessor("pt_core_news_lg")
nlp = proc.nlp

# ---------- 1) AGRUPAMENTO (usa o material processado em files/) ----------
print("=" * 64)
print("1) AGRUPAMENTO POR MATERIAL")
print("=" * 64)
all_topics = []
md_files = sorted(glob.glob("files/*/*.md"))
if not md_files:
    print("  files/ vazia. Processe a apostila com o main.py antes de rodar isto.")
for md in md_files:
    text = open(md, encoding="utf-8").read()
    n_head = len(HEADING_LOCATOR.findall(text))
    topics = proc.collect_topics(md)
    mains = [t for t in topics if t["markdown_level"] in (1, 2)]
    nome = os.path.basename(os.path.dirname(md))
    print(f"\n[{nome}]")
    print(f"  cabecalhos detectados     : {n_head}")
    print(f"  topicos principais (H1/H2): {len(mains)}")
    print(f"  subtopicos H3+ absorvidos : {n_head - len(topics)}")
    all_topics.extend(topics)

# ---------- 2) SIMILARIDADE (tabela da Fase 4, independe do material) ----------
print("\n" + "=" * 64)
print("2) SIMILARIDADE DOS PARES DO CAPITULO (Fase 4)")
print("=" * 64)
pares_tabela = [
    ("Estruturas de Repetição", "Estrutura de Repetição FOR"),
    ("Algoritmos", "Módulo 1 - Algoritmos"),
    ("Atividades Operadores", "Atividades Tipos de Dados"),
    ("Estrutura de Seleção IF/ELSE", "Estrutura de Repetição WHILE"),
]
limiares = [0.70, 0.80, 0.85, 0.90]
print(f"{'sim':>6}  " + "  ".join(f"{l:.2f}" for l in limiares) + "   par")
for a, b in pares_tabela:
    da, db = nlp(a), nlp(b)
    if da.has_vector and db.has_vector:
        s = da.similarity(db)
        marcas = "  ".join("funde" if s > l else " nao " for l in limiares)
        print(f"{s:6.3f}  {marcas}   {a!r} x {b!r}")
    else:
        print(f"  sem vetor   {a!r} x {b!r}")

# ---------- 3) BLOOM (usa o material processado em files/) ----------
print("\n" + "=" * 64)
print("3) DENSIDADE DE BLOOM DOS TOPICOS DO EXEMPLO")
print("=" * 64)
alvos = ["tipos de dados", "estruturas de seleção", "estrutura de seleção"]
achou = False
for t in all_topics:
    if any(alvo in t["title"].lower() for alvo in alvos):
        achou = True
        bl = proc.classify_bloom_by_content(t["content_block"])
        if bl and max(bl.values()) > 0:
            sug = max(bl, key=bl.get)
            print(f"\n  {t['title']!r}")
            print(f"    nivel sugerido: {sug} ({bl[sug]:.2f}%)")
            print(f"    densidades por nivel: {bl}")
        else:
            print(f"\n  {t['title']!r}: nenhum verbo-chave detectado  {bl}")
if not achou:
    print("  Nenhum topico com 'Tipos de Dados' ou 'Estruturas de Selecao' encontrado.")
    print("  (Pode ser que a conversao tenha gerado titulos diferentes; me avise.)")