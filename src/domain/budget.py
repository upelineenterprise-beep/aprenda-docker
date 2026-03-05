from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class Budget:
    company_phone: str
    client_name: str
    environments: str
    project_days: int
    material_cost: Decimal
    displacement_cost: Decimal = Decimal("0")
    commission_pct: Decimal = Decimal("0")
    interest_pct: Decimal = Decimal("0")
    payment_type: str = "avista"
    installments: int = 1
    final_price: Optional[Decimal] = None
    daily_cost: Optional[Decimal] = None
    pdf_url: Optional[str] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    id: Optional[str] = None
