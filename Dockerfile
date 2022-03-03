# syntax=docker/dockerfile:1

FROM python:3.9.7-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ENV NOTION_DB_ID="your notion db id"
ENV PULL_INTERVAL="interval to pull google cal"
COPY . .
ENTRYPOINT exec python3 -u app.py -d ${NOTION_DB_ID} --pull_interval ${PULL_INTERVAL}