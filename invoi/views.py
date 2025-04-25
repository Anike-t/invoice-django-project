from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from .models import Invoice
from xhtml2pdf import pisa
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models import Q
import random
from django.core.paginator import Paginator


def create_invoice(request):
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
           

            request.session['invoice_'] = invoice_items
            request.session['invoice_items'] = invoice_items
            request.session['grand_total'] = round(grand_total, 2)
            request.session['due'] = due
            

            return redirect('invoice_preview', invoice_id=invoice.id)

    return render(request, 'create_invoice.html')

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
    paginator = Paginator(invoices, 9)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'invoice_list.html', {'invoices': page_obj, 'query': query, 'page_obj': page_obj})

