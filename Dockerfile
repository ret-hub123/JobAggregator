FROM python:3.11-slim

RUN groupadd -r groupdjango && useradd -r -g groupdjango userdj

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install Django==5.2.7 \
                gunicorn==21.2.0 \
                psycopg2-binary==2.9.10 \
                pillow==11.3.0 \
                requests==2.32.5 \
                beautifulsoup4==4.14.2 \
                matplotlib==3.10.7 \
                numpy==2.3.5

COPY . .

RUN chown -R userdj:groupdjango /app
USER userdj

EXPOSE $PORT

CMD gunicorn JobAggregator.wsgi:application --bind 0.0.0.0:$PORT