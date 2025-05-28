from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import Stock, StockPrediction, StockData
from .forms import StockPredictionForm
from .data_fetcher import fetch_stock_data, get_stock_info
from .ml_models import StockPredictor
import pandas as pd
import json
import requests
from decimal import Decimal

def index(request):
    """Home page view"""
    form = StockPredictionForm()
    recent_predictions = StockPrediction.objects.all()[:5]
    
    context = {
        'form': form,
        'recent_predictions': recent_predictions,
    }
    return render(request, 'predictor/index.html', context)

def predict(request):
    """Handle stock prediction requests"""
    if request.method == 'POST':
        form = StockPredictionForm(request.POST)
        
        if form.is_valid():
            # Get form data
            symbol = form.cleaned_data['stock_symbol'].upper()
            prediction_days = form.cleaned_data['prediction_days']
            algorithm = form.cleaned_data['algorithm']
            data_period = form.cleaned_data['data_period']
            
            # Fetch stock data
            session = requests.Session()
            session.headers.update({'User-Agent': 'Mozilla/5.0'})

            stock_data = fetch_stock_data(symbol, period=data_period, session=session)

            
            if stock_data is None or stock_data.empty:
                messages.error(request, f"Could not fetch data for {symbol}. Please check the symbol and try again.")
                return redirect('predictor:index')
            
            # Get stock info
            stock_info = get_stock_info(symbol)
            
            # Make prediction
            predictor = StockPredictor(stock_data, algorithm=algorithm)
            prediction_result = predictor.predict(prediction_days=prediction_days)
            
            # Save prediction to database
            stock = get_object_or_404(Stock, symbol=symbol)
            
            for pred in prediction_result['predictions']:
                StockPrediction.objects.create(
                    stock=stock,
                    prediction_date=pred['date'],
                    predicted_price=pred['price'],
                    confidence_score=prediction_result['confidence'],
                    algorithm=prediction_result['algorithm']
                )
            
            # Prepare data for charts
            historical_dates = stock_data['Date'].dt.strftime('%Y-%m-%d').tolist()
            historical_prices = stock_data['Close'].round(2).tolist()
            
            prediction_dates = [pred['date'].strftime('%Y-%m-%d') for pred in prediction_result['predictions']]
            prediction_prices = [pred['price'] for pred in prediction_result['predictions']]
            
            context = {
                'stock_symbol': symbol,
                'stock_info': stock_info,
                'prediction_result': prediction_result,
                'historical_dates': json.dumps(historical_dates),
                'historical_prices': json.dumps(historical_prices),
                'prediction_dates': json.dumps(prediction_dates),
                'prediction_prices': json.dumps(prediction_prices),
                'algorithm': prediction_result['algorithm'],
                'confidence': prediction_result['confidence'],
            }
            
            return render(request, 'predictor/prediction.html', context)
    else:
        form = StockPredictionForm()
    
    return render(request, 'predictor/index.html', {'form': form})

def prediction_history(request):
    """View for prediction history"""
    predictions = StockPrediction.objects.all()
    
    # Group by stock and date
    grouped_predictions = {}
    for prediction in predictions:
        key = f"{prediction.stock.symbol}_{prediction.date_created.date()}"
        if key not in grouped_predictions:
            grouped_predictions[key] = {
                'stock': prediction.stock,
                'date_created': prediction.date_created,
                'predictions': []
            }
        grouped_predictions[key]['predictions'].append(prediction)
    
    context = {
        'grouped_predictions': list(grouped_predictions.values())
    }
    
    return render(request, 'predictor/history.html', context)

def get_stock_data(request, symbol):
    """API endpoint to fetch stock data"""
    period = request.GET.get('period', '1y')
    
    # Fetch and return data
    data = fetch_stock_data(symbol, period=period)
    
    if data is None:
        return JsonResponse({'error': f'Could not fetch data for {symbol}'}, status=400)
    
    # Convert to JSON-serializable format
    result = {
        'dates': data['Date'].dt.strftime('%Y-%m-%d').tolist(),
        'prices': data['Close'].round(2).tolist(),
        'volumes': data['Volume'].tolist(),
    }
    
    return JsonResponse(result)