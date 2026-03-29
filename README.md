# 📄 InvoiceCzech

Aplikace pro **extrakci informací z faktur** využívající moderní přístupy z oblasti:
- OCR
- layout-aware NLP
- multimodálních modelů

Projekt vznikl jako součást bakalářské práce:

**Metody extrakce informací pro analýzu faktur**

---

## Cíl projektu

Cílem projektu je prozkoumat a porovnat různé přístupy k vytěžování dat z dokumentů:

- modely s podporou layoutu (LayoutLMv3, LiLT)
- textové modely (BERT)
- generativní multimodální modely (Donut, Pix2Struct)

Součástí je:
- implementace jednotlivých přístupů
- jejich aplikace na dataset faktur
- aplikace umožňující zpracování png fotek faktur pomocí natrénovaných modelů(LayoutLMv3, LiLT, BERT, Donut, Pix2Struct)
- komparativní analýza jejich silných a slabých stránek

---

## 🤗 Modely

Modely použité v projektu jsou dostupné na Hugging Face:

https://huggingface.co/TomasFAV

Podporované modely:
- BERT
- LiLT
- LayoutLMv3
- Donut
- Pix2Struct

---

## Struktura projektu


    app/
    ├── client/ # GUI aplikace (Tkinter)
    ├── common/
    │ ├── models/ # AI modely
    │ ├── utils/ # OCR (Tesseract), helper funkce
    │ ├── invoice/ # reprezentace faktury
    │ └── controller/ # aplikační logika
    ├── invoices_generator/ # generování datasetu
    ├── invoice_annotator/ # anotace dat

## Přístupy
### OCR + klasifikace tokenů

vstup: text + bounding boxy
výstup: labely tokenů

#### Modely:

   - BERT
   - LiLT
   - LayoutLMv3
    
### End-to-End modely
    
vstup: obrázek
výstup: strukturovaný JSON

#### Modely:

   - Donut
   - Pix2Struct

## Poznámky
modely se stahují z Hugging Face → první spuštění může být pomalejší
GPU (CUDA) výrazně zrychlí inference
kvalita OCR zásadně ovlivňuje výsledky

## Autor

Tomáš Brabec

Bakalářská projekt:
**Metody extrakce informací pro analýzu faktur**

## Licence

Projekt je určen pro studijní a výzkumné účely.