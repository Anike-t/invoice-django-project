from django.shortcuts import render, redirect, get_object_or_404

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.files.base import ContentFile
from io import BytesIO
from xhtml2pdf import pisa
import random
from .models import Invoice
from django.core.mail.backends.smtp import EmailBackend

def create_or_edit_invoice(request, invoice_id=None):
    if invoice_id:
        invoice = get_object_or_404(Invoice, id=invoice_id)
        is_edit = True
    else:
        invoice = None
        is_edit = False 

    if request.method == 'POST':
        bill_to = request.POST.get('bill_to')
        address = request.POST.get('address')
        place = request.POST.get('place')
        phone = request.POST.get('phone')
        date = request.POST.get('date')
        due = request.POST.get('due')
        email = request.POST.get('email')

        descriptions = request.POST.getlist('description[]')
        unit_prices = request.POST.getlist('unit_price[]')
        quantities = request.POST.getlist('quantity[]')

        invoice_items = []
        grand_total = 0

        for desc, price, qty in zip(descriptions, unit_prices, quantities):
            try:
                price = float(price)
                qty = float(qty)
                row_total = round(price * qty, 2)
                grand_total += row_total

                invoice_items.append({
                    'description': desc,
                    'unit_price': price,
                    'quantity': qty,
                    'row_total': row_total,
                })
            except ValueError:
                continue

        if invoice_items:
            if is_edit:
                
                invoice.bill_to = bill_to
                invoice.address = address
                invoice.place = place
                invoice.phone = phone
                invoice.email = email
                invoice.date = date
                invoice.due = due
                invoice.save()
            else:
            
                random_number = random.randint(100000, 999999)
                invoice = Invoice.objects.create(
                    bill_to=bill_to,
                    address=address,
                    place=place,
                    phone=phone,
                    email=email,
                    date=date,
                    due=due,
                    invoice_number=random_number
                )

            
            request.session['invoice_items'] = invoice_items
            request.session['grand_total'] = round(grand_total, 2)
            request.session['due'] = due

            return redirect('invoice_preview', invoice_id=invoice.id)

    else:
        if is_edit:
            
            context_invoice = {
                'bill_to': invoice.bill_to,
                'address': invoice.address,
                'place': invoice.place,
                'phone': invoice.phone,
                'email': invoice.email,
                'date': invoice.date.strftime('%Y-%m-%d') if invoice.date else '',
                'due': invoice.due,
                
            }
        else:
            context_invoice = {}

    return render(request, 'create_invoice.html', {
        'invoice': context_invoice,
        'is_edit': is_edit,
    })

def invoice_preview(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = request.session.get('invoice_items', [])
    grand_total = request.session.get('grand_total', 0)
    due = request.session.get('due', '')
    email_to = invoice.email

    context = {
        'invoice': invoice,
        'items': items,
        'grand_total': grand_total,
        'due': due,
        'email_to': email_to,
    }

    if request.GET.get('save_invoice') == '1':
        html = render_to_string('invoice_mail.html', context)
        result = BytesIO()
        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result)

        if not pdf.err:
            pdf_file = ContentFile(result.getvalue())
            file_name = f"invoice_{invoice.invoice_number}.pdf"
            invoice.invoice_file.save(file_name, pdf_file)
            invoice.save()
            return redirect('invoice_list')
        else:
            return HttpResponse("Error generating PDF", status=500)

    if request.GET.get('email') == '1':
        html = render_to_string('invoice_mail.html', context)
        result = BytesIO()
        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result)
        
        if not pdf.err:
            pdf_file = ContentFile(result.getvalue())
            file_name = f"invoice_{invoice.invoice_number}.pdf"
            invoice.invoice_file.save(file_name, pdf_file)
            invoice.save()

            email_backend = EmailBackend(
                host='smtp.gmail.com',
                port=587,
                username='aniket638601@gmail.com',
                password='etmg bbdd kdka axez', 
                use_tls=True
            )

            email = EmailMessage(
                subject='Your Invoice',
                body='Please find attached your invoice.',
                from_email='aniket638601@gmail.com',
                to=[email_to],
            )
            email.attach(file_name, result.getvalue(), 'application/pdf')
            email.send()
            return redirect(f"{request.path}?sent=1")
        else:
            return HttpResponse("Error generating PDF", status=500)

    return render(request, 'invoice_preview.html', context)


def invoice_list(request):
    query=request.GET.get('q','')
    invoices = Invoice.objects.all().order_by('-id')
       

    if query:
        invoices = invoices.filter(
            Q(invoice_number__startswith=query) |  
            Q(bill_to__startswith=query) |        
            Q(phone__startswith=query) |          
            Q(email__startswith=query)            
        )
    paginator = Paginator(invoices, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'invoice_list.html', {'invoices': page_obj, 'query': query, 'page_obj': page_obj})




def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice.delete()
 
 
    return redirect('invoice_list')  
## invoi/views.py
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from .models import Invoice
from datetime import datetime
import uuid
import json

from django.utils import timezone
import pytz

def schedule_invoice_email(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        
        date_str = request.POST['date']  # Format: '2025-05-02T14:30'
        scheduled_time_naive = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')

        # Convert to timezone-aware datetime in IST
        india_tz = pytz.timezone('Asia/Kolkata')
        scheduled_time = india_tz.localize(scheduled_time_naive)

        # Create crontab using IST time components
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=str(scheduled_time.minute),
            hour=str(scheduled_time.hour),
            day_of_month=str(scheduled_time.day),
            month_of_year=str(scheduled_time.month),
            day_of_week='*',
            timezone='Asia/Kolkata'  # Ensure crontab uses IST
        )

        task_name = f"send-invoice-{invoice.id}-{uuid.uuid4()}"
        PeriodicTask.objects.create(
            crontab=schedule,
            name=task_name,
            task='invoi.tasks.send_invoice_email',
            args=json.dumps([invoice.id]),
            one_off=True,
            start_time=scheduled_time,  # timezone-aware
        )
        print('PeriodicTask',PeriodicTask)

        return HttpResponseRedirect(f"?sent=1")

    return render(request, 'schedule_invoice_email.html', {'invoice': invoice})
