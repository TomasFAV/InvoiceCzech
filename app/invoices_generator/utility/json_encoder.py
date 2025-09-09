import json
from typing import Any, Callable,Optional

from app.invoices_generator.utility.json_serializable import json_serializable


class json_encoder(json.JSONEncoder):
    def __init__(self, *args, method: Optional[str] = "to_json_donut", 
                 fallback: Optional[Callable] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.method = method
        self.fallback = fallback
        
    def default(self, obj:json_serializable)->Any:
        if self.method and hasattr(obj, self.method):
            return getattr(obj, self.method)()
        elif self.fallback:
            return self.fallback(obj)
        else:
            return super().default(obj)