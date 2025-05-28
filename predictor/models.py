from django.db import models
# Create your models here.
from django.utils import timezone

class Stock(models.Model):
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"

class StockPrediction(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='predictions')
    date_created = models.DateTimeField(default=timezone.now)
    prediction_date = models.DateField()
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    algorithm = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-date_created']
    
    def __str__(self):
        return f"{self.stock.symbol} prediction for {self.prediction_date}"

class StockData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='historical_data')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    
    class Meta:
        unique_together = ('stock', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.stock.symbol} data for {self.date}"

