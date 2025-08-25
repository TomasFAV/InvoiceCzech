import json
from typing import Any

from app.invoices.utility.json_serializable import json_serializable


class json_encoder(json.JSONEncoder):
    def default(self, obj:json_serializable)->Any:
        if hasattr(obj,'to_json'):
            return obj.to_json()
        else:
            return json.JSONEncoder.default(self, obj)