from marker.converters.pdf import PdfConverter
from marker.output import text_from_rendered 
from marker.models import create_model_dict
from tkinter import ttk
import pypandoc
import logging
import shutil
import json
import os

log = logging.getLogger("genese")

OUTPUT_DIR = "files"
MEDIA_DIR = "medias"
IMAGES_SUBDIR = "images"
TABLES_SUBDIR = "tables"

def clean_directory():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

class LoadingFrame(ttk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.files_to_process = []
        self.extracted_data = []

        self.processor = controller.processor

        ttk.Label(self, text="Extraindo Texto dos Arquivos...", font=("Segoe UI", 14, "bold")).pack(pady=20)
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=5)
        self.status_label = ttk.Label(self, text="Iniciando...", font=("Segoe UI", 10))
        self.status_label.pack(pady=5)
    
    def start_extraction(self, files):
        self.files_to_process = list(files)
        self.extracted_data = []
        self.progress_bar["maximum"] = len(files)
        self.progress_bar["value"] = 0
        self.status_label.configure(text=f"Processando 0 de {len(files)} arquivos...")
        self.after(50, self._process_next_file)
    
    def _process_file_with_pandoc(self, file_path, output_dir, filename_base):
        temp_media_path = os.path.join(output_dir, "temp_media")
        pypandoc.convert_file(file_path, to="markdown", outputfile=os.path.join(output_dir, f"{filename_base}.md"), extra_args=[f"--extract-media={temp_media_path}", "--wrap=none"])
        final_images_path = os.path.join(output_dir, MEDIA_DIR, IMAGES_SUBDIR)

        if os.path.exists(temp_media_path):
            os.makedirs(final_images_path, exist_ok=True)
            media_content_path = os.path.join(temp_media_path, "media")
            if os.path.exists(media_content_path):
                for item in os.listdir(media_content_path):
                    shutil.move(os.path.join(media_content_path, item), final_images_path)      
            shutil.rmtree(temp_media_path)

        pandoc_json = pypandoc.convert_file(file_path, to="json")
        llm_data = {
            "filename": os.path.basename(file_path),
            "full_text": pypandoc.convert_text(pandoc_json, to="plain", format="json"),
            "tables": [],
            "sections": [],
        }

#        with open(os.path.join(output_dir, f"{filename_base}.json"), "w", encoding="utf-8") as f: json.dump(llm_data, f, indent=4, ensure_ascii=False)

        return llm_data
    
    def _process_next_file(self):
        if self.files_to_process:
            file_path = self.files_to_process.pop(0)
            filename_base, extension = os.path.splitext(os.path.basename(file_path))
            extension = extension.lower()
            output_dir = os.path.join(OUTPUT_DIR, filename_base)

            log.info("=== Fase 1 · Ingestão (conversão do documento) ===")

            try:
                os.makedirs(output_dir, exist_ok=True)
                os.makedirs(os.path.join(output_dir, MEDIA_DIR, IMAGES_SUBDIR), exist_ok=True)
                os.makedirs(os.path.join(output_dir, MEDIA_DIR, TABLES_SUBDIR), exist_ok=True)

                if extension in (".docx", ".odt", ".rtf"):
                    llm_data = self._process_file_with_pandoc(file_path, output_dir, filename_base)
                    log.info(f"Convertendo {os.path.basename(file_path)} via Pandoc...")
                elif extension == ".pdf":
                    log.info(f"Convertendo {os.path.basename(file_path)} via Marker (PDF → Markdown)...")
                    llm_data = None
                    md_output_path = os.path.join(output_dir, f"{filename_base}.md")
                    converter = PdfConverter(artifact_dict=create_model_dict(), config={"pdf_config": {"extract_images": True, "extract_tables": True}})
                    rendered = converter(file_path)
                    content_read, _, images = text_from_rendered(rendered)
                    
                    with open(md_output_path, "w", encoding="utf-8") as f:
                        f.write(content_read)
                    
                    llm_data = {
                        "filename": os.path.basename(file_path),
                        "full_text": content_read,
                        "tables": [],
                        "sections": [],
                    }
                
                elif extension == ".txt":
                    log.info(f"Lendo {os.path.basename(file_path)} (texto puro)...")
                    with open(file_path, "r", encoding="utf-8") as f: text_content = f.read()

                    llm_data = {
                        "filename": os.path.basename(file_path),
                        "full_text": text_content,
                        "tables": [],
                        "sections": [],
                    }

                    with open(os.path.join(output_dir, f"{filename_base}.md"), "w", encoding="utf-8") as f: f.write(text_content)

                md_path = os.path.join(output_dir, f"{filename_base}.md")
                file_topics = self.processor.collect_topics(md_path)

                for topic in file_topics:
                    topic['source_file'] = filename_base
    
                llm_data["sections"] = file_topics
                with open(os.path.join(output_dir, f"{filename_base}.json"), "w", encoding="utf-8") as f: json.dump(llm_data, f, indent=4, ensure_ascii=False)
                self.extracted_data.append(llm_data)

            except Exception as e:
                error_message = f"ERRO ao processar {filename_base}: {type(e).__name__}"
                log.error("%s: %s", error_message, e)

            current_count = self.progress_bar["value"] + 1
            self.progress_bar["value"] = current_count
            self.status_label.configure(text=f"Processando {current_count} de {self.progress_bar["maximum"]} arquivos...")

            self.after(50, self._process_next_file)
        else:
            self._extraction_complete()
    
    def _extraction_complete(self):
        self.status_label.configure(text="Extração concluída!")

        all_raw_topics = []
        for data in self.extracted_data:
            all_raw_topics.extend(data["sections"])

        filtered_topics, content_map = self.processor.process_curriculum_topics(
            all_raw_topics, threshold=0.6
        )

        final_curriculum = self.processor.run_bloom_classification(filtered_topics, content_map)
        self.controller.extraction_finished(final_curriculum)