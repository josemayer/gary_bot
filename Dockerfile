FROM python:3.10-slim
RUN apt-get update && apt-get install -y build-essential python-dev
RUN apt-get install -y libffi-dev ffmpeg

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD python3 main.py
