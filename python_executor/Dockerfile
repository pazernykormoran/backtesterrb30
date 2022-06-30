FROM python:3.8
RUN mkdir /usr/src/app
RUN apt-get update && apt-get -y install gcc libzmq3-dev
WORKDIR /usr/src/app
COPY ./python_executor/run.py .
COPY ./python_executor/requirements.txt .
COPY ./python_executor ./python_executor
RUN pip install -r requirements.txt
COPY ./libs ./libs
COPY ./strategies ./strategies
CMD ["python","-u","run.py"]