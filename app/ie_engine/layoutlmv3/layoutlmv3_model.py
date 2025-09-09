import torch
from transformers import AutoModel, LayoutLMv3Model
import torch.nn as nn

from app.ie_engine.layoutlmv3.span_pooler import span_pooler

class layoutlmv3_model(nn.Module):
    
    def __init__(self, num_classes:int, num_relationships:int, model: LayoutLMv3Model):
        super().__init__()
        self.model = model
        hidden_dim = self.model.config.hidden_size
        self.ner_layer = nn.Sequential(nn.Linear(in_features = hidden_dim,
                                                out_features = hidden_dim),
                                                nn.ReLU(), nn.Linear(in_features = hidden_dim, out_features = num_classes)) #kvůli klasifikaci ner tagů
        
        self.span_pooler = span_pooler([15,16,17])

        #vstup = dva vektory o délce 768 z layoutlmv3 spojeny za sebou
        self.re_layer = nn.Sequential(nn.Linear(in_features = 2 * 3 * hidden_dim,
                                                out_features = hidden_dim),
                                                nn.ReLU(), nn.Linear(in_features = hidden_dim, out_features = num_relationships)) #kvůli klasifikaci vztahu na base_of, vat_of a none
        


    def forward(self, batch:dict[str, any], training:bool = True):
        input_ids = batch['input_ids'].long()
        bbox = batch['bbox'].long()
        pixel_values = batch['pixel_values'].float()
        attention_mask = batch['attention_mask'].long()
        spans = batch["spans"]
        words = batch["words"]
        word_input_ids_mapping = batch["word_input_ids_mapping"]

        B = input_ids.size(0)
        P = input_ids.size(1) #počet dílů na kolik byl dokument rozdělen...počet oken

        outputs = list()
        ner_tags = list()

        for p in range(P):

            px_val = pixel_values[:, p, :, :, :]
            
            inpt_ids = input_ids[:, p, :]
            
            bbx = bbox[:,p,:,:]
            
            at_msk = attention_mask[:,p,:]

            output = self.model(input_ids=inpt_ids,
                        bbox=bbx,
                        pixel_values=px_val,
                        attention_mask=at_msk).last_hidden_state[:, :512, :]  ## output má rozměry [batch_size, 709, 768], 
                                                                                                    ## 709 = 512 vektorů pro jednotlivé subtokeny a 197 pro obraz
            
            #B,512, num_classes
            ner = self.ner_layer(output)

            outputs.append(output)
            ner_tags.append(ner) #2, B, 512, 768

        outputs_BP = torch.stack(outputs, dim=1)
        outputs_list = list(outputs_BP.unbind(dim=0)) #list prvků batche, kde každý prvek batche obsahuje všechny svoje části rozsekané kvůli maximální délce 512 tokenů

        ner_BP = torch.stack(ner_tags, dim=1) #B, 2,512,768
        ner_list = list(ner_BP.unbind(dim=0))    

        spans = self.span_pooler(batch, outputs_list, training)
            
        # return {
        #     #P je počet párů spanů v dokumentu, 
        #     #S_kept je počet ponechaných spanů,
        #     #H je rozěr output vektoru layoutlmv3 pro jeden subtoken
        #     "pairs": pairs_per_doc,                # list [P, 2*(3*H)]
        #     "pair_indices": pair_indices_per_doc,  # list (i, j)  obsahuje indexy tvořící pár
        #     "pair_labels": pair_labels_per_doc,    # list [P] obsahuje labely pro dané páry

        #     "span_reprs": span_reprs_per_doc,      # list [S_kept, 3H]
        #     "span_tags": kept_tags_per_doc,        # list list[int]
            
        #     "origin2kept": origin2kept_per_doc,    # list dict
        #     "kept2origin": kept2origin_per_doc,    # list dict
        # }

        rels = list()

        #PAIRS_PER_DOC MÁ ROZMĚRY [POČET DVOJIC, 2*2304]
        for pair in spans["pairs_per_doc"]:
            if pair is not None:
                rel = self.re_layer(pair) #output má rozměry [počet dvojic, 3]
                rels.append(rel)
            else:
                rels.append(None)

        return {"ner_logits": ner_BP,
                "rel_logits": rels,
                "rel_labels": spans["pair_labels"],
                "rel_pair_indices": spans["pair_indices"],
                "rel_span_words": spans["pair_words_per_doc"]}