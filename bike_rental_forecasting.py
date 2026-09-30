"""
Bike Rental Demand Forecasting System
Predicts bike rental demand based on weather, time, and seasonal patterns
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# ============================================================================
# 1. GENERATE SYNTHETIC BIKE RENTAL DATASET
# ============================================================================

def generate_bike_rental_dataset(n_days=365, random_state=42):
    """Generate synthetic bike rental demand dataset"""
    np.random.seed(random_state)
    
    # Create date range
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_days)]
    
    # Extract time-based features
    day_of_week = np.array([d.weekday() for d in dates])
    month = np.array([d.month for d in dates])
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    hour = np.random.randint(0, 24, n_days)
    
    # Generate weather features
    temperature = 20 + 10 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 3, n_days)
    humidity = 60 + 15 * np.cos(2 * np.pi * day_of_year / 365) + np.random.normal(0, 5, n_days)
    wind_speed = 10 + 5 * np.sin(2 * np.pi * day_of_year / 365) + np.random.exponential(2, n_days)
    weather_condition = np.random.choice([1, 2, 3, 4], n_days, p=[0.7, 0.15, 0.1, 0.05])  # 1=clear, 2=cloudy, 3=rainy, 4=snowy
    
    # Holiday indicator
    holidays = np.zeros(n_days)
    holidays[[0, 25, 150, 200, 300]] = 1  # Sample holidays
    
    # Generate demand based on features
    base_demand = 100
    
    # Time-based demand patterns
    hour_effect = np.where(hour < 6, 0.3, np.where(hour < 12, 0.8, np.where(hour < 18, 1.2, 0.6)))
    day_effect = np.where(day_of_week < 5, 1.0, 1.3)  # Higher on weekends
    season_effect = 1.0 + 0.3 * np.sin(2 * np.pi * day_of_year / 365)
    
    # Weather effect
    temp_effect = 1.0 + 0.02 * (temperature - 20)
    weather_effect = np.where(weather_condition == 1, 1.0, np.where(weather_condition == 2, 0.9, np.where(weather_condition == 3, 0.5, 0.2)))
    humidity_effect = 1.0 - 0.005 * (humidity - 60)
    wind_effect = 1.0 - 0.05 * wind_speed
    
    # Holiday effect
    holiday_effect = np.where(holidays == 1, 1.5, 1.0)
    
    # Calculate demand
    demand = base_demand * hour_effect * day_effect * season_effect * temp_effect * weather_effect * humidity_effect * wind_effect * holiday_effect
    demand = np.maximum(demand + np.random.normal(0, 10, n_days), 0)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Hour': hour,
        'Day_of_Week': day_of_week,
        'Month': month,
        'Day_of_Year': day_of_year,
        'Temperature': temperature,
        'Humidity': humidity,
        'Wind_Speed': wind_speed,
        'Weather_Condition': weather_condition,
        'Holiday': holidays,
        'Bike_Rentals': demand.astype(int)
    })
    
    print("=" * 90)
    print("BIKE RENTAL DEMAND FORECASTING SYSTEM - DATASET OVERVIEW")
    print("=" * 90)
    print(f"\nTotal Records: {len(df)}")
    print(f"Date Range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    print(f"Total Features: {df.shape[1] - 2}")
    print(f"\nDemand Statistics:")
    print(f"  Mean Daily Rentals: {df['Bike_Rentals'].mean():.0f}")
    print(f"  Min Daily Rentals: {df['Bike_Rentals'].min():.0f}")
    print(f"  Max Daily Rentals: {df['Bike_Rentals'].max():.0f}")
    print(f"  Std Dev: {df['Bike_Rentals'].std():.0f}")
    
    print("\nWeather Conditions Distribution:")
    print(f"  Clear (1): {sum(weather_condition == 1)} days")
    print(f"  Cloudy (2): {sum(weather_condition == 2)} days")
    print(f"  Rainy (3): {sum(weather_condition == 3)} days")
    print(f"  Snowy (4): {sum(weather_condition == 4)} days")
    
    return df

# ============================================================================
# 2. DATA PREPROCESSING
# ============================================================================

def preprocess_data(df):
    """Preprocess bike rental data"""
    df_processed = df.copy()
    
    # Create additional features
    df_processed['Is_Weekend'] = (df_processed['Day_of_Week'] >= 5).astype(int)
    df_processed['Is_Morning'] = ((df_processed['Hour'] >= 6) & (df_processed['Hour'] < 12)).astype(int)
    df_processed['Is_Evening'] = ((df_processed['Hour'] >= 17) & (df_processed['Hour'] < 21)).astype(int)
    df_processed['Is_Night'] = ((df_processed['Hour'] < 6) | (df_processed['Hour'] >= 21)).astype(int)
    
    # Separate features and target
    X = df_processed.drop(['Date', 'Bike_Rentals'], axis=1)
    y = df_processed['Bike_Rentals']
    
    # Split data (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("\n" + "=" * 90)
    print("DATA PREPROCESSING SUMMARY")
    print("=" * 90)
    print(f"Training set size: {len(X_train)} records")
    print(f"Test set size: {len(X_test)} records")
    print(f"Total features: {X.shape[1]}")
    print(f"Feature scaling: StandardScaler (mean=0, std=1)")
    
    return X_train_scaled, X_test_scaled, y_train, y_test, X, scaler, df_processed

# ============================================================================
# 3. VISUALIZATION FUNCTIONS
# ============================================================================

def visualize_demand_over_time(df):
    """Visualize bike rental demand over time"""
    fig, axes = plt.subplots(2, 1, figsize=(15, 10))
    
    # Daily demand
    daily_demand = df.groupby('Date')['Bike_Rentals'].sum()
    axes[0].plot(daily_demand.index, daily_demand.values, linewidth=2, color='#2E86AB')
    axes[0].fill_between(daily_demand.index, daily_demand.values, alpha=0.3, color='#2E86AB')
    axes[0].set_title('Daily Bike Rental Demand Over Time', fontweight='bold', fontsize=12)
    axes[0].set_ylabel('Total Rentals')
    axes[0].grid(alpha=0.3)
    
    # Monthly demand
    monthly_demand = df.groupby('Month')['Bike_Rentals'].mean()
    axes[1].bar(monthly_demand.index, monthly_demand.values, color='#A23B72', edgecolor='black', alpha=0.8)
    axes[1].set_title('Average Monthly Bike Rental Demand', fontweight='bold', fontsize=12)
    axes[1].set_xlabel('Month')
    axes[1].set_ylabel('Average Rentals')
    axes[1].set_xticks(range(1, 13))
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/demand_over_time.png', dpi=300, bbox_inches='tight')
    print("✓ Demand over time visualization saved")
    plt.close()

def visualize_weather_impact(df):
    """Visualize impact of weather on demand"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Temperature vs Demand
    axes[0, 0].scatter(df['Temperature'], df['Bike_Rentals'], alpha=0.5, s=30, color='#F18F01')
    z = np.polyfit(df['Temperature'], df['Bike_Rentals'], 2)
    p = np.poly1d(z)
    axes[0, 0].plot(sorted(df['Temperature']), p(sorted(df['Temperature'])), "r-", linewidth=2)
    axes[0, 0].set_title('Temperature vs Bike Rentals', fontweight='bold')
    axes[0, 0].set_xlabel('Temperature (°C)')
    axes[0, 0].set_ylabel('Bike Rentals')
    axes[0, 0].grid(alpha=0.3)
    
    # Humidity vs Demand
    axes[0, 1].scatter(df['Humidity'], df['Bike_Rentals'], alpha=0.5, s=30, color='#06A77D')
    z = np.polyfit(df['Humidity'], df['Bike_Rentals'], 2)
    p = np.poly1d(z)
    axes[0, 1].plot(sorted(df['Humidity']), p(sorted(df['Humidity'])), "r-", linewidth=2)
    axes[0, 1].set_title('Humidity vs Bike Rentals', fontweight='bold')
    axes[0, 1].set_xlabel('Humidity (%)')
    axes[0, 1].set_ylabel('Bike Rentals')
    axes[0, 1].grid(alpha=0.3)
    
    # Wind Speed vs Demand
    axes[1, 0].scatter(df['Wind_Speed'], df['Bike_Rentals'], alpha=0.5, s=30, color='#D62828')
    z = np.polyfit(df['Wind_Speed'], df['Bike_Rentals'], 2)
    p = np.poly1d(z)
    axes[1, 0].plot(sorted(df['Wind_Speed']), p(sorted(df['Wind_Speed'])), "r-", linewidth=2)
    axes[1, 0].set_title('Wind Speed vs Bike Rentals', fontweight='bold')
    axes[1, 0].set_xlabel('Wind Speed (km/h)')
    axes[1, 0].set_ylabel('Bike Rentals')
    axes[1, 0].grid(alpha=0.3)
    
    # Weather Condition vs Demand
    weather_labels = {1: 'Clear', 2: 'Cloudy', 3: 'Rainy', 4: 'Snowy'}
    weather_demand = df.groupby('Weather_Condition')['Bike_Rentals'].mean()
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D']
    axes[1, 1].bar([weather_labels[i] for i in weather_demand.index], weather_demand.values, 
                   color=colors, edgecolor='black', alpha=0.8)
    axes[1, 1].set_title('Weather Condition Impact on Demand', fontweight='bold')
    axes[1, 1].set_ylabel('Average Rentals')
    axes[1, 1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/weather_impact.png', dpi=300, bbox_inches='tight')
    print("✓ Weather impact visualization saved")
    plt.close()

def visualize_hourly_pattern(df):
    """Visualize hourly demand patterns"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Hourly demand
    hourly_demand = df.groupby('Hour')['Bike_Rentals'].mean()
    axes[0].plot(hourly_demand.index, hourly_demand.values, marker='o', linewidth=2, 
                 markersize=8, color='#2E86AB')
    axes[0].fill_between(hourly_demand.index, hourly_demand.values, alpha=0.3, color='#2E86AB')
    axes[0].set_title('Average Hourly Bike Rental Demand', fontweight='bold', fontsize=12)
    axes[0].set_xlabel('Hour of Day')
    axes[0].set_ylabel('Average Rentals')
    axes[0].set_xticks(range(0, 24, 2))
    axes[0].grid(alpha=0.3)
    
    # Day of week demand
    day_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_demand = df.groupby('Day_of_Week')['Bike_Rentals'].mean()
    colors_day = ['#2E86AB'] * 5 + ['#F18F01'] * 2
    axes[1].bar(range(7), day_demand.values, color=colors_day, edgecolor='black', alpha=0.8)
    axes[1].set_title('Average Daily Bike Rental Demand', fontweight='bold', fontsize=12)
    axes[1].set_ylabel('Average Rentals')
    axes[1].set_xticks(range(7))
    axes[1].set_xticklabels(day_labels, rotation=45, ha='right')
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/hourly_pattern.png', dpi=300, bbox_inches='tight')
    print("✓ Hourly pattern visualization saved")
    plt.close()

def visualize_model_comparison(results):
    """Visualize model performance comparison"""
    models = list(results.keys())
    mae_values = [results[m]['MAE'] for m in models]
    rmse_values = [results[m]['RMSE'] for m in models]
    r2_values = [results[m]['R2'] for m in models]
    
    x = np.arange(len(models))
    width = 0.25
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Error metrics
    ax1.bar(x - width, mae_values, width, label='MAE', alpha=0.8, edgecolor='black')
    ax1.bar(x, rmse_values, width, label='RMSE', alpha=0.8, edgecolor='black')
    ax1.set_title('Model Error Comparison', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Error (Rentals)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, rotation=15, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # R² Score
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    ax2.bar(models, r2_values, color=colors, edgecolor='black', alpha=0.8)
    ax2.set_title('Model R² Score Comparison', fontweight='bold', fontsize=12)
    ax2.set_ylabel('R² Score')
    ax2.set_ylim([0, 1])
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/model_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Model comparison visualization saved")
    plt.close()

def visualize_predictions_vs_actual(y_test, y_pred, model_name):
    """Visualize predictions vs actual values"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Time series comparison
    axes[0].plot(range(len(y_test)), y_test.values, label='Actual', linewidth=2, color='#2E86AB')
    axes[0].plot(range(len(y_pred)), y_pred, label='Predicted', linewidth=2, color='#F18F01', alpha=0.8)
    axes[0].set_title(f'Predictions vs Actual - {model_name}', fontweight='bold', fontsize=12)
    axes[0].set_xlabel('Test Sample')
    axes[0].set_ylabel('Bike Rentals')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    # Scatter plot
    axes[1].scatter(y_test, y_pred, alpha=0.6, s=50, color='#2E86AB', edgecolor='black')
    min_val = min(y_test.min(), y_pred.min())
    max_val = max(y_test.max(), y_pred.max())
    axes[1].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    axes[1].set_title(f'Actual vs Predicted - {model_name}', fontweight='bold', fontsize=12)
    axes[1].set_xlabel('Actual Rentals')
    axes[1].set_ylabel('Predicted Rentals')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'/home/ubuntu/predictions_{model_name.lower().replace(" ", "_")}.png', dpi=300, bbox_inches='tight')
    print(f"✓ Predictions vs actual for {model_name} saved")
    plt.close()

