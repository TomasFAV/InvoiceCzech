from collections import defaultdict
import torch
import torch.nn as nn
from typing import Any, Dict, List, Tuple

from app.invoices_generator.core.enumerates.relationship_types import relationship_types

VAT_PERCENTAGE_TAG = 15  # vat_percentage
# FYI: 16...vat_base, 17...vat_amount (jen dokumentačně)

class span_pooler(nn.Module):
    """
    Vytvoří vektory pro spany z výstupu LayoutLMv3 a připraví kandidátní páry (X -> vat_percentage).
    Pooling spanu: concat([first, mean, last]) přes subtokény spanu.

    Očekávaný vstup `batch` (po dokumentech):
        batch["spans"][b]: {
            "tags": List[int],                    # tag id pro každý span
            "token_indices": List[List[int]]      # word-level token indexy tvořící span (v pořadí)
        }
        batch["words"][b]: List[str]              # nepovinné
        batch["word_input_ids_mapping"][b]: List[Tuple[int,int]]
            # mapping slovo -> (start_subtok, end_subtok), včetně obou krajů
        batch["relationships"][b]: {
            "span_index_a": List[int],            # originální indexy (před filtrem)
            "span_index_b": List[int],
            "relationship_type": List[int]        # kódy z relationship_types
        }
    """

    def __init__(self, allowed_span_types_ids: List[int], hidden_size: int = None):
        super().__init__()
        self.allowed_span_types = set(allowed_span_types_ids)
        self.hidden_size = hidden_size  # jen informativní; nevyžadováno

    @staticmethod
    def _span_subtoken_range(token_indices: List[int], word_to_subtok: List[List[Tuple[int, int]]]) -> List[tuple[int, int]]:
        """
        Z word-level tokenů ve spanu spočítá globální (min_start, max_end) rozsah subtokénů.
        Vrací (start, end) včetně obou hran.
        Musí vracet start a end pro každou stránku
        """

        #token indices obsahuje...kdyz mam slovo Čechova tak se rozpadne v DATECH uměle(nikoliv v encoderu) na Čech ova...token indices tedy obsahuje číslo
        # 177,181, kde to znamená id v words v datech...takže víme, že span je tvořen částmi  177, 181
        # word_to_subtok na místě 177 má dvojici (s,e) kde s znamená, kde Čech začíná v input_ids a také v hidden layeru layoutlmv3
        # to samé platí i pro index 181  

        if not token_indices:
            return list()  # prázdný rozsah (start > end)
        ranges = [] #indexy jsou jednotlivé stránky...(start, end)
        for t in token_indices:
            s,e = -1,-1
            for wts_index in range(len(word_to_subtok)):
                s,e = word_to_subtok[wts_index][t]
                if(s != -1 and e != -1):
                    break
            while(wts_index >= len(ranges)):
                ranges.append([])
            ranges[wts_index].append((s,e))

        return ranges

    @staticmethod
    def _pool_span_hidden(hidden: torch.Tensor, ranges: List[tuple[int, int]]) -> torch.Tensor:
        """
        hidden: Tensor [S, L, H]  (S=počet oken, L=délka okna, H=dim)
        start, end: globální tokenové indexy přes S*L (end včetně)
        window_len: očekávaná délka okna (default 512); pokud nesedí, vezme se L z hidden

        Vrací: Tensor [3H] = [first ⊕ mean ⊕ last]
        """

        S, L, H = hidden.shape
        # neplatný rozsah → nuly

        if len(ranges) <= 0:
            return hidden.new_zeros(3 * H)
        
        start = None

        for page_index, page in enumerate(ranges):
            if(len(page) == 0):
                continue
            else:
                start = (page_index,ranges[page_index][0][0])

        #SPANY
        end = (len(ranges)-1,ranges[-1][-1][1])#index posledního subtokenu posledního slova

        # first/last
        first = hidden[start[0], start[1]]        # [H]
        last  = hidden[end[0], end[1]]        # [H]

        
        parts = []


        #průměr přes všechny slova
        for page_index, page in enumerate(ranges):
            for word_start_id, word_end_id in page:
                for id in range(word_start_id, word_end_id+1):
                    parts.append(hidden[page_index, id])
        
        seg = torch.stack(parts, dim=0)                        # [M, H]
        mean = seg.mean(dim=0)

        return torch.cat([first, mean, last], dim=-1)                # [3H]


    def forward(self, batch: Dict[str, Any], layoutlmv3_output: List[torch.Tensor], training: bool = True):
        spans = batch["spans"]
        word_input_ids_mapping = batch["word_input_ids_mapping"] #mapping prvku z batch["words"] na (počáteční index v input_ids, poslední index v input_ids)...vrací indexy input_ids reprezentujicíí jednotlivé prkvy embedingu
        relationships = batch.get("relationships", None)

        B = len(spans)#počet batchů
        device = layoutlmv3_output[0].device
        H = layoutlmv3_output[0].size(-1) #velikost embedingu pro vložené slovo do layoutlmv3, orientačně: 768
        span_reprs_per_doc: List[torch.Tensor] = []
        kept_tags_per_doc: List[List[int]] = []
        kept_spans_per_doc: List[List[str]] = []
        origin2kept_per_doc: List[Dict[int, int]] = []
        kept2origin_per_doc: List[Dict[int, int]] = []

        # Filtr a pooling spanů
        for b in range(B):
            tags_b: List[int] = spans[b]["tags"]
            tokidx_b: List[List[int]] = spans[b]["token_indices"]
            w2s_b: List[Tuple[int, int]] = word_input_ids_mapping[b]
            hidden_b: torch.Tensor = layoutlmv3_output[b]   # [počet oken,L_b, H]

            keep_mask = [t in self.allowed_span_types for t in tags_b]
            kept_reprs: List[torch.Tensor] = []
            kept_tags: List[int] = []
            kept_spans: List[str] = []

            o2k: Dict[int, int] = {}
            k2o: Dict[int, int] = {}

            k = 0
            for i, keep in enumerate(keep_mask):
                if not keep:
                    continue
                ranges = self._span_subtoken_range(tokidx_b[i], w2s_b)
                span_vec = self._pool_span_hidden(hidden_b, ranges)
                kept_reprs.append(span_vec)
                kept_tags.append(tags_b[i])
                kept_spans.append(' '.join([batch["words"][b][idx] for idx in tokidx_b[i]]))
                o2k[i] = k
                k2o[k] = i
                k += 1

            if kept_reprs:
                span_reprs_per_doc.append(torch.stack(kept_reprs, dim=0))  # [S_kept, 3H]
            else:
                span_reprs_per_doc.append(None)
                
            # else:
            #     span_reprs_per_doc.append(torch.zeros(0, 3 * H, device=device))
            kept_spans_per_doc.append(kept_spans)
            kept_tags_per_doc.append(kept_tags)
            origin2kept_per_doc.append(o2k)
            kept2origin_per_doc.append(k2o)

        
        #Generování kandidátních párů: (cokoli != percentage) -> (percentage)
        pair_indices_per_doc: List[tuple[int, int]] = []
        pair_labels_per_doc: List[tuple[int, int]] = []

        for b in range(B):
            tags = kept_tags_per_doc[b]
            S = len(tags)
            if S == 0:
                pair_indices_per_doc.append(None)
                pair_labels_per_doc.append(None)
                continue

            idx_pct = [i for i, t in enumerate(tags) if t == VAT_PERCENTAGE_TAG]
            idx_oth = [i for i, t in enumerate(tags) if t != VAT_PERCENTAGE_TAG]

            pairs_b: List[Tuple[int, int]] = [(i, j) for i in idx_oth for j in idx_pct]

            # 3) Labely z relationships (porovnáváme v kept-indexech)
            labels_b: List[int] = []
            if relationships is not None:
                rel_b = relationships[b]
                # Přemapování všech vztáhů z datasetu do kept-indexů
                mapped_gt = {}
                for a, c, t in zip(rel_b["span_index_a"], rel_b["span_index_b"], rel_b["relationship_type"]):
                    ai = origin2kept_per_doc[b].get(a, None)
                    bi = origin2kept_per_doc[b].get(c, None)
                    if ai is not None and bi is not None:
                        mapped_gt[(ai, bi)] = t

                for (i, j) in pairs_b:
                    labels_b.append(mapped_gt.get((i, j), relationship_types.NONE.code))
            else:
                labels_b = [relationship_types.NONE.code] * len(pairs_b)

            pair_indices_per_doc.append(pairs_b)
            pair_labels_per_doc.append(labels_b)

        pairs_per_doc = list()

        for doc_index, doc in enumerate(pair_indices_per_doc):
            pairs = list()
            if(doc):
                for item_index , (i, j) in enumerate(doc):
                    pairs.append(torch.cat((span_reprs_per_doc[doc_index][i], span_reprs_per_doc[doc_index][j])))
                if(len(pairs)>0):
                    pairs_per_doc.append(torch.stack(pairs))
            else:
                pairs_per_doc.append(None)
            # else:
            #     pairs_per_doc.append(torch.empty((0,2* 3 * H)))
        #per doc znamená na prvek na batche

        return {
            #P je počet párů spanů v dokumentu, 
            #S_kept je počet ponechaných spanů,
            #H je rozěr output vektoru layoutlmv3 pro jeden subtoken
            "pairs_per_doc": pairs_per_doc,                # list [P, 2*(3*H)]
            "pair_indices": pair_indices_per_doc,  # list (i, j)  obsahuje indexy tvořící pár
            "pair_labels": pair_labels_per_doc,    # list [P] obsahuje labely pro dané páry

            "span_reprs": span_reprs_per_doc,      # list [S_kept, 3H]
            "span_tags": kept_tags_per_doc,        # list list[int]
            "pair_words_per_doc": kept_spans_per_doc,

            "origin2kept": origin2kept_per_doc,    # list dict
            "kept2origin": kept2origin_per_doc,    # list dict
        }
