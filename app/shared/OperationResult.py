from dataclasses import dataclass
from typing import Any

@dataclass
class OperationResult:
    
    """
        Slouží pro komunikaci mezi aplikační vrstvou(Controller) a uživatelskou vrstvou
    """

    ok:bool #Zda se operace zdařila či nikoliv
    passed_value:Any = None #předávaná hodnota 
