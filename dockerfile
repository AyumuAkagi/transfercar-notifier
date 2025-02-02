FROM umihico/aws-lambda-selenium-python:latest

# 必要なファイルをコピー
COPY lambda/lambda_function.py .
COPY lambda/notification.py .
COPY lambda/config.py .
COPY requirements.txt .

# 依存関係のインストール
RUN pip install -r requirements.txt

# Lambda関数のタイムアウトとメモリ設定
ENV AWS_LAMBDA_FUNCTION_TIMEOUT=900
ENV AWS_LAMBDA_FUNCTION_MEMORY_SIZE=2048

CMD [ "lambda_function.lambda_handler" ]