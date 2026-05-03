FROM python:3.12-alpine

LABEL maintainer="Tássio Carvalho"
LABEL description="Timesheet Analyzer — UnMEP Dev Jr. challenge"

WORKDIR /app

COPY data.json .
COPY main.py   .

CMD ["python", "-u", "main.py"]
