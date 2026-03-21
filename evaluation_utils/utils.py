from PIL import Image
from zss import Node
import zss
from nltk import edit_distance
import pytesseract


########################pomocné metody pro evaluaci v google collab#############################

def get_ocr_data_for_layoutlm(image: Image.Image, lang: str = "ces"):
    """
    Provede OCR a vrátí data připravená pro processor.feature_extractor (LayoutLMv3).
    """
    ocr_df = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)

    words = []
    boxes = []
    width, height = image.size

    for i in range(len(ocr_df["text"])):
        # Filtrujeme prázdné řetězce a whitespace
        word = ocr_df["text"][i].strip()
        if word != "":
            words.append(word)

            # Tesseract dává: left, top, width, height
            x, y, w, h = ocr_df["left"][i], ocr_df["top"][i], ocr_df["width"][i], ocr_df["height"][i]

            # Normalizace na rozsah 0-1000 pro LayoutLMv3
            # x1, y1 (vlevo nahoře), x2, y2 (vpravo dole)
            normalized_box = [
                int(1000 * (x / width)),
                int(1000 * (y / height)),
                int(1000 * ((x + w) / width)),
                int(1000 * ((y + h) / height))
            ]
            boxes.append(normalized_box)

    return words, boxes


import re

def token2json(tokens, is_inner_value=False):
    output = {}
    # Matches <s_tag>content</s_tag>
    pattern = r"<s_(?P<key>[^>]+)>(?P<value>.*?)<\s*/\s*s_(?P=key)>"

    matches = list(re.finditer(pattern, tokens, re.DOTALL | re.IGNORECASE))

    if not matches:
        # If no tags, treat as leaf node or raw text
        return tokens.strip()

    for match in matches:
        key = match.group("key")
        value_str = match.group("value").strip()

        # Recursive step for nested tags
        if "<s_" in value_str:
            value = token2json(value_str, is_inner_value=True)
        else:
            # Handle list splitting by <sep/>
            parts = [v.strip() for v in value_str.split("<sep/>") if v.strip()]
            value = parts[0] if len(parts) == 1 else parts

        # Grouping logic for repeating keys
        if key in output:
            if isinstance(output[key], list):
                output[key].append(value)
            else:
                output[key] = [output[key], value]
        else:
            output[key] = value

    return output if output else tokens

from typing import Any, Dict, List, Tuple, Union

def ned(s1:str, s2:str)->float:
    """
    Vrací normal edit distance
    """
    max_len = max(len(s1), len(s2))
    return (edit_distance(s1, s2)/max_len) if max_len != 0 else 0

#################################################čištění hodnot#######################################################
import re

def _normalize_date(value: str) -> str:
    value = str(value).strip()
    if not value:
        return ""

    # sjednocení oddělovačů
    value = value.replace("-", ".").replace("/", ".")

    # vytáhni datum typu 3.1.2026 nebo 03.01.2026
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
    if not m:
        return ""

    day = str(int(m.group(1)))
    month = str(int(m.group(2)))
    year = m.group(3)

    return f"{day}.{month}.{year}"


def _normalize_total(value: str) -> str:
    value = str(value).strip()
    if not value:
        return ""

    # nech jen čísla, čárku a tečku
    value = re.sub(r"[^0-9,\.]", "", value)

    if not value:
        return ""

    # pokud je tam jen tečka, změň ji na čárku
    if "," not in value and "." in value:
        # vezmeme poslední tečku jako desetinný oddělovač
        parts = value.split(".")
        if len(parts) == 2:
            value = parts[0] + "," + parts[1]
        else:
            value = "".join(parts[:-1]) + "," + parts[-1]

    # pokud je tam více čárek nebo kombinace bordelu, nech poslední oddělovač jako desetinný
    value = value.replace(".", ",")
    parts = value.split(",")

    if len(parts) == 1:
        return parts[0]

    integer_part = "".join(parts[:-1])
    decimal_part = parts[-1]

    if integer_part == "":
        integer_part = "0"

    return f"{integer_part},{decimal_part}" if decimal_part != "" else integer_part


def _normalize_lower_alnum(value: str) -> str:
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


def _normalize_tax_id(value: str) -> str:
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


def _normalize_register_id(value: str) -> str:
    value = str(value).strip()
    value = re.sub(r"[^0-9]", "", value)
    return value


def _normalize_bank_account(value: str) -> str:
    value = str(value).strip()
    if not value:
        return ""

    # nech čísla a lomítko
    value = re.sub(r"[^0-9/]", "", value)

    # více lomítek -> nech první jako oddělovač, zbytek smaž
    if value.count("/") > 1:
        parts = value.split("/")
        value = parts[0] + "/" + "".join(parts[1:])

    return value



