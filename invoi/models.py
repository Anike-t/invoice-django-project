from django.db import models

class Invoice(models.Model):


    invoice_number = models.CharField(max_length=20,  blank=True)
    invoice_file = models.FileField(upload_to='invoices/', null=True, blank=True)


    

   
    

    bill_to = models.CharField(max_length=200)
    address = models.TextField()
    place = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    date = models.DateField()
    email = models.EmailField(default="example@example.com")
   

    
    
    description = models.CharField(max_length=255,default='')
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    

    due = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
 
   

    def __str__(self):
        return f"Invoice for {self.bill_to} on {self.date}"
