from typing import Any


class OperationResult:
    
    def __init__(self, ok:bool, passed_value:Any=None):
        self.ok = ok
        self.passed_value = passed_value
