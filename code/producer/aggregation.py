from confluent_kafka import Consumer, KafkaError
import json
import os
import logging


FILENAME_RESULTS = os.getenv('FILENAME_RESULTS')
KEYS = os.getenv('KEYS').split(',')
NB_CONSUMERS = int(os.getenv('NB_CONSUMERS'))

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_GROUP_NAME = os.getenv('KAFKA_GROUP_NAME')
KAFKA_AGGREGATION_TOPIC = os.getenv('KAFKA_AGGREGATION_TOPIC')


def msg_process(msg, dico):
    val = json.loads(msg.value().decode('utf-8'))
    if val['timestamp'] not in dico.keys():
        dico[val['timestamp']] = {key: value for key, value in val.items() if key != 'timestamp'}
    else:
        if len(dico[val['timestamp']]) == len(KEYS) + NB_CONSUMERS - 2:
            final_json = dico[val['timestamp']]
            del dico[val['timestamp']]
            for key in val.keys():
                if key not in KEYS:
                    final_json[key] = val[key]
                    with open(FILENAME_RESULTS, "a") as f:
                        f.write(str(final_json) + "\n")
                    logging.debug(f'##Msg reçu: {final_json}')
        else:
            for key in val.keys():
                if key not in KEYS:
                    dico[val['timestamp']][key] = val[key]


def main():
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
                msg_process(msg, dico)

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
    logging.debug(f"Kafka topic sur lequel sont postées les données aggrégées: {KAFKA_AGGREGATION_TOPIC}")

    main()
