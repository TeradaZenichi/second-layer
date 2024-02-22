FROM python:3.10
EXPOSE 5000

WORKDIR /src
RUN apt-get update
RUN yes | apt-get install build-essential
RUN yes | apt-get install python3-dev
RUN yes | apt-get install jq
RUN yes | apt-get install tzdata

COPY requirements.txt /src
RUN pip install -U pip
RUN pip install --no-cache-dir -r requirements.txt
COPY src /src

CMD [ "uwsgi", "app.ini" ]