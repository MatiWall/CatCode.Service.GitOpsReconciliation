FROM python:3.12-slim

ENV POETRY_HOME=/app
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV POETRY_NO_INTERACTION=true

RUN pip install poetry
RUN apt-get update && apt-get install -y git

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-dev

COPY . /app

EXPOSE 8000

CMD ["poetry", "run", "python", "main.py"]
