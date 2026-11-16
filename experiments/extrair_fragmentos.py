"""
Extração de fragmentos candidatos para a validação com docentes.

Não faz parte da ferramenta. É um utilitário de uso único: lê o JSON já
produzido pela fase 1 e garimpa parágrafos de prosa limpa, em tamanho
adequado para um docente ler e classificar em poucos segundos.

Uso:
    python experiments/extrair_fragmentos.py                  # imprime na tela
    python experiments/extrair_fragmentos.py > candidatos.txt # salva para leitura
    python experiments/extrair_fragmentos.py --json frags.json

Depois de gerar, leia os candidatos, escolha os 30 finais à mão mirando
cobrir os seis níveis de Bloom, e salve a seleção. O mesmo arquivo deve
alimentar o Anexo do Caderno 1 e o classificador — professor e ferramenta
precisam julgar exatamente o mesmo texto.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from title_cleaner import clean_inline


CAMINHO_PADRAO = "files/livro_alg1/livro_alg1.json"

MIN_CHARS = 200
MAX_CHARS = 700
MIN_PONTOS = 2          # frases completas: parágrafo precisa ter pelo menos 2 pontos
MAX_PROP_DIGITOS = 0.12  # acima disso é tabela, listagem de saída ou caso de teste

# Restos de conversão que indicam que o parágrafo não é prosa aproveitável.
RUIDO = re.compile(
    r'\{#_bookmark'          # âncoras do Pandoc
    r'|!\[\]\('              # imagens sem alt
    r'|\.png'                # referências a figuras
    r'|^\s*[-|+]{3,}'        # bordas de tabela ASCII
    r'|\\\|'                 # pipes escapados (tabela)
    r'|figura \d'            # legendas
    r'|tabela \d'
    r'|listagem \d'
    r'|^\s*\d+\s+\d+\s+\d+'  # três números seguidos: matriz ou caso de teste
    r'|<table|</td>|<tr>',   # tabelas em HTML
    re.IGNORECASE | re.MULTILINE,
)


def extrair_candidatos(bloco, min_chars=MIN_CHARS, max_chars=MAX_CHARS):
    """Devolve os parágrafos do bloco que servem como fragmento de validação."""
    if not bloco:
        return []

    texto = clean_inline(bloco)
    texto = re.sub(r'^\s*>\s?', '', texto, flags=re.MULTILINE)  # blockquote do Pandoc
    texto = texto.replace('\u2011', '-').replace('\u00a0', ' ')

    candidatos = []
    for paragrafo in re.split(r'\n\s*\n', texto):
        bruto = paragrafo
        par = ' '.join(paragrafo.split())

        if not par:
            continue
        if not (min_chars <= len(par) <= max_chars):
            continue
        if RUIDO.search(bruto):
            continue
        if sum(c.isdigit() for c in par) / len(par) > MAX_PROP_DIGITOS:
            continue
        if par.count('.') < MIN_PONTOS:
            continue

        candidatos.append(par)

    return candidatos


def carregar_secoes(caminho):
    with open(caminho, encoding='utf-8') as f:
        dados = json.load(f)

    secoes = dados.get('sections')
    if not secoes:
        raise ValueError(
            f"{caminho} não contém a chave 'sections'. "
            "Confirme que é o JSON gerado pela fase 1 da ferramenta."
        )
    return secoes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--arquivo', default=CAMINHO_PADRAO,
                    help=f'JSON da fase 1 (padrão: {CAMINHO_PADRAO})')
    ap.add_argument('--min', type=int, default=MIN_CHARS,
                    help=f'tamanho mínimo do fragmento (padrão: {MIN_CHARS})')
    ap.add_argument('--max', type=int, default=MAX_CHARS,
                    help=f'tamanho máximo do fragmento (padrão: {MAX_CHARS})')
    ap.add_argument('--secao', default=None,
                    help='filtra por trecho do título da seção (ex.: Exercícios)')
    ap.add_argument('--a-partir-de', type=int, default=None, metavar='N',
                    help='só seções com doc_order >= N (capítulos finais têm '
                         'os exercícios difíceis, onde estão os níveis altos)')
    ap.add_argument('--json', default=None, metavar='SAIDA',
                    help='grava os candidatos em JSON em vez de imprimir')
    args = ap.parse_args()

    secoes = carregar_secoes(args.arquivo)

    coletados = []
    for secao in secoes:
        titulo = secao.get('title', '(sem título)')
        ordem = secao.get('doc_order', 0)

        if args.secao and args.secao.lower() not in titulo.lower():
            continue
        if args.a_partir_de is not None and ordem < args.a_partir_de:
            continue

        for i, frag in enumerate(extrair_candidatos(secao.get('content_block', ''),
                                                    args.min, args.max)):
            coletados.append({
                'secao': titulo,
                'doc_order': ordem,
                'indice_no_bloco': i,
                'caracteres': len(frag),
                'texto': frag,
            })

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(coletados, f, ensure_ascii=False, indent=2)
        print(f"{len(coletados)} candidatos gravados em {args.json}", file=sys.stderr)
        return

    for c in coletados:
        print(f"\n--- [{c['doc_order']:>3}] {c['secao']} "
              f"#{c['indice_no_bloco']} ({c['caracteres']} car.) ---")
        print(c['texto'])

    print(f"\n\n{'=' * 70}", file=sys.stderr)
    print(f"{len(coletados)} candidatos em {len({c['secao'] for c in coletados})} seções.",
          file=sys.stderr)
    if len(coletados) < 60:
        print("Colheita magra. Tente --min 120 para afrouxar o filtro.", file=sys.stderr)


if __name__ == '__main__':
    main()