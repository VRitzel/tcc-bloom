"""
Diagnostico pos-correcao. Determinístico: a saida e a fonte da verdade.
Rode na raiz do projeto:  uv run python experiments/fr.py
Cole a saida inteira de volta no chat.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import CurriculumProcessor, BLOOM_VERBS

proc = CurriculumProcessor("pt_core_news_lg")

all_topics = []
for md in glob.glob("files/*/*.md"):
    all_topics.extend(proc.collect_topics(md))

# 1) SAUDE DA CONSOLIDACAO (Fase 4) com titulos limpos
print("=" * 60)
print("1) CONSOLIDACAO (Fase 4)")
print("=" * 60)
print("Topicos antes da consolidacao :", len(all_topics))
filtrados, mapa = proc.process_curriculum_topics(all_topics, threshold=0.6)
print("Topicos apos a consolidacao   :", len(filtrados))
print("\nTitulos finais que sobraram:")
for t in filtrados:
    print("  -", repr(t["title"]))

# 2) VERBOS REAIS QUE DISPARAM CADA NIVEL (sem chute)
print("\n" + "=" * 60)
print("2) VERBOS CASADOS NO CONTEUDO (amostra de seçoes)")
print("=" * 60)
alvos = ["if/else", "tipos de dados", "estruturas de selecao", "estruturas de seleção"]
for t in all_topics:
    if any(a in t["title"].lower() for a in alvos):
        doc = proc.nlp(t["content_block"].lower())
        casados = []
        for tok in doc:
            for nivel, verbos in BLOOM_VERBS.items():
                if tok.lemma_ in verbos:
                    casados.append(f"{nivel}:{tok.lemma_}(<-{tok.text})")
        print(f"\n  {t['title']!r}")
        print(f"    casados: {casados if casados else 'nenhum'}")