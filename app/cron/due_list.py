from models import Payment
from datetime import datetime, timedelta

def get_due_payments():
    deadline = datetime.now() + timedelta(days=2)
    return Payment.query.filter(Payment.deadline <= deadline).all()