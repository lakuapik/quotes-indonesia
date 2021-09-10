FROM python:slim

RUN pip install Pillow requests twython pydash

ENTRYPOINT ["sh", "-c", "cd scripts/autopost && python autopost.py"]