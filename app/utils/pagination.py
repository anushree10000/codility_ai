from dataclasses import dataclass
from typing import Any


@dataclass
class PaginationParams:
    page: int = 1
    per_page: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def paginated_response(items: list[Any], total: int, params: PaginationParams) -> dict:
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "per_page": params.per_page,
        "total_pages": (total + params.per_page - 1) // params.per_page,
    }
