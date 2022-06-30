FROM python:3.8
RUN mkdir /usr/src/app
RUN apt-get update && apt-get -y install gcc libzmq3-dev
WORKDIR /usr/src/app
COPY ./python_engine/run.py .
COPY ./python_engine/requirements.txt .
COPY ./python_engine ./python_engine
RUN pip install -r requirements.txt
COPY ./libs ./libs
COPY ./strategies ./strategies
CMD ["python","-u","run.py"]
