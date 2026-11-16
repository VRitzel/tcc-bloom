"""
Classifica os fragmentos escolhidos e prepara o material da validação.

Gera dois arquivos a partir do mesmo JSON de fragmentos:

  1. classificacao_ferramenta.csv  -> a resposta da FERRAMENTA para cada
     fragmento. É sua, fica guardada, e não vai para o professor.

  2. anexo_fragmentos.txt          -> os fragmentos numerados, SEM nenhuma
     classificação, prontos para colar no Anexo do Caderno 1.

O texto usado nos dois é exatamente o mesmo, que é o ponto: professor e
ferramenta precisam julgar o mesmo objeto para o Kappa fazer sentido.

Uso:
    python experiments/classificar_fragmentos.py fragmentos_escolhidos.json

Depois da aplicação, você terá três colunas para cruzar:
  - a deste CSV (ferramenta)
  - as respostas de cada docente (Parte B)
  - a moda das respostas dos docentes (o gabarito)
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import (
    CurriculumProcessor,
    BLOOM_ORDER,
    BLOOM_VERBS,
    MIN_DENSITY,
    DOMINANCE_RATIO,
)

SEM_DOMINANTE = "SEM_VERBO_DOMINANTE"


def classificar(processor, texto):
    """Aplica a fase 5 a um fragmento, com as mesmas regras de dominância
    usadas em run_bloom_classification."""
    densidades = processor.classify_bloom_by_content(texto)

    ranked = sorted(densidades.items(), key=lambda item: item[1], reverse=True)
    nivel, dens = ranked[0]
    segundo_nivel, segundo = ranked[1] if len(ranked) > 1 else (None, 0.0)

    if dens < MIN_DENSITY:
        motivo = f"densidade {dens:.2f}% abaixo do piso"
        return SEM_DOMINANTE, dens, segundo_nivel, segundo, motivo

    if segundo > 0.0 and dens < segundo * DOMINANCE_RATIO:
        motivo = f"{nivel} {dens:.2f}% vs {segundo_nivel} {segundo:.2f}%"
        return SEM_DOMINANTE, dens, segundo_nivel, segundo, motivo

    return nivel, dens, segundo_nivel, segundo, ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('fragmentos', help='JSON com os fragmentos escolhidos')
    ap.add_argument('--csv', default='classificacao_ferramenta.csv')
    ap.add_argument('--anexo', default='anexo_fragmentos.txt')
    ap.add_argument('--modelo', default='pt_core_news_lg')
    args = ap.parse_args()

    with open(args.fragmentos, encoding='utf-8') as f:
        fragmentos = json.load(f)

    print(f"Carregando {args.modelo}...", file=sys.stderr)
    processor = CurriculumProcessor(args.modelo)

    linhas = []
    for i, frag in enumerate(fragmentos, start=1):
        texto = frag['texto']
        nivel, dens, seg_nivel, seg_dens, motivo = classificar(processor, texto)

        linhas.append({
            'n': f"{i:02d}",
            'nivel_ferramenta': nivel,
            'ordem_bloom': BLOOM_ORDER.get(nivel, ''),
            'densidade': f"{dens:.2f}",
            'segundo_nivel': seg_nivel or '',
            'segunda_densidade': f"{seg_dens:.2f}",
            'observacao': motivo,
            'secao': frag.get('secao', ''),
            'doc_order': frag.get('doc_order', ''),
            'caracteres': len(texto),
            'texto': texto,
        })

        marca = nivel if nivel != SEM_DOMINANTE else "-- sem dominante"
        print(f"  {i:02d}. {marca:<22} {texto[:60]}...", file=sys.stderr)

    with open(args.csv, 'w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)

    with open(args.anexo, 'w', encoding='utf-8') as f:
        f.write("ANEXO — CADERNO DE FRAGMENTOS\n\n")
        f.write("Os fragmentos abaixo foram extraídos de material didático real de\n")
        f.write("disciplinas de programação. São apresentados sem classificação e sem\n")
        f.write("identificação do capítulo de origem.\n\n")
        for linha in linhas:
            f.write(f"\n{'-' * 70}\n")
            f.write(f"FRAGMENTO {linha['n']}\n\n")
            f.write(f"{linha['texto']}\n")

    # Distribuição, para conferir o balanceamento antes de aplicar
    print(f"\n{'=' * 60}", file=sys.stderr)
    contagem = {}
    for linha in linhas:
        contagem[linha['nivel_ferramenta']] = contagem.get(linha['nivel_ferramenta'], 0) + 1

    print("Distribuição segundo a ferramenta:", file=sys.stderr)
    for nivel in list(BLOOM_VERBS.keys()) + [SEM_DOMINANTE]:
        print(f"  {nivel:<22} {contagem.get(nivel, 0)}", file=sys.stderr)

    print(f"\n{args.csv}    <- guarde, não mostre a ninguém", file=sys.stderr)
    print(f"{args.anexo}   <- vai para o Caderno 1", file=sys.stderr)


if __name__ == '__main__':
    main()