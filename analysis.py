import re
import os
import spacy

from title_cleaner import clean_title

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger("genese")

HEADING_LOCATOR = re.compile(r"^(#{1,6})\s*(.*)$", re.MULTILINE)

BLOOM_ORDER = {
    "LEMBRAR": 1,
    "ENTENDER": 2,
    "APLICAR": 3,
    "ANALISAR": 4,
    "AVALIAR": 5,
    "CRIAR": 6,
}

BLOOM_VERBS = {
    "CRIAR": {
        "projetar", "criar", "elaborar", "desenvolver", "construir",
        "produzir", "compor", "formular", "propor", "planejar",
    },
    "AVALIAR": {
        "avaliar", "julgar", "criticar", "justificar", "argumentar",
        "defender", "selecionar", "priorizar", "recomendar", "concluir",
    },
    "ANALISAR": {
        "analisar", "comparar", "diferenciar", "distinguir", "decompor",
        "relacionar", "categorizar", "depurar", "investigar", "examinar",
    },
    "APLICAR": {
        "aplicar", "implementar", "calcular", "construir", "montar",
        "simular", "demonstrar", "converter", "ordenar",
    },
    "ENTENDER": {
        "explicar", "descrever", "exemplificar", "ilustrar", "resumir",
        "interpretar", "traduzir", "esquematizar", "generalizar", "inferir",
    },
    "LEMBRAR": {
        "definir", "listar", "nomear", "citar", "enumerar",
        "identificar", "reconhecer", "recordar", "apontar", "indicar",
    },
}

MIN_LEMMAS_FOR_MERGE = 2

MIN_DENSITY = 0.5
DOMINANCE_RATIO = 1.3

NON_PEDAGOGICAL_TITLES = {
    "sumário", "índice", "prefácio", "dedicatória", "agradecimentos",
    "referências bibliográficas", "referências", "bibliografia",
    "apresentação", "sobre os autores", "colofão", "histórico"
}

MIN_CONTENT_CHARS = 200

# Substantivos que, como sujeito, indicam que o verbo descreve o comportamento
# do sistema, não uma instrução dirigida ao aluno.
SYSTEM_SUBJECTS = {
    "programa", "algoritmo", "computador", "função", "procedimento",
    "comando", "instrução", "variável", "sistema", "máquina", "código",
    "compilador", "processador", "memória", "linguagem", "software",
    "vetor", "matriz", "registro", "laço", "estrutura", "método",
    "operador", "expressão", "valor", "dado", "processo",
}

# O spaCy erra a lematização de formas verbais em subjuntivo/imperativo.
# Confirmado empiricamente; ampliar conforme o modelo em uso.
LEMMA_FIXES = {
    "justifiquar": "justificar",
    "inverta": "inverter",
    "analise": "analisar",
    "verifiquar": "verificar",
    "expliquar": "explicar",
    "identifiquar": "identificar",
    "classifiquar": "classificar",
    "modifiquar": "modificar",
    "simplifiquar": "simplificar",
    "especifiquar": "especificar",
}

# Formas imperativas frequentes em enunciados que o parser classifica
# erroneamente como substantivo. Detectadas por forma de superfície.
IMPERATIVE_FORMS = {
    "implemente": "implementar",
    "analise": "analisar",
    "compare": "comparar",
    "calcule": "calcular",
    "descreva": "descrever",
    "explique": "explicar",
    "justifique": "justificar",
    "elabore": "elaborar",
    "projete": "projetar",
    "construa": "construir",
    "defina": "definir",
    "identifique": "identificar",
    "liste": "listar",
    "cite": "citar",
    "escreva": "escrever",
    "faça": "fazer",
    "crie": "criar",
    "avalie": "avaliar",
}

