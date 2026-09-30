"""
Bike Rental Time-Series Analysis Utilities
Provides utilities for time-series decomposition, trend analysis, and forecasting
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler

class TimeSeriesAnalyzer:
    """
    Analyzes time-series patterns in bike rental data
    """
    
    def __init__(self, df):
        """Initialize the analyzer with bike rental data"""
        self.df = df
        
    def decompose_trend(self):
        """Decompose time-series into trend, seasonal, and residual components"""
        daily_demand = self.df.groupby('Date')['Bike_Rentals'].sum()
        
        # Calculate trend (7-day moving average)
        trend = daily_demand.rolling(window=7).mean()
        
        # Calculate seasonal component (7-day cycle)
        seasonal = daily_demand - trend
        
        # Calculate residual
        residual = daily_demand - trend - seasonal
        
        return {
            'Original': daily_demand,
            'Trend': trend,
            'Seasonal': seasonal,
            'Residual': residual
        }
    
    def analyze_seasonal_patterns(self):
        """Analyze seasonal patterns in bike rental demand"""
        seasonal_analysis = {}
        
        # Monthly seasonality
        monthly_stats = self.df.groupby('Month')['Bike_Rentals'].agg(['mean', 'std', 'min', 'max'])
        seasonal_analysis['Monthly'] = monthly_stats
        
        # Daily seasonality (day of week)
        daily_stats = self.df.groupby('Day_of_Week')['Bike_Rentals'].agg(['mean', 'std', 'min', 'max'])
        seasonal_analysis['Daily'] = daily_stats
        
        # Hourly seasonality
        hourly_stats = self.df.groupby('Hour')['Bike_Rentals'].agg(['mean', 'std', 'min', 'max'])
        seasonal_analysis['Hourly'] = hourly_stats
        
        return seasonal_analysis
    
    def identify_peak_periods(self, percentile=75):
        """Identify peak demand periods"""
        threshold = self.df['Bike_Rentals'].quantile(percentile / 100)
        peak_periods = self.df[self.df['Bike_Rentals'] >= threshold]
        
        peak_analysis = {
            'Peak_Threshold': threshold,
            'Peak_Count': len(peak_periods),
            'Peak_Percentage': len(peak_periods) / len(self.df) * 100,
            'Peak_Hours': peak_periods['Hour'].mode().values,
            'Peak_Days': peak_periods['Day_of_Week'].mode().values,
            'Peak_Months': peak_periods['Month'].mode().values
        }
        
        return peak_analysis
    
    def analyze_weather_correlation(self):
        """Analyze correlation between weather and demand"""
        correlations = {
            'Temperature': self.df['Temperature'].corr(self.df['Bike_Rentals']),
            'Humidity': self.df['Humidity'].corr(self.df['Bike_Rentals']),
            'Wind_Speed': self.df['Wind_Speed'].corr(self.df['Bike_Rentals'])
        }
        
        return correlations
    
    def forecast_simple_exponential_smoothing(self, alpha=0.3, steps=30):
        """Simple exponential smoothing forecast"""
        daily_demand = self.df.groupby('Date')['Bike_Rentals'].sum()
        
        forecast = []
        last_value = daily_demand.iloc[-1]
        
        for _ in range(steps):
            forecast_value = alpha * last_value + (1 - alpha) * daily_demand.mean()
            forecast.append(forecast_value)
            last_value = forecast_value
        
        return forecast
    
    def calculate_demand_statistics(self):
        """Calculate comprehensive demand statistics"""
        stats = {
            'Total_Rentals': self.df['Bike_Rentals'].sum(),
            'Average_Daily': self.df.groupby('Date')['Bike_Rentals'].sum().mean(),
            'Average_Hourly': self.df['Bike_Rentals'].mean(),
            'Peak_Hour_Demand': self.df.groupby('Hour')['Bike_Rentals'].mean().max(),
            'Off_Peak_Hour_Demand': self.df.groupby('Hour')['Bike_Rentals'].mean().min(),
            'Weekend_Demand': self.df[self.df['Day_of_Week'] >= 5]['Bike_Rentals'].mean(),
            'Weekday_Demand': self.df[self.df['Day_of_Week'] < 5]['Bike_Rentals'].mean(),
            'Holiday_Demand': self.df[self.df['Holiday'] == 1]['Bike_Rentals'].mean(),
            'Non_Holiday_Demand': self.df[self.df['Holiday'] == 0]['Bike_Rentals'].mean()
        }
        
        return stats


class DemandOptimizer:
    """
    Optimizes bike distribution based on predicted demand
    """
    
    def __init__(self, total_bikes=500):
        """Initialize optimizer with total bike fleet size"""
        self.total_bikes = total_bikes
        
    def calculate_optimal_distribution(self, predicted_demand_by_station):
        """Calculate optimal bike distribution across stations"""
        total_demand = sum(predicted_demand_by_station.values())
        
        distribution = {}
        for station, demand in predicted_demand_by_station.items():
            allocation = int((demand / total_demand) * self.total_bikes)
            distribution[station] = allocation
        
        return distribution
    
    def identify_rebalancing_needs(self, current_inventory, predicted_demand):
        """Identify which stations need rebalancing"""
        rebalancing_needs = {}
        
        for station in current_inventory.keys():
            current = current_inventory[station]
            predicted = predicted_demand.get(station, 0)
            
            if predicted > current:
                rebalancing_needs[station] = {
                    'Type': 'Deficit',
                    'Amount': predicted - current,
                    'Priority': 'High' if predicted - current > 50 else 'Medium'
                }
            elif predicted < current:
                rebalancing_needs[station] = {
                    'Type': 'Surplus',
                    'Amount': current - predicted,
                    'Priority': 'Low'
                }
        
        return rebalancing_needs


def generate_and_save_bike_datasets(output_dir='/home/ubuntu'):
    """
    Generate and save all sample bike rental datasets
    """
    print("Generating bike rental time-series datasets...")
    
    # Generate bike rental dataset
    from bike_rental_forecasting import generate_bike_rental_dataset
    
    df = generate_bike_rental_dataset(n_days=365)
    
    # Save raw dataset
    print("  Saving raw bike rental dataset...")
    df.to_csv(f'{output_dir}/bike_rental_data.csv', index=False)
    print(f"  ✓ Raw dataset saved")
    
    # Perform time-series analysis
    print("  Performing time-series analysis...")
    analyzer = TimeSeriesAnalyzer(df)
    
    # Decompose trend
    decomposition = analyzer.decompose_trend()
    
    # Analyze seasonal patterns
    seasonal_patterns = analyzer.analyze_seasonal_patterns()
    
    seasonal_df = pd.DataFrame({
        'Month': seasonal_patterns['Monthly'].index,
        'Avg_Demand': seasonal_patterns['Monthly']['mean'].values,
        'Std_Dev': seasonal_patterns['Monthly']['std'].values,
        'Min_Demand': seasonal_patterns['Monthly']['min'].values,
        'Max_Demand': seasonal_patterns['Monthly']['max'].values
    })
    
    seasonal_df.to_csv(f'{output_dir}/seasonal_patterns.csv', index=False)
    print(f"  ✓ Seasonal patterns saved")
    
    # Identify peak periods
    print("  Identifying peak demand periods...")
    peak_analysis = analyzer.identify_peak_periods()
    
    peak_df = pd.DataFrame({
        'Metric': ['Peak Threshold', 'Peak Count', 'Peak Percentage'],
        'Value': [
            f"{peak_analysis['Peak_Threshold']:.0f}",
            f"{peak_analysis['Peak_Count']}",
            f"{peak_analysis['Peak_Percentage']:.1f}%"
        ]
    })
    
    peak_df.to_csv(f'{output_dir}/peak_periods.csv', index=False)
    print(f"  ✓ Peak periods saved")
    
    # Weather correlation analysis
    print("  Analyzing weather correlations...")
    weather_corr = analyzer.analyze_weather_correlation()
    
    weather_df = pd.DataFrame({
        'Weather_Factor': list(weather_corr.keys()),
        'Correlation': list(weather_corr.values())
    })
    
    weather_df.to_csv(f'{output_dir}/weather_correlation.csv', index=False)
    print(f"  ✓ Weather correlation saved")
    
    # Calculate demand statistics
    print("  Calculating demand statistics...")
    demand_stats = analyzer.calculate_demand_statistics()
    
    stats_df = pd.DataFrame({
        'Metric': list(demand_stats.keys()),
        'Value': list(demand_stats.values())
    })
    
    stats_df.to_csv(f'{output_dir}/demand_statistics.csv', index=False)
    print(f"  ✓ Demand statistics saved")
    
    # Generate forecast
    print("  Generating demand forecast...")
    forecast = analyzer.forecast_simple_exponential_smoothing(alpha=0.3, steps=30)
    
    forecast_df = pd.DataFrame({
        'Day': range(1, 31),
        'Forecasted_Demand': forecast
    })
    
    forecast_df.to_csv(f'{output_dir}/demand_forecast.csv', index=False)
    print(f"  ✓ Demand forecast saved")
    
    # Generate hourly demand profile
    print("  Generating hourly demand profile...")
    hourly_profile = df.groupby('Hour')['Bike_Rentals'].agg(['mean', 'std', 'min', 'max'])
    hourly_profile.to_csv(f'{output_dir}/hourly_profile.csv')
    print(f"  ✓ Hourly profile saved")
    
    return df, analyzer, demand_stats


if __name__ == '__main__':
    df, analyzer, stats = generate_and_save_bike_datasets()
    
    print("\nDataset Summary:")
    print(f"Total Records: {len(df)}")
    print(f"Date Range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    
    print("\nDemand Statistics:")
    for metric, value in stats.items():
        print(f"  {metric}: {value:.2f}")
    
    print("\nWeather Correlation:")
    weather_corr = analyzer.analyze_weather_correlation()
    for factor, corr in weather_corr.items():
        print(f"  {factor}: {corr:.3f}")