def _normalize_symbol(value: str) -> str:
    value = str(value).strip()
    value = re.sub(r"[^0-9]", "", value)
    return value


def clean_value(key, value, predictions:bool = False) -> str:
    if value is None:
        return ""

    key = str(key).strip().lower()
    value = str(value).strip()
    
    if predictions:

        if not value:
            return ""

        if key == "bic":
            return _normalize_lower_alnum(value)

        if key == "iban":
            return _normalize_lower_alnum(value)

        if key == "total":
            return _normalize_total(value)

        if key in {"cust_tax_id", "supp_tax_id"}:
            return _normalize_tax_id(value)

        if key in {"cust_register_id", "supp_register_id"}:
            return _normalize_register_id(value)

        if key in {"due_date", "issue_date", "taxable_supply_date"}:
            return _normalize_date(value)

        if key in {"const_symbol"}:
            return _normalize_symbol(value)

        if key == "bank_account_number":
            return _normalize_bank_account(value)
    
    else:
        
        if key == "total":
            return _normalize_total(value)

        if key in {"due_date", "issue_date", "taxable_supply_date"}:
            return _normalize_date(value)

    return value.strip().lower()


#zkopírováno z repozitáře clovai/donut a lehce modifikováno
def flatten(data: dict):
        """
        Convert Dictionary into Non-nested Dictionary
        Example:
            input(dict)
                {
                    "menu": [
                        {"name" : ["cake"], "count" : ["2"]},
                        {"name" : ["juice"], "count" : ["1"]},
                    ]
                }
            output(list)
                [
                    ("menu.name", "cake"),
                    ("menu.count", "2"),
                    ("menu.name", "juice"),
                    ("menu.count", "1"),
                ]
        """
        flatten_data = list()

        def _flatten(value, key=""):
            if type(value) is dict:
                for child_key, child_value in value.items():
                    _flatten(child_value, f"{key}.{child_key}" if key else child_key)
                if len(value.items()) == 0:
                    flatten_data.append((key, ""))
            elif type(value) is list:
                for value_item in value:
                    _flatten(value_item, key)
                if(len(value) == 0):
                    flatten_data.append((key, ""))
            else:
                flatten_data.append((key, value))

        _flatten(data)
        return flatten_data

def normalize_text(x):
    if x is None:
        return ""

    if not isinstance(x, str):
        x = str(x)

    x = x.strip().lower()

    if not x:
        return ""

    x = x.replace("\u00a0", " ")
    x = re.sub(r"\s+", " ", x)

    # fix "4. 80" -> "4.80", "4 , 80" -> "4,80"
    x = re.sub(r"(\d)\s*([.,])\s*(\d)", r"\1\2\3", x)

    return x

#zkopírováno z repozitáře clovai/donut a lehce modifikováno
def normalize_dict(data: Union[Dict, List, Any], predictions:bool = False):
        """
        Sort by value, while iterate over element if data is list
        """
        if not data:
            return {}

        if isinstance(data, dict):
            new_data = dict()
            for key in sorted(data.keys(), key=lambda k: (len(k), k)):
                value = clean_value(key, normalize_text(data[key]), predictions)
                new_data[key] = value

        elif isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                new_data = []
                for item in data:
                    item = normalize_dict(item, predictions)
                    if item:
                        new_data.append(item)
            else:
                new_data = [normalize_text(item) for item in data if type(item) in {str, int, float}]
        else:
            try:
              new_data = normalize_text(str(data))
            except ValueError:
              new_data = normalize_text(data)

        return new_data

##################################### Pro výpočet accuracy###############################################

#zkopírováno z repozitáře clovai/donut
def update_cost(node1: Node, node2: Node):
        """
        Update cost for tree edit distance.
        If both are leaf node, calculate string edit distance between two labels (special token '<leaf>' will be ignored).
        If one of them is leaf node, cost is length of string in leaf node + 1.
        If neither are leaf node, cost is 0 if label1 is same with label2 othewise 1
        """
        label1 = node1.label
        label2 = node2.label
        label1_leaf = "<leaf>" in label1
        label2_leaf = "<leaf>" in label2
        if label1_leaf == True and label2_leaf == True:
            return edit_distance(label1.replace("<leaf>", ""), label2.replace("<leaf>", ""))
        elif label1_leaf == False and label2_leaf == True:
            return 1 + len(label2.replace("<leaf>", ""))
        elif label1_leaf == True and label2_leaf == False:
            return 1 + len(label1.replace("<leaf>", ""))
        else:
            return int(label1 != label2)

