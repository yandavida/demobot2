from dataclasses import dataclass

@dataclass(frozen=True)
class AppendResult:
    applied: bool
