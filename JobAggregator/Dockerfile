FROM python:3.11-slim

RUN groupadd -r groupdjango && useradd -r -g groupdjango userdj

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000


WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN chown -R userdj:groupdjango /app
USER userdj

CMD ["gunicorn", "JobAggregator.wsgi:application", "--bind", "0.0.0.0:$PORT"]