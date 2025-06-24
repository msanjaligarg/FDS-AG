FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
COPY main.py .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask requests
#CMD ["python", "main.py"]
ENV FLASK_APP=main.py
EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
