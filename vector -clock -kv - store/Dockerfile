FROM python:3.9-slim
RUN apt-get update && apt-get install -y iputils-ping curl
WORKDIR /app
COPY requirements.txt .
RUN pip install requests
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ .
CMD ["python", "node.py"]