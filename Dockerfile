FROM python:2-alpine

RUN pip install nltk slackclient

RUN python -m nltk.downloader -d /usr/local/share/nltk_data all

RUN mkdir -p /app/gratzie

ADD listbot.py /app/gratzie/listbot.py

ENTRYPOINT ["python", "/app/gratzie/listbot.py"]