class CurriculumProcessor:
    def __init__(self, spacy_model="pt_core_news_lg"):
        self.nlp = None
        self.last_raw_topics = []
        self._load_nlp_model(spacy_model)
    
    def _title_lemmas(self, title):
        doc = self.nlp(title.lower())
        return {tok.lemma_ for tok in doc
                if (tok.is_alpha or tok.like_num)
                and not tok.is_stop
                and len(tok.lemma_) > 2}
    
    def _load_nlp_model(self, model_name):
        self.nlp = spacy.load(model_name)

    def _instructional_verbs(self, doc):
        """Extrai os lemas dos verbos que instruem o aluno, descartando os que
        apenas descrevem o comportamento do sistema.

        O critério é o sujeito: 'o programa executa' descreve a máquina;
        'execute o programa' instrui o leitor. A detecção de imperativo por
        morfologia não é viável em português — o spaCy marca as formas
        imperativas como subjuntivo ou indicativo.
        """
        verbs = []
        for token in doc:
            surface = token.text.lower()
            if surface in IMPERATIVE_FORMS:
                verbs.append(IMPERATIVE_FORMS[surface])
                continue

            if token.pos_ not in ("VERB", "AUX") or token.is_stop:
                continue

            # Auxiliar de uma locução: o lema relevante é o do verbo principal.
            if token.dep_ == "aux":
                continue

            if "VerbForm=Part" in str(token.morph):
                tem_auxiliar = any(c.dep_ == "aux" for c in token.children)
                if not tem_auxiliar or token.dep_ in ("amod", "acl"):
                    continue
            
            subjects = {
                child.lemma_
                for child in token.children
                if child.dep_.startswith("nsubj")
            }

            if subjects & SYSTEM_SUBJECTS:
                continue

            lemma = LEMMA_FIXES.get(token.lemma_, token.lemma_)
            verbs.append(lemma)

        return verbs    

    def _order_by_document_position(self, topics):
        return sorted(topics, key=lambda t: t.get("doc_order", 0))
    
    def clean_pandoc_metadata(self, title_text):
        return clean_title(title_text)

    def collect_topics(self, md_file):
        with open(md_file, 'r', encoding='utf-8') as f:
            md_text = f.read()

        
        headings_data = []

        for match in HEADING_LOCATOR.finditer(md_text):
            headings_data.append({
                "start_index": match.start(),
                "end_index": match.end(),
                "hashes": match.group(1),
                "raw_title": match.group(2).strip()
            })
        log.info("=== Fase 2·3 · Coleta e agrupamento de cabeçalhos ===")
        log.info(f"{len(headings_data)} cabeçalhos brutos em {os.path.basename(md_file)}")

        collected_topics = []
        last_main_topic = None

        for i, current_heading in enumerate(headings_data):
            content_start_index = current_heading["end_index"]

            if i + 1 < len(headings_data):
                content_end_index = headings_data[i + 1]["start_index"]
            else:
                content_end_index = len(md_text)
            
            raw_content = md_text[content_start_index:content_end_index].strip()

            cleaned_title = self.clean_pandoc_metadata(current_heading["raw_title"])

            level = len(current_heading["hashes"])

            if not cleaned_title or len(cleaned_title) < 3:
                continue

            if cleaned_title.strip().lower() in NON_PEDAGOGICAL_TITLES:
                log.info(f"   descartado (seção não pedagógica): {cleaned_title!r}")
                continue

            if level in (1,2) and len(raw_content.strip()) < MIN_CONTENT_CHARS:
                log.info(f"   descartado (corpo insuficiente): {cleaned_title!r}")
                continue

            topic = {
                "title": cleaned_title,
                "markdown_level": level,
                "content_block": raw_content,
                "parent_title": last_main_topic["title"] if (level > 1 and last_main_topic) else None,
                "doc_order": len(collected_topics)
            }

            if level in (1, 2):
                collected_topics.append(topic)
                last_main_topic = topic
            
            elif level in (3, 4, 5, 6):
                if last_main_topic:
                    last_main_topic["content_block"] += raw_content
                    log.info(f"   H{level} {cleaned_title!r} absorvido em {last_main_topic['title']!r}")
                else:
                    collected_topics.append(topic)
                    last_main_topic = topic

        log.info(f"{len(collected_topics)} tópicos principais após o agrupamento")
        return collected_topics

    def filter_similar_topics(self, collected_topics, similarity_threshold=0.6):
        if not self.nlp:
            return collected_topics, {}
        
        log.info("=== Fase 4 · Consolidação por sobreposição lexical (Jaccard) ===")
        log.info(f"{len(collected_topics)} tópicos antes da consolidação (limiar {similarity_threshold:.2f})")

        final_topics = []
        processed_titles = []
        merged_content_map = {}

        def topic_key(t):
            return (t["title"], t.get("parent_title"), t.get("source_file", "N/A"))
        
        for topic in collected_topics:
            title = topic["title"]
            key = topic_key(topic)
            merged_content_map[key] = ""
            actual = self._title_lemmas(title)

            is_duplicate = False
            if len(actual) < MIN_LEMMAS_FOR_MERGE:
                # Título com carga lexical insuficiente: fundir por sobreposição
                # aqui produziria falsos positivos (ex.: "Capítulo 2" x "Capítulo 3").
                final_topics.append(topic)
                processed_titles.append((title, actual, key))
                continue

            if actual:
                for accepted_title, accepted, accepted_key in processed_titles:
                    union = actual | accepted
                    if not union:
                        continue
                    jaccard = len(actual & accepted) / len(union)
                    if jaccard >= similarity_threshold:
                        is_duplicate = True
                        log.info(f"   fundir: {title!r} × {accepted_title!r}   →   Jaccard {jaccard:.2f}")
                        merged_content_map[accepted_key] += topic["content_block"]
                        break
            
            if not is_duplicate:
                final_topics.append(topic)
                processed_titles.append((title, actual, key))
        
        log.info(f"{len(final_topics)} tópicos após a consolidação ({len(collected_topics) - len(final_topics)} fundidos)")
        return final_topics, merged_content_map
    
    def classify_bloom_by_content(self, content_block):
        if not self.nlp:
            return {level: 0.0 for level in BLOOM_VERBS.keys()}
        
        doc = self.nlp(content_block.lower())

        verb_lemmas = self._instructional_verbs(doc)

        content_lemmas = [
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_punct and token.is_alpha
        ]

        total_units = len(content_lemmas)

        if total_units == 0:
            return {level: 0.0 for level in BLOOM_VERBS.keys()}
        
        bloom_densities = {}

        for level, verbs in BLOOM_VERBS.items():
            frequency = sum(1 for lemma in verb_lemmas if lemma in verbs)

            density = (frequency / total_units) * 100
            bloom_densities[level] = round(density, 2)
        
        return bloom_densities
    
    def process_curriculum_topics(self, all_raw_topics, threshold=0.6):
        self.last_raw_topics = list(all_raw_topics)
        def aggregation_key(topic):
            # O título sozinho não identifica o tópico: "Exercícios" repete-se em
            # todos os capítulos. A chave inclui a origem para preservá-los separados.
            return (topic["title"], topic.get("parent_title"), topic.get("source_file", "N/A"))
        
        aggregated_topics_map = {}
        
        for topic in all_raw_topics:
            key = aggregation_key(topic)
        
            if key not in aggregated_topics_map:
                aggregated_topics_map[key] = {
                    "title": topic["title"],
                    "markdown_level": topic["markdown_level"],
                    "content_block": topic["content_block"],
                    "parent_title": topic.get("parent_title"),
                    "doc_order": topic.get("doc_order", 0),
                    "source_file": topic.get("source_file", "N/A")
                }
            else:
                aggregated_topics_map[key]["content_block"] += topic["content_block"]
        
        ordered_aggregated_topics = []
        seen_keys = set()
        for topic in all_raw_topics:
            key = aggregation_key(topic)
            if key not in seen_keys:
                ordered_aggregated_topics.append(aggregated_topics_map[key])
                seen_keys.add(key)

        filtered_topics, content_map = self.filter_similar_topics(ordered_aggregated_topics, similarity_threshold=threshold)

        return filtered_topics, content_map
    
    def run_bloom_classification(self, topics_for_bloom, content_map):

        final_curriculum = []
        log.info("=== Fase 5 · Classificação cognitiva (Taxonomia de Bloom) ===")
        for topic in topics_for_bloom:
            title = topic["title"]

            content_to_analyze = topic["content_block"]

            key = (topic["title"], topic.get("parent_title"), topic.get("source_file", "N/A"))
            if key in content_map and content_map[key]:
                content_to_analyze += "\n\n" + content_map[key]
            bloom_density_map = self.classify_bloom_by_content(content_to_analyze)

            topic["bloom_level"] = bloom_density_map

            ranked = sorted(bloom_density_map.items(),
                            key=lambda item: item[1], reverse=True)
            level, dens = ranked[0]
            runner_up = ranked[1][1] if len(ranked) > 1 else 0.0

            if dens < MIN_DENSITY:
                log.info(f"   {title!r}  →  sem verbo de Bloom dominante "
                         f"(densidade {dens:.2f}% abaixo do piso)")
                topic["bloom_level"] = {lvl: 0.0 for lvl in BLOOM_VERBS}
            elif runner_up > 0.0 and dens < runner_up * DOMINANCE_RATIO:
                log.info(f"   {title!r}  →  sem verbo de Bloom dominante "
                         f"({level} {dens:.2f}% vs {ranked[1][0]} {runner_up:.2f}%)")
                topic["bloom_level"] = {lvl: 0.0 for lvl in BLOOM_VERBS}
            else:
                log.info(f"   {title!r}  →  {level}  (densidade {dens:.2f}%)")

            final_curriculum.append(topic)

        return final_curriculum

    def _dominant_bloom_level(self, topic):
        bloom_map = topic.get("bloom_level") or {}
        if not bloom_map:
            return None
        ranked = sorted(bloom_map.items(), key=lambda kv: kv[1], reverse=True)
        nivel, dens = ranked[0]
        segundo = ranked[1][1] if len(ranked) > 1 else 0.0
        if dens < MIN_DENSITY:
            return None
        if segundo > 0.0 and dens < segundo * DOMINANCE_RATIO:
            return None
        return nivel

    def generate_learning_path(self, classified_topics):
        log.info("=== Fase 6 · Geração da trilha de aprendizagem ===")

        topics_by_level = {}
        unclassified_topics = []

        for topic in classified_topics:
            level = self._dominant_bloom_level(topic)
            if level is None:
                unclassified_topics.append(topic)
            else:
                topics_by_level.setdefault(level, []).append(topic)

        log.info("--- Etapa 1: ordenação cognitiva (Nível 1 ao 6) ---")
        ordered_levels = sorted(topics_by_level.keys(), key=lambda level: BLOOM_ORDER.get(level, 99))
        for level in ordered_levels:
            log.info(f"   Nível {BLOOM_ORDER.get(level, '?')} ({level}): {len(topics_by_level[level])} tópico(s)")

        log.info("--- Etapa 2: ordenação temática dentro de cada nível ---")
        learning_path = []
        for level in ordered_levels:
            group = self._order_by_document_position(topics_by_level[level])
            log.info(f"   {level}: " + " → ".join(t["title"] for t in group))
            learning_path.extend(group)

        if unclassified_topics:
            log.info(f"   {len(unclassified_topics)} tópico(s) sem verbo dominante "
                     f"inseridos na posição original do documento")
            learning_path.extend(unclassified_topics)
            learning_path.sort(key=lambda t: (
                BLOOM_ORDER.get(self._dominant_bloom_level(t), 99),
                t.get("doc_order", 0)
            ))
        for position, topic in enumerate(learning_path, start=1):
            topic["path_position"] = position

        log.info(f"Trilha de aprendizagem gerada com {len(learning_path)} tópico(s).")
        return learning_path

    def build_analytics_report(self, learning_path):
        log.info("=== Relatório analítico · distribuição e lacunas ===")

        distribution = {level: 0 for level in BLOOM_ORDER.keys()}
        unclassified_count = 0

        for topic in learning_path:
            level = self._dominant_bloom_level(topic)
            if level is None:
                unclassified_count += 1
            else:
                distribution[level] += 1

        total_classified = sum(distribution.values())

        percentages = {
            level: round((count / total_classified) * 100, 2) if total_classified else 0.0
            for level, count in distribution.items()
        }

        missing_levels = [
            level for level, count in distribution.items()
            if count == 0
        ]
        missing_levels.sort(key=lambda level: BLOOM_ORDER[level])

        report = {
            "total_topics": len(learning_path),
            "total_classified": total_classified,
            "unclassified_count": unclassified_count,
            "distribution": distribution,
            "percentages": percentages,
            "missing_levels": missing_levels,
        }

        log.info(f"   Distribuição: {distribution}")
        if missing_levels:
            log.info(f"   Lacunas identificadas: {', '.join(missing_levels)}")
        else:
            log.info("   Nenhuma lacuna de nível cognitivo identificada.")

        return report