def visualize_feature_importance(model, feature_names):
    """Visualize feature importance from tree-based models"""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:10]  # Top 10 features
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(indices)))
    ax.barh(range(len(indices)), importances[indices], color=colors, edgecolor='black', alpha=0.8)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([feature_names[i] for i in indices])
    ax.set_title('Top 10 Feature Importance - Random Forest', fontweight='bold', fontsize=12)
    ax.set_xlabel('Importance')
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/feature_importance.png', dpi=300, bbox_inches='tight')
    print("✓ Feature importance visualization saved")
    plt.close()

# ============================================================================
# 4. MODEL BUILDING AND TRAINING
# ============================================================================

def train_models(X_train, X_test, y_train, y_test):
    """Train multiple regression models"""
    print("\n" + "=" * 90)
    print("MODEL TRAINING")
    print("=" * 90)
    
    results = {}
    models = {}
    
    # Linear Regression
    print("\nTraining Linear Regression...")
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)
    
    results['Linear Regression'] = {
        'MAE': mean_absolute_error(y_test, y_pred_lr),
        'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_lr)),
        'R2': r2_score(y_test, y_pred_lr)
    }
    models['Linear Regression'] = lr_model
    
    # Random Forest
    print("Training Random Forest Regressor...")
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    
    results['Random Forest'] = {
        'MAE': mean_absolute_error(y_test, y_pred_rf),
        'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_rf)),
        'R2': r2_score(y_test, y_pred_rf)
    }
    models['Random Forest'] = rf_model
    
    # Gradient Boosting
    print("Training Gradient Boosting Regressor...")
    gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb_model.fit(X_train, y_train)
    y_pred_gb = gb_model.predict(X_test)
    
    results['Gradient Boosting'] = {
        'MAE': mean_absolute_error(y_test, y_pred_gb),
        'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_gb)),
        'R2': r2_score(y_test, y_pred_gb)
    }
    models['Gradient Boosting'] = gb_model
    
    return results, models, y_pred_rf

