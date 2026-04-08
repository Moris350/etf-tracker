FROM python:3.9-slim
WORKDIR /app

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
RUN pip install flask requests beautifulsoup4 playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Create Cron file
RUN echo "30 18 * * * cd /app && /usr/local/bin/python track_etf_units.py harel >> /var/log/cron.log 2>&1" > /etc/cron.d/etf_cron
RUN echo "35 18 * * * cd /app && /usr/local/bin/python track_etf_units.py tech >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "40 18 * * * cd /app && /usr/local/bin/python track_etf_units.py realestate >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "45 18 * * * cd /app && /usr/local/bin/python track_etf_units.py banks >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "50 18 * * * cd /app && /usr/local/bin/python track_etf_units.py oil >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "55 18 * * * cd /app && /usr/local/bin/python track_etf_units.py construction >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "00 19 * * * cd /app && /usr/local/bin/python track_etf_units.py ta35 >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "05 19 * * * cd /app && /usr/local/bin/python track_etf_units.py ta90 >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "10 19 * * * cd /app && /usr/local/bin/python track_etf_units.py ta125 >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron
RUN echo "00 21 * * * cd /app && /usr/local/bin/python track_etf_units.py ibi >> /var/log/cron.log 2>&1" >> /etc/cron.d/etf_cron

RUN chmod 0644 /etc/cron.d/etf_cron
RUN crontab /etc/cron.d/etf_cron
RUN touch /var/log/cron.log

COPY track_etf_units.py /app/
COPY app.py /app/
COPY templates /app/templates

EXPOSE 3333
CMD cron && python app.py