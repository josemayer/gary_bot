FROM python:3.9-slim
RUN apt-get update && apt-get install -y build-essential python-dev-is-python3
RUN apt-get install -y libffi-dev ffmpeg

WORKDIR /gary
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD python3 main.py
