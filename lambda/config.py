from datetime import datetime

# 基本設定
BASE_URL = "https://www.transfercar.com.au/search"
CHECK_INTERVAL = 300  

# 日付フィルター設定
TARGET_DATE = datetime(2025, 2, 21)

# 場所フィルター設定
LOCATIONS = {
    'from': [],  
    'to': []     
}

# 車両タイプフィルター設定
VEHICLE_TYPES = [
    # Uncomment the vehicle types you want to monitor
    # 'Campervan',    # Campervans and small motorhomes
    # 'Motorhome',    # Larger motorhomes
    # 'SUV',          # Sport Utility Vehicles
    # 'Car',          # Standard cars
    # 'Large Car',    # Larger sized cars
    # 'Medium Car',   # Medium sized cars
    # 'Small Car',    # Compact cars
    # 'Van',          # Commercial vans
    # 'People Mover', # Multi-passenger vehicles
]

# LINE通知設定
LINE_TOKEN_ENV_NAME = 'personal_token'  

# Selenium設定
SELENIUM_OPTIONS = {
    'headless': True,
    'window_size': (1920, 1080),
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# AWS設定
AWS_REGION = 'ap-northeast-1'
DYNAMODB_TABLE_NAME = 'transfer_car_known_cars'