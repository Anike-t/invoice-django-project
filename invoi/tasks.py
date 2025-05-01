from celery import shared_task

@shared_task
def send_invoice_email(invoice_id):
    
    print(f"Sending invoice email for invoice ID: {invoice_id}")