#zkopírováno z repozitáře clovai/donut
def insert_and_remove_cost(node: Node):
        """
        Insert and remove cost for tree edit distance.
        If leaf node, cost is length of label name.
        Otherwise, 1
        """
        label = node.label
        if "<leaf>" in label:
            return len(label.replace("<leaf>", ""))
        else:
            return 1
        
#zkopírováno z repozitáře clovai/donut
def construct_tree_from_dict(data: Union[Dict, List], node_name: str = None):
        """
        Convert Dictionary into Tree

        Example:
            input(dict)

                {
                    "menu": [
                        {"name" : ["cake"], "count" : ["2"]},
                        {"name" : ["juice"], "count" : ["1"]},
                    ]
                }

            output(tree)
                                     <root>
                                       |
                                     menu
                                    /    \
                             <subtree>  <subtree>
                            /      |     |      \
                         name    count  name    count
                        /         |     |         \
                  <leaf>cake  <leaf>2  <leaf>juice  <leaf>1
         """
        if node_name is None:
            node_name = "<root>"

        node = Node(node_name)

        if isinstance(data, dict):
            for key, value in data.items():
                kid_node = construct_tree_from_dict(value, key)
                node.addkid(kid_node)
        elif isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                for item in data:
                    kid_node = construct_tree_from_dict(
                        item,
                        "<subtree>",
                    )
                    node.addkid(kid_node)
            else:
                for item in data:
                    node.addkid(Node(f"<leaf>{item}"))
        #aby normalize dict nemusel vracet jenom listy
        elif isinstance(data, str):
            node.addkid(Node(f"<leaf>{data}"))
        else:
            raise Exception(data, node_name)
        return node

############################################GRAFY###########################################

import matplotlib.pyplot as plt
import numpy as np

def plot_field_level_f1(field_accuracy: dict):
    # připrav data
    data = [
        (field, correct / total, total)
        for field, (correct, total) in field_accuracy.items()
        if total > 0
    ]

    # seřadit podle accuracy (nejhorší nahoře → lepší pro debug)
    data = sorted(data, key=lambda x: x[1])

    fields, accuracies, _ = zip(*data)

    # plot
    plt.figure()
    plt.barh(fields, accuracies)

    # osa a grid
    plt.xlim(0, 1)
    plt.xticks(np.arange(0, 1.1, 0.1))
    plt.grid(axis="x", linestyle="--", alpha=0.5)

    plt.xlabel("Accuracy")
    plt.title("Field-level Accuracy")

    plt.tight_layout()
    plt.show()

##########################################METRIKY###############################################

#zkopírováno z repozitáře clovai/donut
def cal_f1(preds: List[dict], answers: List[dict], max_ned:float = 0.0):
        """
        Calculate global F1 accuracy score (field-level, micro-averaged) by counting all true positives, false negatives and false positives
        """
        total_tp, total_fn_or_fp = 0, 0
        for pred, answer in zip(preds, answers):
            pred, answer = flatten(normalize_dict(pred, True)), flatten(normalize_dict(answer))
            for pred_field in pred:
                total_fn_or_fp += 1 #pro případ, když nenajdu hodnotu v ground-truth
                for answ_field in answer:
                    if(answ_field[0] == pred_field[0] and ned(pred_field[1], answ_field[1]) <= max_ned):
                        total_tp += 1
                        total_fn_or_fp -= 1 #našel jsem v gt takže musím vrátit zpět
                        answer.remove(answ_field)
                        break

            total_fn_or_fp += len(answer)
        return total_tp / (total_tp + total_fn_or_fp / 2)


from collections import defaultdict

def field_level_f1(preds: List[dict], answers: List[dict]):
        """
        Calculate global F1 accuracy score (field-level, micro-averaged) by counting all true positives, false negatives and false positives
        """
        field_accuracy = defaultdict(lambda: (0.0, 0.0))
        field_errors = defaultdict(list) #obsahuje list dvojic predikce, ground_truth

        for pred, answer in zip(preds, answers):
            pred, answer = flatten(normalize_dict(pred, True)), flatten(normalize_dict(answer))
            for answ_field in answer:
                key:str = answ_field[0]

                if answ_field in pred:
                    field_accuracy[key] = (field_accuracy[key][0]+1, field_accuracy[key][1]+1)
                else:
                    field_accuracy[key] = (field_accuracy[key][0], field_accuracy[key][1]+1)

                    for pred_field in pred:
                        if(pred_field[0] == key):

                            field_errors[key].append((pred_field[1], answ_field[1]))


        return field_accuracy, field_errors

