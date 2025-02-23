FROM python:3.12-slim

WORKDIR /app

# Install poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY backend/pyproject.toml backend/poetry.lock ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# cors
ARG UI_URL
ENV UI_URL=$UI_URL

# Copy project files (diff step from deps for layer efficency)
COPY backend/ .

EXPOSE 8000

CMD ["poetry", "run", "fastapi", "run", "scout_platform/server/main.py", "--host", "0.0.0.0", "--port", "8000"]

