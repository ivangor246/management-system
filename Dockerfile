FROM python:3.13.2

RUN apt-get update \
    && apt-get install -y netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.1.3 \
    POETRY_HOME="/opt/poetry" \
    PATH="/opt/poetry/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create false

WORKDIR /project

COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-root

COPY . .

EXPOSE ${ROOT_PORT}

ENTRYPOINT [ "sh", "entrypoint.sh" ]
