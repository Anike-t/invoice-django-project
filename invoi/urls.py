from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),  
    path('invoice/<int:invoice_id>/', views.invoice_preview, name='invoice_preview'), 
    path('create-invoice/', views.create_or_edit_invoice, name='create_invoice'), 
    path('invoices/delete/<int:invoice_id>/', views.delete_invoice, name='delete_invoice'),
    path('invoices/<int:invoice_id>/edit/', views.create_or_edit_invoice, name='invoice_edit'),
]
