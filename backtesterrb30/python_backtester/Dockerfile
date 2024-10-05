FROM python:3.8
RUN mkdir /usr/src/app
RUN apt-get update && apt-get -y install gcc libzmq3-dev
WORKDIR /usr/src/app
ADD ./python_backtester/requirements.txt .
RUN pip install -r requirements.txt
ADD ./python_backtester/run.py .
ADD ./python_backtester ./python_backtester
ADD ./libs ./libs
ADD ./strategies ./strategies
CMD ["python","-u","run.py"]