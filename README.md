# 📄 InvoiceCzech

**Metody extrakce informací z českých faktur – bakalářský projekt**

Projekt se zaměřuje na automatickou extrakci strukturovaných dat z faktur s důrazem na **lokálně provozovatelné řešení bez závislosti na externích cloudových službách**. Součástí je návrh a tvorba datasetu českých faktur a experimentální porovnání různých přístupů ke zpracování dokumentů.

---

## Přehled projektu

Projekt pokrývá celý proces zpracování faktur:

- generování syntetických dat
- augmentaci reálných dokumentů
- ruční anotaci faktur
- trénování modelů pro extrakci informací
- inferenci a vizualizaci výsledků

Podporovány jsou tři hlavní přístupy:
- klasické NER modely nad OCR výstupem
- layout-aware modely využívající prostorové informace
- end-to-end multimodální model generující strukturovaný výstup

---

## Použité modely

| Model        | Typ přístupu                              |
|--------------|-------------------------------------------|
| BERT         | NER (text z OCR)                          |
| LiLT         | layout-aware (text + bounding boxy)       |
| LayoutLMv3   | multimodální (text + layout + obraz)      |
| Donut        | end-to-end (přímé zpracování obrazu)      |

Natrénované modely jsou dostupné na Hugging Face:  
👉 https://huggingface.co/TomasFAV

---

## Dataset

V rámci projektu byl vytvořen vlastní dataset českých faktur:

| Dataset | Typ        | Popis                                      |
|---------|------------|--------------------------------------------|
| V0      | syntetický | šablonové faktury                          |
| V1      | syntetický | faktury s náhodným layoutem                |
| V2      | hybridní   | reálné faktury + syntetické komponenty     |
| V3      | reálný     | ručně anotované faktury                    |
| Test    | reálný     | testovací sada (39 dokumentů)              |

### Podporované formáty

- **NER (BIO tagging)**
- **LayoutLMv3 (tokeny + bounding boxy)**
- **Donut (JSON klíč–hodnota)**
- **COCO / YOLO** (pro detekční přístupy)

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

### Hlavní komponenty

- **Generator** – generování syntetických faktur  
- **Enhancer** – augmentace reálných dokumentů  
- **Annotator** – ruční anotace s poloautomatickým předznačením  
- **Client** – demonstrační aplikace pro inferenci  

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

Modely jsou vyhodnocovány na testovací sadě reálných faktur pomocí následujících metrik:

- **micro-F1** (hlavní metrika)
- **macro-F1**
- **Document Exact Match (DEM)**
- **Normalized Edit Distance (NED)**
- **Strukturální metrika (tree edit distance)**

---

## Hlavní závěry

- Reálná data (V3) mají zásadní vliv na kvalitu modelů
- Hybridní dataset (V2) výrazně zlepšuje generalizaci
- Layout-aware modely překonávají čistě textové přístupy
- End-to-end model (Donut) dosahuje nejlepších výsledků, zejména v document-level metrikách

---

## Omezení

- Závislost na kvalitě OCR (u NER přístupů)
- Relativně malý počet reálných anotovaných faktur
- Výsledky jsou omezeny na české prostředí a konkrétní strukturu dat

---

## Autor

**Tomáš Brabec**  
Bakalářský projekt – Metody extrakce informací pro analýzu faktur  
Vedoucí: Ing. Ladislav Lenc, Ph.D.

---

## Licence

Projekt je určen primárně pro studijní a výzkumné účely.

> Jedná se o výzkumný prototyp sloužící k experimentálnímu porovnání přístupů ke zpracování dokumentů, nikoliv o produkční řešení.