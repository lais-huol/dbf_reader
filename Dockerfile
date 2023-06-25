FROM python:3.8.17-slim-bullseye

RUN pip install --upgrade pip

RUN pip install --upgrade flake8 coverage twine
