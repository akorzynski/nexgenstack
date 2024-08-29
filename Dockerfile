FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python3 -m pip install poetry
WORKDIR /app
COPY . /app/
RUN poetry install --no-root

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "nexgenstack.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
