from django import forms
from .models import Stock

class StockPredictionForm(forms.Form):
    stock_symbol = forms.CharField(
        max_length=10,
        label="Stock Symbol",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., AAPL'}),
    )
    
    prediction_days = forms.IntegerField(
        label="Prediction Days",
        min_value=1,
        max_value=30,
        initial=7,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    algorithm_choices = [
        ('linear_regression', 'Linear Regression'),
        ('arima', 'ARIMA'),
        ('lstm', 'LSTM Neural Network')
    ]
    
    algorithm = forms.ChoiceField(
        choices=algorithm_choices,
        label="Prediction Algorithm",
        initial='linear_regression',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    data_period_choices = [
        ('1mo', '1 Month'),
        ('3mo', '3 Months'),
        ('6mo', '6 Months'),
        ('1y', '1 Year'),
        ('2y', '2 Years'),
        ('5y', '5 Years'),
    ]
    
    data_period = forms.ChoiceField(
        choices=data_period_choices,
        label="Historical Data Period",
        initial='1y',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )