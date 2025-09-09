import evaluate
import pytorch_lightning
import torch
import torch.nn.functional as F
from transformers import LayoutLMv3Model


from app.ie_engine.layoutlmv3.layoutlmv3_model import layoutlmv3_model
from app.invoices_generator.core.enumerates.relationship_types import relationship_types
from app.invoices_generator.core.enumerates.token_tags import token_tags

class layoutlmv3_pl_model(pytorch_lightning.LightningModule):

    def __init__(self, ner_classes:int, re_classes:int ,model:LayoutLMv3Model, lr = 1e-4):

        super(layoutlmv3_pl_model, self).__init__()
        self.save_hyperparameters()

        self.model = layoutlmv3_model(ner_classes, re_classes,model)

        ## Metrics
        self.train_metric = evaluate.load("seqeval")
        self.val_metric = evaluate.load("seqeval")

        ## Parameters
        self.lr = lr
        self.ner_classes = ner_classes

    def forward(self, batch):
        return self.model(batch)

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=self.lr)

    def training_step(self, batch, batch_idx):
        
        ## Forward Propagatipn
        outputs = self.model(batch)
        ##výsledky a vypočítání ztráty
        predictions = outputs['ner_logits']
        predictions = torch.reshape(predictions, [predictions.shape[0], predictions.shape[1]*predictions.shape[2], predictions.shape[3]]) #[Batch, 1024, 37] ... [batch, 2*512, 37]
        
        predictions_ids = outputs['ner_logits'].argmax(-1)
        predictions_ids = torch.reshape(predictions_ids, [predictions_ids.shape[0], predictions_ids.shape[1]*predictions_ids.shape[2]]) #[Batch, 1024] ... [batch, 2*512]

        labels = batch["labels"]
        labels = torch.reshape(labels, [labels.shape[0], labels.shape[1]*labels.shape[2]]) #[Batch, 1024] ... [batch, 2*512]

        rel_predictions = outputs["rel_logits"]
        rel_predictions = [rel for rel in rel_predictions if rel is not None]
        if(len(rel_predictions)>0):
            rel_predictions_flat = torch.cat(rel_predictions)

        rel_predictions = [rel.argmax(-1) for rel in rel_predictions]

        rel_labels = outputs["rel_labels"]
        rel_labels = [torch.tensor(rel_label, device=rel_predictions_flat.device) for rel_label in rel_labels if rel_label is not None]
        if(len(rel_labels)>0):
            rel_labels_flat = torch.cat(rel_labels)

        true_predictions, true_labels = self.get_labels(predictions_ids, labels)

        ## Logging Purpose
        self.train_metric.add_batch(references=true_labels, predictions=true_predictions)
        results = self.train_metric.compute()
        loss_ner = F.cross_entropy(predictions.view(-1, self.ner_classes), labels.view(-1)) #musí mít tvar INPUT: [B, C] nebo [C], TARGET: [B]
        if(torch.is_tensor(rel_labels_flat) and torch.is_tensor(rel_predictions_flat)):
            loss_re = F.cross_entropy(rel_predictions_flat ,rel_labels_flat) #musí mít tvar INPUT: [B, C] nebo [C], TARGET: [B]
        else:
            loss_re = 0

        loss = loss_ner + loss_re

        self.log("train_loss", loss.item(), prog_bar = True)
        self.log("train_overall_fl", results["overall_f1"], prog_bar = True)
        self.log("train_overall_recall", results["overall_recall"], prog_bar = True)
        self.log("train_overall_precision", results["overall_precision"], prog_bar = True)

        return loss

    def validation_step(self, batch, batch_idx):    
        ## Forward Propagatipn
        outputs = self.model(batch)
        ##výsledky a vypočítání ztráty
        predictions = outputs['ner_logits']
        predictions = torch.reshape(predictions, [predictions.shape[0], predictions.shape[1]*predictions.shape[2], predictions.shape[3]]) #[Batch, 1024, 37] ... [batch, 2*512, 37]
        
        predictions_ids = outputs['ner_logits'].argmax(-1)
        predictions_ids = torch.reshape(predictions_ids, [predictions_ids.shape[0], predictions_ids.shape[1]*predictions_ids.shape[2]]) #[Batch, 1024] ... [batch, 2*512]

        labels = batch["labels"]
        labels = torch.reshape(labels, [labels.shape[0], labels.shape[1]*labels.shape[2]]) #[Batch, 1024] ... [batch, 2*512]

        rel_predictions = outputs["rel_logits"]
        rel_predictions = [rel for rel in rel_predictions if rel is not None]
        rel_predictions_flat = None
        if(len(rel_predictions)>0):
            rel_predictions_flat = torch.cat(rel_predictions)

        rel_predictions = [rel.argmax(-1) for rel in rel_predictions]

        rel_labels = outputs["rel_labels"]
        rel_labels = [torch.tensor(rel_label, device=rel_predictions_flat.device) for rel_label in rel_labels if rel_label is not None]
        
        rel_labels_flat = None
        if(len(rel_labels)>0):
            rel_labels_flat = torch.cat(rel_labels)

        true_predictions, true_labels = self.get_labels(predictions_ids, labels)

        if(batch_idx%10 == 0):
            for b in range(len(batch["words"])):
                for word, prediction, label in zip(batch["words"][b], true_predictions[b], true_labels[b]):
                    print(f"Text: {word} | Predikce: {prediction} | Label: {label}")
                
                print("***********************VZTAHY***************************")

                for pair_index, (x_id, y_id) in enumerate(outputs["rel_pair_indices"][b]):
                    print(f"Span A: {outputs['rel_span_words'][b][x_id]} | Span B: {outputs['rel_span_words'][b][y_id]} | Predikce:{list(relationship_types)[rel_predictions[b][pair_index]]}| Label: {list(relationship_types)[rel_labels[b][pair_index]]}")
                print("===========================KONEC===========================")

        ## Logging Purpose
        self.val_metric.add_batch(references=true_labels, predictions=true_predictions)
        results = self.val_metric.compute()

        loss_ner = F.cross_entropy(predictions.view(-1, self.ner_classes), labels.view(-1)) #musí mít tvar INPUT: [B, C] nebo [C], TARGET: [B]
        if(rel_labels_flat is not None and rel_predictions_flat is not None and torch.is_tensor(rel_labels_flat) and torch.is_tensor(rel_predictions_flat)):
            loss_re = F.cross_entropy(rel_predictions_flat ,rel_labels_flat) #musí mít tvar INPUT: [B, C] nebo [C], TARGET: [B]
        else:
            loss_re = 0

        loss = loss_ner + loss_re

        self.log("val_loss", loss.item(), prog_bar = True)
        self.log("val_overall_fl", results["overall_f1"], prog_bar = True)
        self.log("val_overall_recall", results["overall_recall"], prog_bar = True)
        self.log("val_overall_precision", results["overall_precision"], prog_bar = True)

        return loss


    def get_labels(self, predictions:any, references:any = None):

        # Transform predictions and references tensors to numpy arrays
        if predictions.device.type == "cpu":
            y_pred = predictions.detach().clone()
            if references is not None:
                y_true = references.detach().clone()
            else:
                y_true = None
        else:
            y_pred = predictions.detach().cpu().clone()
            if references is not None:
                y_true = references.detach().cpu().clone()
            else:
                y_true = None

        # true_predictions: když máme y_true, filtrujeme podle -100, jinak bereme celé
        if y_true is not None:
            true_predictions = list()
            true_labels = list()


            for pred, gold_label in zip(y_pred, y_true):
                true_predictions_document = list()
                for (p, l) in zip(pred, gold_label):
                    if l != -100:
                        true_predictions_document.append(list(token_tags)[p].text)
                true_predictions.append(true_predictions_document)

            for pred, gold_label in zip(y_pred, y_true):
                true_labels_document = list()
                for (p, l) in zip(pred, gold_label):
                    if l != -100:
                        true_labels_document.append(list(token_tags)[l].text)
                true_labels.append(true_labels_document)
            

            return true_predictions, true_labels
        else:
            true_predictions = [
                [list(token_tags)[p].text for p in pred] for pred in y_pred
            ]
            return true_predictions, None
    


class training_callback(pytorch_lightning.Callback):
    def on_train_epoch_end(self, trainer, pl_module):
        print(f"Pushing model to the hub, epoch {trainer.current_epoch}")
        pl_module.model.push_to_hub("TomasFAV/DonutInvoiceCzech",
                                    commit_message=f"Training in progress, epoch {trainer.current_epoch}")
        pl_module.processor.push_to_hub("TomasFAV/DonutInvoiceCzech",
                                    commit_message=f"Training in progress, epoch {trainer.current_epoch}")

    def on_train_end(self, trainer, pl_module):
        print(f"Pushing model to the hub after training")
        pl_module.processor.push_to_hub("TomasFAV/DonutInvoiceCzech",
                                    commit_message=f"Training done")
        pl_module.model.push_to_hub("TomasFAV/DonutInvoiceCzech",
                                    commit_message=f"Training done")
