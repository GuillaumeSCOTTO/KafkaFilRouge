from confluent_kafka import Consumer, KafkaError
import json
import os
import logging
from elasticsearch import Elasticsearch
from datetime import datetime
import time
import socket

ELK_INDEX_NAME = os.getenv('ELK_INDEX_NAME')
CONSUMERS = json.loads(os.getenv('CONSUMERS_LIST'))
INITIAL_FIELDS = json.loads(os.getenv('INITIAL_FIELDS')).keys()

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_AGGREGATION_TOPIC = os.getenv('KAFKA_AGGREGATION_TOPIC')


def compute_date(time):
    return datetime.fromtimestamp(int(time))


def define_index_properties():
    properties = {'timestamp': "date"}
    for field in INITIAL_FIELDS:
        properties[field] = 'text'
    for consumer, typ in CONSUMERS.items():
        properties[consumer] = typ
    return properties


def msg_process(client, msg, dico):
    val = json.loads(msg.value().decode('utf-8'))

    if val['timestamp'] not in dico.keys():  # Première métadonnée de ce tweet reçue
        dico[val['timestamp']] = {key: value for key, value in val.items() if key != 'timestamp'}
    else:
        if len(dico[val['timestamp']]) == len(INITIAL_FIELDS) + len(CONSUMERS) - 1:  # Dernière métadonnée du tweet arrivée
            final_json = dico[val['timestamp']]
            del dico[val['timestamp']]
            for key in val.keys():
                if key not in INITIAL_FIELDS and key != 'timestamp':
                    final_json[key] = val[key]
            final_json['timestamp'] = compute_date(val['timestamp'])  # Unix Timestamp to Date
            import_data_into_ELK(client, final_json)  # On stocke dans Elastic
        else:  # Autre métadonnée du tweet arrivée mais pas la dernière
            for key in val.keys():
                if key not in INITIAL_FIELDS and key != 'timestamp':
                    dico[val['timestamp']][key] = val[key]


def import_data_into_ELK(client, data):
    logging.debug(f'##data: {data}')
    '''body = {
        'timestamp': data['timestamp'],
        'pseudo': data['pseudo'],
        'tweet': data['tweet'],
        'offense': data['offense'],
        'sentiment': data['sentiment']   
    }'''

    # Index the document with the timestamp as the index
    response = client.index(index=ELK_INDEX_NAME, body=data, id=data['timestamp'])
    if response['result'] == 'created':
        logging.debug(f"Document indexed with timestamp: {data['timestamp']}")
    else:
        logging.debug(f"Failed to index document with timestamp: {data['timestamp']}")


def main():
    # Define the Elasticsearch host
    elasticsearch_host = 'elasticsearch'  # Container name of Elasticsearch

    try:
        elasticsearch_ip = socket.gethostbyname(elasticsearch_host)
        logging.debug(f"Elasticsearch IP address: {elasticsearch_ip}")
    except socket.gaierror:
        logging.debug(f"Failed to resolve Elasticsearch hostname: {elasticsearch_host}")


    # Create the Elasticsearch client
    client = Elasticsearch(hosts=["http://" + elasticsearch_ip + ":9200"])

    # Initialize the response variable
    response = None

    # Keep checking the connection until a response is received
    while response is None:
        try:
            # Check the connection by retrieving the cluster information
            response = client.cluster.health()
            logging.debug(f"CLUSTER RESPONSE HEALTH: {response}")
        except Exception as e:
            # Handle any exceptions and log the error
            logging.error(f"Error connecting to Elasticsearch, trying again to connect: {e}")
            time.sleep(1)  # Wait for 1 second before retrying
    logging.debug(f"Connected to Elasticsearch successfully.")

    settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": define_index_properties()
        }
    }

    try:
        # Create the index with the settings and mappings above if doesn't already exist
        response = client.indices.create(index=ELK_INDEX_NAME, body=settings, ignore=400)
        logging.debug(f"INDEX CREATED: {response}")
    except Exception as e:
        logging.error(f"Error creating the index: {e}")

    delete_query = {
        "query": {
            "match_all": {}
        }
    }
    response = client.delete_by_query(index=ELK_INDEX_NAME, body=delete_query)
    logging.debug(f"DELETE RESPONSE: {response}")

    c = Consumer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'group',
        'auto.offset.reset': 'earliest'})

    c.subscribe([KAFKA_AGGREGATION_TOPIC])

    dico = {}

    try:
        while True:
            msg = c.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logging.debug(f'End of partition reached: {msg.topic()}[{msg.partition()}]')
                else:
                    logging.debug(f'Error while consuming message: {msg.error()}')
            else:
                msg_process(client, msg, dico)

    except KeyboardInterrupt:
        pass
    finally:
        c.close()


if __name__ == "__main__":
    logging.basicConfig(filename='logs_aggregation.log', encoding='utf-8', level=logging.DEBUG)

    logging.debug(f"ELK index name : {ELK_INDEX_NAME}")
    logging.debug(f"Liste des consumers : {CONSUMERS}")
    logging.debug(f"Liste des champs initiaux : {INITIAL_FIELDS}")
    logging.debug(f"Kafka bootstrap servers : {KAFKA_BOOTSTRAP_SERVERS}")
    logging.debug(f"Kafka aggregation TOPIC: {KAFKA_AGGREGATION_TOPIC}")

    main()
