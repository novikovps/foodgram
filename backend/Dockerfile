FROM python:3.10-slim as build
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt --no-cache-dir
COPY . .
EXPOSE 8000
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0:8000"]
