import json
from typing import Any, Callable,Optional

from invoices_generator.utility.json_serializable import json_serializable


class json_encoder(json.JSONEncoder):
    def __init__(self, *args, method: Optional[str] = "to_json_donut", 
                 fallback: Optional[Callable] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.method = method
        self.fallback = fallback
        
    def default(self, o:json_serializable)->Any:
        if self.method and hasattr(o, self.method):
            return getattr(o, self.method)()
        elif self.fallback:
            return self.fallback(o)
        else:
            return super().default(o)
