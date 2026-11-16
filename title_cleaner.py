"""
Limpeza robusta de titulos. Determinístico: mesma entrada -> mesma saida, sempre.
Sem modelo, sem IA, só regex e a stdlib (html).

Integração no seu analysis.py:
    from title_cleaner import clean_title
    # dentro de CurriculumProcessor:
    def clean_pandoc_metadata(self, title_text):
        return clean_title(title_text)

Auditoria: rode `python title_cleaner.py` e confira os antes/depois.
Adicione seus próprios casos na lista TEST_CASES no fim do arquivo.
"""
import re
import html
import logging

log = logging.getLogger("genese")

# Prefixos de legenda (Figura 3:, Tabela 1, Exemplo 2 ...)
LISTING_PREFIX = re.compile(
    r'^\s*(Listagem|Figura|Tabela|Quadro|Gr[aá]fico|Ap[eê]ndice|Anexo|Exemplo)\b'
    r'\s+(\d+(?:\.\d+)*|[IVXLC]+|[A-Z])\b\s*[:\-.\u2013\u2014]?\s*',
    re.IGNORECASE,
)
# Numeração multinível: 1, 1.1, 3.2.1, 1), 2 -, 4 –
NUMERATION = re.compile(r'^\s*\d+(?:\.\d+)*\s*[\.\)\-\u2013\u2014]?\s+')
HEADING_HASH = re.compile(r'^\s*#{1,6}\s*')        # ### no início
HTML_TAG = re.compile(r'</?[a-zA-Z][^<>\n]{0,200}>')                  # <span ...>, </span>, <br>, <x_y>
MD_LINK = re.compile(r'!?\[([^\]]*)\]\([^)]*\)')   # [txt](url) -> txt ; ![alt](url) -> alt
PANDOC_ATTR = re.compile(r'\s*\{[#.][^}]*\}')      # {#id .classe}
BULLET = re.compile(r'^\s*[\-\u2022\u2023\u25E6\u2043\u25AA\u00B7\u2219]+\s+')
ESCAPE = re.compile(r'\\([\\`*_{}\[\]()#+\-.!~<>|])')  # \_ \* \# -> _ * #


def clean_title(raw: str) -> str:
    if not raw:
        return ""
    t = html.unescape(raw)          # &nbsp; &amp; &lt; ...
    t = ESCAPE.sub(r'\1', t)        # desfaz escapes de markdown
    t = MD_LINK.sub(r'\1', t)       # links/imagens markdown -> texto
    t = HTML_TAG.sub(' ', t)        # remove qualquer tag HTML
    t = PANDOC_ATTR.sub('', t)      # atributos pandoc
    t = HEADING_HASH.sub('', t)     # hashes de cabeçalho
    t = re.sub(r'[*`~]', '', t)     # ênfase markdown * ** ` ~~
    t = re.sub(r'_{2,}', '', t)     # __ negrito (preserva snake_case)
    t = BULLET.sub('', t)           # marcadores de lista no início
    t = LISTING_PREFIX.sub('', t)   # Figura/Tabela/Exemplo ...
    t = NUMERATION.sub('', t)       # numeração de seção
    t = re.sub(r'\s+', ' ', t)      # colapsa espaços
    t = t.strip(' \t\u2013\u2014-:.\u00a0')
    return t.strip()

def clean_inline(raw: str) -> str:
    """Remove marcação do Pandoc preservando a estrutura do texto.
    Serve tanto para títulos quanto para blocos de conteúdo."""
    if not raw:
        return ""
    t = html.unescape(raw)
    t = ESCAPE.sub(r'\1', t)
    t = MD_LINK.sub(r'\1', t)
    t = HTML_TAG.sub(' ', t)
    t = PANDOC_ATTR.sub('', t)
    t = re.sub(r'[*`~]', '', t)
    return t


# ----------------------------- AUDITORIA -----------------------------
TEST_CASES = [
    # (entrada bruta, saida esperada)
    ('**1.1 ALGORITMOS**', 'ALGORITMOS'),
    ('**Funcionamento**', 'Funcionamento'),
    ('**Pseudocódigo**', 'Pseudocódigo'),
    ('**Módulo 1 - Algoritmos**', 'Módulo 1 - Algoritmos'),
    ('**Questionário Final**', 'Questionário Final'),
    ('## **Funcionamento**', 'Funcionamento'),
    ('### 3.3 ESTRUTURA DE SELEÇÃO SWITCH/CASE', 'ESTRUTURA DE SELEÇÃO SWITCH/CASE'),
    ('<span id="page-46-0"></span>**3.2.1 ATIVIDADES ESTRUTURA DE SELEÇÃO IF/ELSE**',
     'ATIVIDADES ESTRUTURA DE SELEÇÃO IF/ELSE'),
    ('**3.2 ESTRUTURA DE SELEÇÃO IF/ELSE**', 'ESTRUTURA DE SELEÇÃO IF/ELSE'),
    ('1) Introdução', 'Introdução'),
    ('2 - Conceitos básicos', 'Conceitos básicos'),
    ('4.4.1 ATIVIDADES ESTRUTURA DE REPETIÇÃO DO/WHILE', 'ATIVIDADES ESTRUTURA DE REPETIÇÃO DO/WHILE'),
    ('`código`', 'código'),
    ('~~texto riscado~~', 'texto riscado'),
    ('[Link para vídeo](https://youtu.be/abc)', 'Link para vídeo'),
    ('**O que é uma Variável?**', 'O que é uma Variável?'),
    ('&nbsp;**Operadores**&amp;Lógicos', 'Operadores&Lógicos'),
    ('• Tipos de Dados', 'Tipos de Dados'),
    ('Figura 3: Fluxograma de média', 'Fluxograma de média'),
    ('Tabela 1 - Comparação', 'Comparação'),
    ('Exemplo:', 'Exemplo'),
    ('**:**', ''),
    ('   ', ''),
    ('__Negrito com underscore__', 'Negrito com underscore'),
    ('nome\\_do\\_algoritmo', 'nome_do_algoritmo'),
    ('## 10. CONCLUSÃO', 'CONCLUSÃO'),
    ('Exemplo de execução de um programa', 'Exemplo de execução de um programa'),
    ('Anexo A - Resultados', 'Resultados'),
    ('decida se x \\< y', 'decida se x < y'),
]

if __name__ == "__main__":
    largura = max(len(repr(e)) for e, _ in TEST_CASES)
    ok = 0
    for entrada, esperado in TEST_CASES:
        obtido = clean_title(entrada)
        marca = "OK " if obtido == esperado else "FALHOU"
        if obtido == esperado:
            ok += 1
        log.info(f"[{marca}] {repr(entrada):<{largura}} -> {obtido!r}")
        if obtido != esperado:
            log.info(f"          esperado: {esperado!r}")
    log.info(f"\n{ok}/{len(TEST_CASES)} casos conforme o esperado.")