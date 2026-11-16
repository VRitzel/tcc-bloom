import spacy
nlp = spacy.load("pt_core_news_lg")

frases = [
    "Escreva um algoritmo que calcule a soma dos elementos de um vetor.",
    "Implemente uma função que inverta um número de três dígitos.",
    "Compare as duas abordagens e justifique sua escolha.",
    "Analise o comportamento do algoritmo para entradas grandes.",
    "O programa usa uma variável para armazenar o resultado.",
    "O computador executa as instruções sequencialmente.",
    "Este algoritmo resolve o problema em tempo linear.",
]

for f in frases:
    doc = nlp(f.lower())
    print("\n" + f)
    for t in doc:
        if t.pos_ in ("VERB", "AUX"):
            subj = [c.lemma_ for c in t.children if c.dep_.startswith("nsubj")]
            print(f"   {t.text:<14} lemma={t.lemma_:<14} dep={t.dep_:<10} subj={subj}")