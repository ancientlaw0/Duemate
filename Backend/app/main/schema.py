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
    @classmethod
    def validate_deadline(cls, v):
        try:
            if isinstance(v, str):

                if v.endswith('Z'):
                    v = v.replace('Z', '+00:00')
                deadline_dt = datetime.fromisoformat(v)
            elif isinstance(v, datetime):
                deadline_dt = v
            else:
                raise ValueError('Invalid datetime type')
                

            return deadline_dt
            
        except ValueError as e:
            if "Deadline cannot be in the past" in str(e):
                raise e
            raise ValueError('Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')

class EditStatusSchema(BaseModel):
     status: Annotated[
        Literal["pending", "paid", "overdue", "cancelled"], 
        Field(..., description="Current status for payment")
    ]

class PaymentFilterSchema(BaseModel):
    status: Annotated[
        Optional[Literal["pending", "paid", "overdue", "cancelled"]], 
        Field(None, description="Filter by payment status")
    ]
    category: Annotated[
        Optional[Literal["bills", "subscription", "loan", "tax", "other"]], 
        Field(None, description="Filter by payment category")
    ]
    search: Annotated[
        Optional[str], 
        Field(None, min_length=1, max_length=100, description="Search in payment name and description")
    ]
    sort_by: Annotated[
        Optional[Literal["deadline", "amount", "payment_name", "status", "category"]], 
        Field("deadline", description="Field to sort by")
    ]
    sort_order: Annotated[
        Optional[Literal["asc", "desc"]], 
        Field("asc", description="Sort order")
    ]
    page: Annotated[
        Optional[int], 
        Field(1, ge=1, description="Page number")
    ]
    per_page: Annotated[
        Optional[int], 
        Field(10, ge=1, le=100, description="Items per page")
    ]

    @field_validator('search')
    def validate_search(cls, v):
        if v is not None and v.strip() == '':
            return None
        return v.strip() if v else None