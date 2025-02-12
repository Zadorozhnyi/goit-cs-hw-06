FROM python:3.9

WORKDIR /app
COPY . /app

RUN pip install pymongo

CMD ["python", "main.py"]
