import argparse
import csv
import json
import socket
import sys
import os
import time
from datetime import datetime
from confluent_kafka import Producer


def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg.value()), str(err)))
    else:
        print("Topic: %s, Partition: %s, Message produced: %s, " % (str(msg.topic()), str(msg.partition()), str(msg.value())))


def rows_from_a_csv_file(filename):
    with open(filename) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in reader:
            yield row


def compute_date(time):
    return datetime.fromtimestamp(int(time))


def send_msg(timestamp, value, producer, args):
    dico = {'timestamp': timestamp, 'pseudo': value[0], 'tweet': value[1]}
    result = json.dumps(dico)
    producer.produce(args.topic, key=args.filename, value=result, callback=acked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filename', type=str, help='Time series csv file.')
    parser.add_argument('topic', type=str, help='Name of the Kafka topic to stream.')
    parser.add_argument('speed', type=float, default=1, help='Speed up time series by a given multiplicative factor.')
    args = parser.parse_args()

    conf = {'bootstrap.servers': "localhost:9092",
            'client.id': socket.gethostname()}
    producer = Producer(conf)
    firstline = True

    dir = '/'.join(os.getcwd().split('\\'))
    for row in rows_from_a_csv_file(dir + '/' + args.filename):
        try:
            if firstline is True:
                firstline = False
                timestamp = row[1]

            else:
                new_timestamp = row[1]
                diff, timestamp = ((compute_date(new_timestamp) - compute_date(timestamp))/args.speed).total_seconds(), new_timestamp
                time.sleep(diff)

            value = (row[4], row[5])
            send_msg(timestamp, value, producer, args)
            producer.flush()

        except TypeError as e:
            print(e)
            sys.exit()


if __name__ == "__main__":
    main()
