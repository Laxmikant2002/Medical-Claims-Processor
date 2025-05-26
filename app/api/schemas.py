from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class BillDocument(BaseModel):
    """Schema for processed bill documents."""
    type: str = Field("bill", const=True)
    hospital_name: str
    total_amount: Decimal
    date_of_service: datetime

class DischargeSummary(BaseModel):
    """Schema for processed discharge summary documents."""
    type: str = Field("discharge_summary", const=True)
    patient_name: str
    diagnosis: str
    admission_date: datetime
    discharge_date: datetime

class IDCard(BaseModel):
    """Schema for processed ID card documents."""
    type: str = Field("id_card", const=True)
    member_name: str
    member_id: str
    insurance_provider: str
    plan_number: str

class ValidationResult(BaseModel):
    """Schema for document validation results."""
    missing_documents: List[str] = Field(default_factory=list)
    discrepancies: List[str] = Field(default_factory=list)

class ClaimDecision(BaseModel):
    """Schema for claim decision."""
    status: str = Field(..., regex="^(approved|rejected)$")
    reason: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class ProcessedClaim(BaseModel):
    """Schema for the complete processed claim."""
    claim_id: str
    processing_info: dict
    documents: List[dict]  # Can be BillDocument, DischargeSummary, or IDCard
    validation: ValidationResult
    claim_decision: ClaimDecision

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        } 