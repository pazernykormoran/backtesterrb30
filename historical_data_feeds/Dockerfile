FROM python:3.8
RUN mkdir /usr/src/app
RUN apt-get update && apt-get -y install gcc libzmq3-dev
WORKDIR /usr/src/app
ADD ./historical_data_feeds/requirements.txt .
RUN pip install -r requirements.txt
ADD ./historical_data_feeds/run.py .
ADD ./historical_data_feeds ./historical_data_feeds
ADD ./libs ./libs
ADD ./strategies ./strategies
CMD ["python","-u","run.py"]