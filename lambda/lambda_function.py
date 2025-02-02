import json
import os
from notification import TransferCarNotifier
from config import *
import subprocess

def lambda_handler(event, context):
    try:
        result = subprocess.run(['ls', '-la', '/opt/'], capture_output=True, text=True)
        result = subprocess.run(['ls', '-la', '/opt/chrome-linux64/'], capture_output=True, text=True)
        result = subprocess.run(['/opt/chrome/chrome', '--version'], capture_output=True, text=True)
        result = subprocess.run(['/opt/chromedriver', '--version'], capture_output=True, text=True)
        
        notifier = TransferCarNotifier(os.getenv(LINE_TOKEN_ENV_NAME))
        notifier.check_new_cars()
        
        return {
            'statusCode': 200,
            'body': json.dumps('Success')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }