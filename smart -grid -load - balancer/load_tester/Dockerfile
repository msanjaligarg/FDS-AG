FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
COPY test.py .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask requests
CMD ["python", "test.py"]
