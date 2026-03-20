from enum import Enum

class EventSource(str, Enum):
    IMAGE_CANVAS   = "image_canvas"
    ENTITIES_PANEL = "entities_panel"
    LABELS_PANEL   = "labels_panel"