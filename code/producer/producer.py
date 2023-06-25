import csv
import json
import sys
import os
import time
import logging
from datetime import datetime
from confluent_kafka import Producer


FILENAME_DATA = os.getenv('FILENAME_DATA')
SPEED = int(os.getenv('SPEED'))
TIMESTAMP_FIELD = int(os.getenv('TIMESTAMP_FIELD')) - 1
INITIAL_FIELDS = {k: v-1 for k, v in json.loads(os.getenv('INITIAL_FIELDS')).items()}

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


def send_msg(timestamp, values, producer):
    values['timestamp'] = timestamp
    result = json.dumps(values)
    producer.produce(KAFKA_TOPIC, value=result, callback=acked)


def get_other_fields(row):
    dico = {}
    for k,v in INITIAL_FIELDS.items():
        dico[k] = row[v]
    return dico


def main():
    conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
    producer = Producer(conf)
    logging.debug("Producer started")
    firstline = True

    dir = '/'.join(os.getcwd().split('\\'))
    for row in rows_from_a_csv_file(FILENAME_DATA):
        actual_timestamp = str(int(time.time()))
        try:
            if firstline is True:
                firstline = False
                timestamp = row[TIMESTAMP_FIELD]

            else:
                new_timestamp = row[TIMESTAMP_FIELD]
                diff, timestamp = ((compute_date(new_timestamp) - compute_date(timestamp))/SPEED).total_seconds(), new_timestamp
                logging.debug(f"New timestamp: {compute_date(actual_timestamp)}, Time sleep: {diff}")
                time.sleep(diff)

            send_msg(actual_timestamp, get_other_fields(row), producer)
            producer.flush()

        except TypeError as e:
            logging.debug(f'Error while sending message: {e}')
            sys.exit()


if __name__ == "__main__":
    logging.basicConfig(filename='logs_producer.log', encoding='utf-8', level=logging.DEBUG)

    logging.debug(f"Nom du fichier de données : {FILENAME_DATA}")
    logging.debug(f"Vitesse de production des données : {SPEED}")
    logging.debug(f"Emplacement du champ timestamp : {TIMESTAMP_FIELD}")
    logging.debug(f"Emplacement des autres champs : {INITIAL_FIELDS}")
    logging.debug(f"Kafka bootstrap servers : {KAFKA_BOOTSTRAP_SERVERS}")
    logging.debug(f"Kafka topic sur lequel sont postées les données : {KAFKA_TOPIC}")

    main()
