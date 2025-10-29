FROM docker.io/python:3.14-slim AS base
ARG VENV=/venv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PATH="$VENV/bin:$PATH"

FROM base AS build
COPY requirements.txt .
RUN python -m venv "$VENV"
RUN pip install --no-cache-dir -r requirements.txt

FROM base
WORKDIR /app/
COPY --from=build "$VENV" "$VENV"
COPY geneweb_py/ app/
COPY hd/ hd/
COPY static/ static/
VOLUME /app/data/
EXPOSE 8000
CMD ["uvicorn", "app.web.app:app", "--host", "0"]
