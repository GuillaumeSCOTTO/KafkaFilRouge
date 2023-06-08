import csv
import json
import sys
import os
import time
import logging
from datetime import datetime
from confluent_kafka import Producer


FILENAME_DATA = os.getenv('FILENAME_DATA')
SPEED = os.getenv('SPEED')
SPEED = int(SPEED)
logging.debug(f"Speed : {SPEED}", type(SPEED))

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC')


def acked(err, msg):
    if err is not None:
        logging.debug("Failed to deliver message: %s: %s" % (str(msg.value()), str(err)))
    else:
        logging.debug("Topic: %s, Partition: %s, Message produced: %s, " % (str(msg.topic()), str(msg.partition()), str(msg.value())))


def rows_from_a_csv_file(filename):
    with open(filename) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in reader:
            yield row


def compute_date(time):
    return datetime.fromtimestamp(int(time))


def send_msg(timestamp, value, producer):
    dico = {'timestamp': timestamp, 'pseudo': value[0], 'tweet': value[1]}
    result = json.dumps(dico)
    producer.produce(KAFKA_TOPIC, value=result, callback=acked)


def main():

    conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
    producer = Producer(conf)
    logging.debug("Producer started")
    firstline = True

    dir = '/'.join(os.getcwd().split('\\'))
    logging.debug(f"Chemin du csv : {type(FILENAME_DATA), FILENAME_DATA}")
    for row in rows_from_a_csv_file(FILENAME_DATA):
        try:
            if firstline is True:
                firstline = False
                timestamp = row[1]

            else:
                new_timestamp = row[1]
                diff, timestamp = ((compute_date(new_timestamp) - compute_date(timestamp))/SPEED).total_seconds(), new_timestamp
                time.sleep(diff)

            value = (row[4], row[5])
            send_msg(timestamp, value, producer)
            producer.flush()

        except TypeError as e:
            logging.debug(f'Error while sending message: {e}')
            sys.exit()


if __name__ == "__main__":

    logging.basicConfig(filename='logs_producer.log', encoding='utf-8', level=logging.DEBUG)

    logging.debug(f"Speed : {os.getenv('SPEED')}")
    logging.debug(f"Type speed : {type(os.getenv('SPEED'))}")
    #logging.debug(f"Speed2 : {SPEED}")
    logging.debug(f"Nom du fichier de données : {FILENAME_DATA}")
    logging.debug(f"Vitesse de production des données : {SPEED}")
    logging.debug(f"Kafka bootstrap servers : {KAFKA_BOOTSTRAP_SERVERS}")
    logging.debug(f"Kafka topic sur lequel sont postées les données : {KAFKA_TOPIC}")

    main()
