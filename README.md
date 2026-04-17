# 📄 InvoiceCzech

**Metody extrakce informací z českých faktur – bakalářský projekt**

Projekt se zaměřuje na automatickou extrakci strukturovaných dat z faktur pomocí moderních NLP a multimodálních modelů, s důrazem na **lokální běh bez závislosti na cloudových službách**.

---

## Co projekt umí

- Načíst obrázek faktury (PNG)
- Extrahovat klíčové informace pomocí AI modelů
- Porovnat různé přístupy: NER modely (BERT), layout-aware modely (LiLT, LayoutLMv3), end-to-end model (Donut)
- Exportovat výsledek do JSON
- Generovat syntetické faktury
- Ručně anotovat data pomocí GUI nástroje
- Augmentovat reálné faktury syntetickými daty

---

## Použité modely

| Model      | Typ přístupu                        |
|------------|-------------------------------------|
| BERT       | klasický NER (text only)            |
| LiLT       | layout-aware (text + bbox)          |
| LayoutLMv3 | multimodální (text + obraz)         |
| Donut      | end-to-end (bez OCR)                |

Modely jsou dostupné na Hugging Face: https://huggingface.co/TomasFAV

---

## Dataset

| Dataset | Typ        | Popis                      |
|---------|------------|----------------------------|
| V0      | syntetický | šablonové faktury          |
| V1      | syntetický | náhodný layout             |
| V2      | hybridní   | reálné + syntetické        |
| V3      | reálný     | ručně anotované faktury    |

**Formáty dat:** NER (BIO tagging) · LayoutLMv3 (bbox + tokeny) · Donut (JSON) · COCO / YOLO

---

## Architektura projektu

```
app/
├── client/             # demonstrační aplikace (GUI)
├── common/             # sdílené modely a utility
├── data_generator/     # generování syntetických faktur
├── invoice_annotator/  # anotační nástroj
├── invoice_enhancer/   # augmentace faktur
└── main.py             # vstupní bod aplikace
```

### Samostatné nástroje

- **Generator** – generování syntetických faktur
- **Enhancer** – augmentace reálných dokumentů
- **Annotator** – ruční anotace + poloautomatické předznačení
- **Client** – demo aplikace pro inference

---

## Instalace

```bash
git clone https://github.com/TomasFAV/InvoiceCzech.git
cd InvoiceCzech
pip install -r requirements.txt
```

### Požadavky

- Python 3.10+
- Tesseract OCR (pro NER modely)
- Doporučeno: GPU (CUDA)

---

## Spuštění

```bash
python app/main.py client
```

### Další režimy

```bash
python main.py annotator
python main.py generate --train 1200 --test 39 --validation 184 --random True
python main.py enhance --metadata-path cesta/k/metadata_layoutlmv3.jsonl --samples 3
```

---

## Vyhodnocení

- micro-F1 / macro-F1
- fuzzy F1 (s tolerancí)
- document-level exact match
- strukturální metrika (tree edit distance)

---

## Hlavní závěry

- Syntetická data mohou výrazně pomoci, ale nestačí sama o sobě
- Layout-aware modely výrazně překonávají čisté NER
- End-to-end modely (Donut) jsou slibné, ale náročnější na data
- Lokální řešení je možné, ale vyžaduje kompromisy

---

## Omezení

- Silná závislost na kvalitě OCR (u NER přístupů)
- Dataset je relativně malý v části reálných dat
- Některé části projektu mají experimentální charakter

---

## Autor

**Tomáš Brabec**  
Bakalářský projekt – Metody extrakce informací pro analýzu faktur  
Vedoucí: Ing. Ladislav Lenc, Ph.D.

---

## Licence

Tento projekt je určen primárně pro studijní a výzkumné účely.

> Projekt vznikl jako výzkumný prototyp. Nejde o hotové produkční řešení, ale o základ pro experimenty, další vývoj a porovnávání přístupů k extrakci informací z českých faktur.