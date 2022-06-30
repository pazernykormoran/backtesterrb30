FROM python:3.8
RUN mkdir /usr/src/app
RUN apt-get update && apt-get -y install gcc libzmq3-dev
WORKDIR /usr/src/app
COPY ./python_backtester/run.py .
COPY ./python_backtester/requirements.txt .
COPY ./python_backtester ./python_backtester
RUN pip install -r requirements.txt
COPY ./libs ./libs
COPY ./strategies ./strategies
CMD ["python","-u","run.py"]