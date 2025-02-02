import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
from config import *  # 設定ファイルからインポート
import re
from selenium.webdriver.chrome.service import Service
import boto3

# .envファイルを読み込む
load_dotenv()

# 環境変数から取得
line_access_token = os.getenv(LINE_TOKEN_ENV_NAME)

if line_access_token is None:
    raise ValueError(f"{LINE_TOKEN_ENV_NAME} が設定されていません。.envファイルを確認してください。")

class TransferCarNotifier:
    def __init__(self, line_token):
        try:
            self.line_token = line_token
            self.base_url = BASE_URL
            
            self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            self.table = self.dynamodb.Table(DYNAMODB_TABLE_NAME)
            
            try:
                self.table.table_status
            except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
                raise
            
            self.known_cars = self._load_known_cars()
            
            chrome_options = Options()
            chrome_options.binary_location = '/opt/chrome/chrome'
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--user-data-dir=/tmp/chrome-user-data')
            chrome_options.page_load_timeout = 30
            chrome_options.set_capability('timeouts', {
                'implicit': 10000,
                'pageLoad': 30000,
                'script': 30000
            })
            
            service = Service(
                executable_path='/opt/chromedriver',
                log_path='/tmp/chromedriver.log'
            )

            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            raise

    def _load_known_cars(self):
        try:
            response = self.table.scan()
            return {item['car_id'] for item in response.get('Items', [])}
        except Exception as e:
            return set()

    def _save_car_id(self, car_id):
        try:
            self.table.put_item(
                Item={
                    'car_id': car_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception as e:
            pass

    def check_new_cars(self):
        try:
            self.driver.get(self.base_url)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tile-shadowed"))
            )
            
            vehicles = self.driver.find_elements(By.CLASS_NAME, "tile-shadowed")
            new_cars = 0

            for vehicle in vehicles:
                try:
                    end_date_str = vehicle.find_element(By.CSS_SELECTOR, '.route-location-name:last-child div').text
                    end_date_str = end_date_str.replace('To ', '')
                    
                    try:
                        end_date = datetime.strptime(end_date_str + ' 2025', '%d %b %Y')
                    except ValueError:
                        end_date = datetime.strptime(end_date_str + ' 2024', '%d %b %Y')
                    
                    if end_date >= TARGET_DATE:
                        car_data = {
                            'id': vehicle.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('/')[-1].split('.')[0],
                            'title': vehicle.find_element(By.CLASS_NAME, 'vehicle-title').text,
                            'from_location': vehicle.find_element(By.CSS_SELECTOR, '.route-locations .route-location-name:first-child').text,
                            'to_location': vehicle.find_element(By.CSS_SELECTOR, '.route-locations .route-location-name:last-child').text,
                            'dates': (
                                vehicle.find_element(By.CSS_SELECTOR, '.route-location-name:first-child div').text + ' - ' +
                                vehicle.find_element(By.CSS_SELECTOR, '.route-location-name:last-child div').text
                            ),
                            'price': vehicle.find_element(By.CLASS_NAME, 'nb-days').text.strip(),
                            'url': vehicle.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                        }
                        
                        try:
                            paid_days = vehicle.find_element(By.CLASS_NAME, 'paid-days').text.strip()
                            if paid_days and paid_days != '&nbsp;':
                                car_data['paid_days'] = paid_days
                        except:
                            pass
                        
                        try:
                            remaining = vehicle.find_element(By.CSS_SELECTOR, '.badges .badge-warning strong').text
                            car_data['remaining'] = remaining
                        except:
                            pass
                        
                        from_location = car_data['from_location']
                        to_location = car_data['to_location']
                        
                        if (not LOCATIONS['from'] or from_location in LOCATIONS['from']) and \
                           (not LOCATIONS['to'] or to_location in LOCATIONS['to']):
                            
                            if not VEHICLE_TYPES or car_data['title'] in VEHICLE_TYPES:
                                if self._is_new_car(car_data['id']):
                                    message = self._create_notification_message(car_data)
                                    self.send_line_notification(message)
                                    new_cars += 1
                                    
                except Exception as e:
                    raise
                    
        except Exception as e:
            raise

    def _create_notification_message(self, car):
        try:
            from_location = re.sub(r'From \d{1,2} [A-Za-z]{3}', '', car['from_location']).strip()
            to_location = re.sub(r'To \d{1,2} [A-Za-z]{3}', '', car['to_location']).strip()
            
            message = f"🚗 新しい車両が見つかりました！\n\n"
            message += f"🚙 {car['title']}\n"
            message += f"📍 {from_location} → {to_location}\n"
            message += f"📅 {car['dates']}\n"
            if 'price' in car:
                message += f"💰 {car['price']}\n"
            if 'paid_days' in car:
                message += f"➕ {car['paid_days']}\n"
            if 'remaining' in car:
                message += f"📊 {car['remaining']}\n"
            message += f"🔗 {car['url']}"
            
            return message
            
        except Exception as e:
            raise

    def send_line_notification(self, message):
        try:
            if not self.line_token:
                raise ValueError("LINE tokenが設定されていません")
            
            url = 'https://notify-api.line.me/api/notify'
            headers = {
                'Authorization': f'Bearer {self.line_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {'message': message}
            
            status_response = requests.get('https://notify-api.line.me/api/status', headers=headers)
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code != 200:
                response.raise_for_status()
            
        except Exception as e:
            raise

    def run(self, check_interval=CHECK_INTERVAL):
        while True:
            self.check_new_cars()
            time.sleep(check_interval)

    def _is_new_car(self, car_id):
        try:
            is_new = car_id not in self.known_cars
            if is_new:
                self._save_car_id(car_id)
                self.known_cars.add(car_id)
            return is_new
        except Exception as e:
            raise

if __name__ == "__main__":
    LINE_TOKENS = line_access_token
    notifier = TransferCarNotifier(LINE_TOKENS)
    notifier.run()