#zkopírováno z repozitáře clovai/donut
def cal_acc(pred: dict, answer: dict):
        """
        Calculate normalized tree edit distance(nTED) based accuracy.
        1) Construct tree from dict,
        2) Get tree distance with insert/remove/update cost,
        3) Divide distance with GT tree size (i.e., nTED),
        4) Calculate nTED based accuracy. (= max(1 - nTED, 0 ).
        """
        pred = construct_tree_from_dict(normalize_dict(pred, True))
        answer = construct_tree_from_dict(normalize_dict(answer))
        return max(
            0,
            1
            - (
                zss.distance(
                    pred,
                    answer,
                    get_children=zss.Node.get_children,
                    insert_cost=insert_and_remove_cost,
                    remove_cost=insert_and_remove_cost,
                    update_cost=update_cost,
                    return_operations=False,
                )
                / zss.distance(
                    construct_tree_from_dict(normalize_dict({})),
                    answer,
                    get_children=zss.Node.get_children,
                    insert_cost=insert_and_remove_cost,
                    remove_cost=insert_and_remove_cost,
                    update_cost=update_cost,
                    return_operations=False,
                )
            ),
        )


def cal_precision(preds: List[dict], answers: List[dict]):
        """
        Calculate global precision score (field-level, micro-averaged) by counting all true positives, false negatives and false positives
        """
        total_tp, total_fn, total_fp = 0, 0, 0
        for pred, answer in zip(preds, answers):
            pred, answer = flatten(normalize_dict(pred, True)), flatten(normalize_dict(answer))
            for field in pred:
                if field in answer:
                    total_tp += 1
                    answer.remove(field)
                else:
                  total_fp += 1


            total_fn += len(answer)
        return total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0


def cal_recall(preds: List[dict], answers: List[dict]):
    total_tp, total_fn = 0, 0

    for pred, answer in zip(preds, answers):
        pred = flatten(normalize_dict(pred, True))
        answer = flatten(normalize_dict(answer))

        for field in pred:
            if field in answer:
                total_tp += 1
                answer.remove(field)

        total_fn += len(answer)

    return total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0

def cal_ned(preds: List[dict], answers: List[dict]):
    ned_val = 0.0
    values_count = 0

    for pred, answer in zip(preds, answers):
        pred = flatten(normalize_dict(pred, True))
        answer = flatten(normalize_dict(answer))

        for answ_field in answer:
            key = answ_field[0]

            field_ned = 1.0

            for pred_field in pred:
                if(key == pred_field[0]):
                    field_ned = ned(pred_field[1], answ_field[1])
                    break
            
            ned_val += field_ned
            values_count += 1

    return ned_val/values_count


import numpy

def compute_metrics(preds: List[dict], answers: List[dict]):
  document_exact_match = 0

  f1_scores = list()

  preds = normalize_dict(preds, True)
  answers = normalize_dict(answers, False)

  micro_f1 = cal_f1(preds, answers)
  micro_f1_1 = cal_f1(preds, answers, 0.1)
  micro_precision = cal_precision(preds, answers)
  micro_recall = cal_recall(preds, answers)
  micro_ned = cal_ned(preds, answers)

  mean_acc = 0.0
  mean_f1 = 0.0 
  mean_f1_1 = 0.0
  mean_ned = 0.0

  f1_standard_deviation = 0.0

  for pred_json, gt_json in zip(preds, answers):
    document_f1 = cal_f1([pred_json], [gt_json])
    document_f1_1 = cal_f1([pred_json], [gt_json], 0.1)
    if(document_f1 == 1):
      document_exact_match += 1

    document_acc = cal_acc(pred_json, gt_json)

    mean_f1 += document_f1
    mean_f1_1 += document_f1_1
    mean_acc += document_acc
    mean_ned += cal_ned([pred_json], [gt_json])

    f1_scores.append(document_f1)


  mean_f1 = mean_f1/len(preds)
  mean_f1_1 = mean_f1_1/len(preds)
  mean_acc = mean_acc/len(preds)
  mean_ned = mean_ned/len(preds)
  document_exact_match = document_exact_match/len(preds)

  f1_standard_deviation = numpy.std(f1_scores, ddof=1 if len(f1_scores) > 1 else 0)

  f1_P50 = numpy.percentile(f1_scores, 50)
  f1_P25 = numpy.percentile(f1_scores, 25)
  f1_P05 = numpy.percentile(f1_scores, 5)

  return {"document_exact_match": document_exact_match, "micro-ned": micro_ned, "micro-recall":  micro_recall, "micro-precision": micro_precision,"micro-f1": micro_f1, "macro-ned":mean_ned, "macro-f1":mean_f1, "macro-f1-dev": f1_standard_deviation,"macro-f1-P50": f1_P50, "macro-f1-P25": f1_P25, "macro-f1-P05": f1_P05, "macro-f1-min": numpy.min(f1_scores),
          "accuracy": mean_acc, "fuzzy-micro-f1": micro_f1_1, "fuzzy-macro-f1": mean_f1_1}