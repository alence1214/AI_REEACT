from typing import Optional
from pydantic import BaseModel

class HandleInvoice(BaseModel):
    service_detail: Optional[str]
    invoice_detail: Optional[str]
    payment_method: Optional[str]
    bill_from: int
    bill_to: int
    total_amount: Optional[str]
    status: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    stipe_id: str
    pdf_url: str
    