FROM python:3.8
RUN mkdir /usr/src/app
RUN apt-get update && apt-get -y install gcc libzmq3-dev
WORKDIR /usr/src/app
COPY ./python_engine ./python_engine
COPY ./python_executor ./python_executor
COPY ./python_engine/run.py .
COPY ./python_engine/requirements.txt .
RUN pip install -r requirements.txt
COPY ./libs ./libs
COPY ./strategies ./strategies