from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class Company:
    phone: str
    name: str
    monthly_costs: Decimal
    working_days: int
    tax_pct: Decimal
    margin_pct: Decimal
    validity_days: int
    email: Optional[str] = None
    instagram: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def daily_cost(self) -> Decimal:
        if self.working_days <= 0:
            raise ValueError("Dias trabalhados deve ser maior que zero.")
        return self.monthly_costs / Decimal(self.working_days)
