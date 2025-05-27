FROM python:3.12.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y

COPY requirements.txt .

RUN pip install -U pip
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]