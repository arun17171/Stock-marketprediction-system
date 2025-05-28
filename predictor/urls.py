from django.urls import path
from predictor import views


app_name = 'predictor'

urlpatterns = [
    path('', views.index, name='index'),
    path('predict/', views.predict, name='predict'),
    path('history/', views.prediction_history, name='history'),
    path('stock-data/<str:symbol>/', views.get_stock_data, name='stock_data'),
]