from dataclasses import dataclass


@dataclass
class PendingFloat:
    is_real_float: bool
    value: str