# ============================================================================
# 5. MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("\n" + "=" * 90)
    print("BIKE RENTAL DEMAND FORECASTING SYSTEM")
    print("Using Machine Learning Regression Techniques")
    print("=" * 90)
    
    # Generate dataset
    print("\n[Step 1] Generating Bike Rental Dataset...")
    df = generate_bike_rental_dataset(n_days=365)
    
    # Preprocess data
    print("\n[Step 2] Preprocessing Data...")
    X_train, X_test, y_train, y_test, X_orig, scaler, df_processed = preprocess_data(df)
    
    # Generate visualizations
    print("\n[Step 3] Generating Visualizations...")
    print("Creating demand over time visualization...")
    visualize_demand_over_time(df)
    
    print("Creating weather impact visualization...")
    visualize_weather_impact(df)
    
    print("Creating hourly pattern visualization...")
    visualize_hourly_pattern(df)
    
    # Train models
    print("\n[Step 4] Training Regression Models...")
    results, models, y_pred_best = train_models(X_train, X_test, y_train, y_test)
    
    # Print results
    print("\n" + "=" * 90)
    print("MODEL PERFORMANCE RESULTS")
    print("=" * 90)
    for model_name, metrics in results.items():
        print(f"\n{model_name}:")
        print(f"  Mean Absolute Error (MAE): {metrics['MAE']:.2f} rentals")
        print(f"  Root Mean Squared Error (RMSE): {metrics['RMSE']:.2f} rentals")
        print(f"  R² Score: {metrics['R2']:.4f}")
    
    # Generate additional visualizations
    print("\n[Step 5] Generating Additional Visualizations...")
    print("Creating model comparison...")
    visualize_model_comparison(results)
    
    print("Creating predictions vs actual...")
    visualize_predictions_vs_actual(y_test, y_pred_best, 'Random Forest')
    
    print("Creating feature importance...")
    visualize_feature_importance(models['Random Forest'], X_orig.columns)
    
    print("\n" + "=" * 90)
    print("EXECUTION COMPLETED SUCCESSFULLY")
    print("=" * 90)
    print("\nGenerated Visualizations:")
    print("  1. demand_over_time.png")
    print("  2. weather_impact.png")
    print("  3. hourly_pattern.png")
    print("  4. model_comparison.png")
    print("  5. predictions_random_forest.png")
    print("  6. feature_importance.png")
    
    return df, X_train, X_test, y_train, y_test, results, models, df_processed

if __name__ == "__main__":
    df, X_train, X_test, y_train, y_test, results, models, df_processed = main()
