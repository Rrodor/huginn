from dataclasses import dataclass, field


@dataclass
class Candidat:
    nuance: str
    surname: str
    family_name: str
    sexe: str
    voix: int
    voix_inscrits: float
    voix_exprimes: float
    elu: bool = field(init=False)

    def __post_init__(self):
        self.elu = self.voix_exprimes > 50

