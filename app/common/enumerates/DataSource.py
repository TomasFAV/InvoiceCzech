from enum import Enum

class DataSource(Enum):

    TOKENS = "tokens"
    SPANS = "spans"
    SEGMENTS = "segments"

    def __str__(self):
        return str(self.value)