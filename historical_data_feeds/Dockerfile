FROM python:3.8
RUN mkdir /usr/src/app
RUN apt-get update && apt-get -y install gcc libzmq3-dev
WORKDIR /usr/src/app
COPY ./historical_data_feeds .
RUN pip install -r requirements.txt
COPY ./libs ./libs
COPY ./strategies ./strategies