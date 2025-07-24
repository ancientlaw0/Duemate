from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Optional, Literal
from datetime import datetime

class NewPaymentSchema(BaseModel):
    payment_name: Annotated[str, Field(..., min_length=2, max_length=50, description="Name of payment")]
    description: Annotated[Optional[str], Field(None, min_length=1, max_length=300, description="Description of payment")]
    amount: Annotated[float, Field(..., gt=0.00, le=10000000.00, description="Amount of the payment")]
    category: Annotated[
        Literal["bills", "subscription", "loan", "tax", "other"], 
        Field(default="other", description="Type of payment")
    ]
    deadline: Annotated[datetime, Field(..., description="Deadline for payment")]
    status: Annotated[
        Literal["pending", "paid", "overdue", "cancelled"], 
        Field(..., description="Current status for payment")
    ]

    @field_validator('deadline')
    def validate_deadline(cls, v):
        if v < datetime.now():
            raise ValueError('Deadline cannot be in the past')
        return v

class EditStatusSchema(BaseModel):
     status: Annotated[
        Literal["pending", "paid", "overdue", "cancelled"], 
        Field(..., description="Current status for payment")
    ]
