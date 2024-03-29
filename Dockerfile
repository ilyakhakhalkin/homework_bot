FROM python:3.10.4-slim

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r ./requirements.txt --no-cache-dir

COPY . .

CMD python3 homework.py