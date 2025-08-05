from services.payment_service import get_due_payments
from utils.email_utils import send_email, send_SMS
from Flask import render_template
from datetime import datetime


def run_email_reminders():
    due_payments = get_due_payments()
    for payment in due_payments:
        user = payment.user
        if not user.email or (datetime.now().date() - payment.deadline.date() ==1):
            continue
        
        send_email(
            to=user.email,
            subject="Payment Reminder",
            html = render_template("reminder_mail.html",amount = payment.amount ,deadline=payment.deadline.strftime("%B %d, %Y"),overdue=datetime.now().date() > payment.deadline.date()),
            text=render_template("reminder.txt",amount = payment.amount,deadline=payment.deadline.strftime("%B %d, %Y"),overdue=datetime.now().date() > payment.deadline.date())
        )

def run_SMS_reminders():
    due_payments = get_due_payments()
    for payment in due_payments:
        user = payment.user
        if not user.phone_number or (datetime.now().date() - payment.deadline.date() ==1):
            continue
        
        send_SMS(
            to=user.phone_number,
            text=render_template("reminder.txt",amount = payment.amount,deadline=payment.deadline.strftime("%B %d, %Y"),overdue=datetime.now().date() > payment.deadline.date())
        )

