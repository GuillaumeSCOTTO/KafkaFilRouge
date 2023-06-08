FROM python:3.9

WORKDIR /home

#RUN apt-get update && \
#  apt-get install -y --no-install-recommends gcc git libssl-dev g++ make && \
#  cd /tmp && git clone https://github.com/edenhill/librdkafka.git && \
#  cd librdkafka && git checkout tags/v1.7.0 && \
#  ./configure --prefix=/usr/ && make && make install && \
#  cd ../ && rm -rf librdkafka


COPY consumer_offense/requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer.py .
COPY consumer_offense/offense_inference.py .
COPY consumer_offense/model_offense_inference.pth.tar .

CMD ["python", "consumer.py"]
