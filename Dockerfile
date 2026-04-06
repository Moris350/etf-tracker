FROM python:3.9-slim
WORKDIR /app

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
RUN pip install flask requests beautifulsoup4 playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Create Cron file
# Harel: Every day at 18:30
RUN echo "30 18 * * * cd /app && /usr/local/bin/python track_etf_units.py harel >> /var/log/cron.log 2>&1" > /etc/cron.d/etf_cron

# IBI: Every day at 21:00
RUN echo "0 21 * * * cd /app && /usr/local/bin/python track_etf_units.py ibi >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron

RUN chmod 0644 /etc/cron.d/etf_cron
RUN crontab /etc/cron.d/etf_cron
RUN touch /var/log/cron.log

COPY track_etf_units.py /app/
COPY app.py /app/
COPY templates /app/templates

EXPOSE 3333
CMD cron && python app.py