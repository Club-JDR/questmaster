FROM python:3.11-slim
WORKDIR /app
RUN apt update && apt upgrade -y
RUN apt install -y locales && \
    sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

RUN apt install -y build-essential gcc
RUN python -m pip install --upgrade pip

COPY . /app
RUN python -m pip install -r requirements.txt

EXPOSE 8000
CMD [ "gunicorn",  "--bind",  "0.0.0.0:8000",  "questmaster:app"]