from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),  
    path('invoice/<int:invoice_id>/', views.invoice_preview, name='invoice_preview'), 
    path('create-invoice/', views.create_invoice, name='create_invoice'), 
]
