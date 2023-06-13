from confluent_kafka import Consumer, KafkaError
import json
import os
import logging
from elasticsearch import Elasticsearch
import time ## à rajouter dans le requirements.txt
import socket

FILENAME_RESULTS = os.getenv('FILENAME_RESULTS')
KEYS = os.getenv('KEYS').split(',')
NB_CONSUMERS = int(os.getenv('NB_CONSUMERS'))

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_GROUP_NAME = os.getenv('KAFKA_GROUP_NAME')
KAFKA_AGGREGATION_TOPIC = os.getenv('KAFKA_AGGREGATION_TOPIC')



def msg_process(client, msg, dico, index_name):
    val = json.loads(msg.value().decode('utf-8'))

    if val['timestamp'] not in dico.keys():
        dico[val['timestamp']] = {key: value for key, value in val.items() if key != 'timestamp'}
        #logging.debug(f'##DICO 2: {dico}')
    else:
        if len(dico[val['timestamp']]) == len(KEYS) + NB_CONSUMERS - 2:
            final_json = dico[val['timestamp']]
            del dico[val['timestamp']]
            #logging.debug(f'##DICO APRES DEL: {dico}')
            for key in val.keys():
                if key not in KEYS:
                    final_json[key] = val[key]
            final_json['timestamp'] = val['timestamp']
            # Call the function to create the index
            logging.debug(f'##json dumps avant intégration: {json.dumps(final_json)}')
            import_data_into_ELK(client, final_json, index_name)
            with open(FILENAME_RESULTS, "a") as f:
                logging.debug(f'##Data reçue: {final_json}')
                f.write(json.dumps(final_json) + "\n")

            #logging.debug(f'##Msg reçu: {final_json}')
        else:
            for key in val.keys():
                if key not in KEYS:
                    dico[val['timestamp']][key] = val[key]



def import_data_into_ELK(client, data, index_name):
    logging.debug(f'##data: {data}')
    body = {
        'timestamp': data['timestamp'],
        'pseudo': data['pseudo'],
        'tweet': data['tweet'],
        'offense': data['offense'],
        'sentiment': data['sentiment']   
    }

    # Index the document with the timestamp as the index
    response = client.index(index=index_name, body=body, id=data['timestamp'])
    if response['result'] == 'created':
        print(f"Document indexed with timestamp: {data['timestamp']}")
    else:
        print(f"Failed to index document with timestamp: {data['timestamp']}")





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
        "properties": {
            "timestamp": {
                "type": "text"
            },
            "pseudo": {
                "type": "text"
            },
            "tweet": {
                "type": "text"
            },
            "offense": {
                "type": "integer"
            },
            "sentiment": {
                "type": "integer"
            }
        }
    }
    }
    index_name = "pfr"

    try:
        # Create the index with the settings and mappings above if doesn't already exist
        response = client.indices.create(index=index_name, body=settings, ignore=400)
        logging.debug(f"INDEX CREATED: {response}")
    except Exception as e:
        logging.error(f"Error creating the index: {e}")
        # If the index already exists, delete what's in it
        delete_query = {
            "query": {
                "match_all": {}
            }
        }
        response = client.delete_by_query(index=index_name, body=delete_query)
        logging.debug(f"DELETE RESPONSE: {response}")

    c = Consumer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_NAME})

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
                msg_process(client, msg, dico, index_name)

    except KeyboardInterrupt:
        pass
    finally:
        c.close()


if __name__ == "__main__":
    logging.basicConfig(filename='logs_aggregation.log', encoding='utf-8', level=logging.DEBUG)

    logging.debug(f"Nom du fichier de stockage des résultats : {FILENAME_RESULTS}")
    logging.debug(f"Champs communs entre les JSONs : {KEYS}")
    logging.debug(f"Nombre de métadonnées : {NB_CONSUMERS}")
    logging.debug(f"Kafka bootstrap servers : {KAFKA_BOOTSTRAP_SERVERS}")
    logging.debug(f"Kafka groupe : {KAFKA_GROUP_NAME}")
    logging.debug(f"Kafka aggregation TOPIC: {KAFKA_AGGREGATION_TOPIC}")

    main()
