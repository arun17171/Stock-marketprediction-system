import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import statsmodels.api as sm
from decimal import Decimal
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class StockPredictor:
    def __init__(self, data, algorithm='linear_regression'):
        """Initialize the stock predictor with historical data"""
        self.data = data.copy()
        self.algorithm = algorithm
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        # Ensure data is sorted by date
        if 'Date' in self.data.columns:
            self.data.sort_values('Date', inplace=True)
        
    def preprocess_data(self):
        """Preprocess data for model training"""
        df = self.data.copy()
        
        # Feature engineering
        df['MA5'] = df['Close'].rolling(window=5).mean()  # 5-day moving average
        df['MA20'] = df['Close'].rolling(window=20).mean()  # 20-day moving average
        df['Return'] = df['Close'].pct_change()  # Daily return
        df['Volatility'] = df['Return'].rolling(window=20).std()  # 20-day volatility
        
        # Add day of week as a feature (one-hot encoded)
        if 'Date' in df.columns:
            df['DayOfWeek'] = pd.to_datetime(df['Date']).dt.dayofweek
            day_dummies = pd.get_dummies(df['DayOfWeek'], prefix='Day')
            df = pd.concat([df, day_dummies], axis=1)
        
        # Drop NaN values resulting from rolling calculations
        df.dropna(inplace=True)
        
        return df
        
    def train_linear_regression(self, df, prediction_days=7):
        """Train a linear regression model"""
        # Features for linear regression
        features = ['Open', 'High', 'Low', 'Volume', 'MA5', 'MA20', 'Volatility']
        
        # Add day of week features if they exist
        day_columns = [col for col in df.columns if col.startswith('Day_')]
        if day_columns:
            features.extend(day_columns)
        
        # Use available features
        features = [f for f in features if f in df.columns]
        
        X = df[features].values
        y = df['Close'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train the model
        self.model = LinearRegression()
        self.model.fit(X_scaled, y)
        
        # Evaluate on training data
        y_pred = self.model.predict(X_scaled)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        confidence = max(0, 100 - (rmse / np.mean(y) * 100))
        
        # Predict future prices
        last_row = df.iloc[-1:][features].values
        last_scaled = self.scaler.transform(last_row)
        
        predictions = []
        current_pred = self.model.predict(last_scaled)[0]
        
        for i in range(prediction_days):
            # Update the prediction based on the previous prediction
            # This is a simple approach; in reality, you would need to generate future features as well
            pred_date = pd.to_datetime(df.iloc[-1]['Date']) + pd.Timedelta(days=i+1)
            predictions.append({
                'date': pred_date.date(),
                'price': round(float(current_pred * (1 + 0.005 * (np.random.random() - 0.5))), 2),
            })
            current_pred = predictions[-1]['price']
        
        return {
            'predictions': predictions,
            'confidence': round(confidence, 2),
            'algorithm': 'Linear Regression'
        }
        
    def train_arima(self, df, prediction_days=7):
        """Train an ARIMA model"""
        # ARIMA modeling requires time series data
        ts = df['Close']
        
        # Fit ARIMA model (p, d, q) = (5, 1, 0)
        # These parameters can be optimized using auto_arima from pmdarima
        model = sm.tsa.ARIMA(ts, order=(5, 1, 0))
        self.model = model.fit()
        
        # Make prediction
        forecast = self.model.forecast(steps=prediction_days)
        
        # Calculate confidence
        y_pred = self.model.predict(start=len(ts)-30, end=len(ts)-1)
        mse = mean_squared_error(ts[-30:], y_pred)
        rmse = np.sqrt(mse)
        confidence = max(0, 100 - (rmse / np.mean(ts[-30:]) * 100))
        
        # Format predictions
        predictions = []
        last_date = pd.to_datetime(df.iloc[-1]['Date'])
        
        for i, price in enumerate(forecast):
            pred_date = last_date + pd.Timedelta(days=i+1)
            predictions.append({
                'date': pred_date.date(),
                'price': round(float(price), 2),
            })
        
        return {
            'predictions': predictions,
            'confidence': round(confidence, 2),
            'algorithm': 'ARIMA'
        }
    
    def mock_lstm(self, df, prediction_days=7):
        """
        Mock LSTM implementation 
        (In a real app, you would implement proper LSTM with TensorFlow/Keras)
        """
        # For demonstration, we'll simulate LSTM predictions
        # In a real app, you'd implement a proper LSTM network here
        ts = df['Close'].values
        
        # Mock predictions with some realistic patterns
        last_price = ts[-1]
        trend = (ts[-1] - ts[-20]) / 20  # Simple trend calculation
        
        predictions = []
        last_date = pd.to_datetime(df.iloc[-1]['Date'])
        
        for i in range(prediction_days):
            # Add trend with some randomness
            next_price = last_price + trend + np.random.normal(0, abs(trend * 2))
            pred_date = last_date + pd.Timedelta(days=i+1)
            
            predictions.append({
                'date': pred_date.date(),
                'price': round(float(next_price), 2),
            })
            
            last_price = next_price
        
        # Mock confidence score
        confidence = 85.0 + np.random.normal(0, 5)
        
        return {
            'predictions': predictions,
            'confidence': round(confidence, 2),
            'algorithm': 'LSTM Neural Network (Mock)'
        }
    
    def predict(self, prediction_days=7):
        """Make stock price predictions"""
        # Preprocess data
        processed_data = self.preprocess_data()
        
        # Choose algorithm and predict
        if self.algorithm == 'linear_regression':
            return self.train_linear_regression(processed_data, prediction_days)
        elif self.algorithm == 'arima':
            return self.train_arima(processed_data, prediction_days)
        elif self.algorithm == 'lstm':
            return self.mock_lstm(processed_data, prediction_days)
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")