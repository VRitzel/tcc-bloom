"""
Testa se a CAIXA ALTA dos titulos esta inflando a similaridade (hipotese OOV).
Roda na raiz:  uv run python experiments/casing.py
Cole a saida no chat.
"""
import spacy
nlp = spacy.load("pt_core_news_lg")

pares = [
    ("TIPOS DE DADOS", "FORMAS DE REPRESENTAÇÃO"),          # NAO deveriam fundir
    ("ESTRUTURAS DE REPETIÇÃO", "FORMAS DE REPRESENTAÇÃO"), # NAO deveriam fundir
    ("ESTRUTURAS DE REPETIÇÃO", "ESTRUTURA DE REPETIÇÃO FOR"),  # DEVERIAM (duplicata real)
    ("TIPOS DE DADOS", "ESTRUTURAS DE SELEÇÃO"),            # NAO deveriam fundir
]

def oov(doc):
    return [t.text for t in doc if t.is_oov]

for a, b in pares:
    print(f"\n{a!r}  x  {b!r}")
    for nome, f in [("ORIGINAL", lambda s: s), ("minusculo", str.lower)]:
        da, db = nlp(f(a)), nlp(f(b))
        print(f"  {nome:9}: sim={da.similarity(db):.3f}  | OOV: {oov(da)} / {oov(db)}")