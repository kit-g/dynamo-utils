from typing import Dict, Any


class PublicModel:
    def public(self) -> Dict[str, Any]:
        raise NotImplementedError
