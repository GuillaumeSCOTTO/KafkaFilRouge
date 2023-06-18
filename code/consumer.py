from confluent_kafka import Consumer, KafkaError, Producer
import os
import json
import logging


KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_AGGREGATION_TOPIC = os.getenv('KAFKA_AGGREGATION_TOPIC')

INFERENCE_PYTHON_FILE = os.getenv('INFERENCE_PYTHON_FILE')
INFERENCE_CLASSIFIER_NAME = os.getenv('INFERENCE_CLASSIFIER_NAME')
INFERENCE_PYTHON_MODEL = os.getenv('INFERENCE_PYTHON_MODEL')
CONSUMERS_LIST = json.loads(os.getenv('CONSUMERS_LIST'))


def msg_process(msg):
    val = json.loads(msg.value().decode('utf-8'))

    if RETURN_TYPE == 'integer':
        result = int(inference.predict(model, val['tweet']))
    elif RETURN_TYPE == 'float':
        result = float(inference.predict(model, val['tweet']))
    else:
        result = str(inference.predict(model, val['tweet']))

    val[METADATA_NAME] = result
    with open("result.txt", "a") as f:
        f.write(str(val) + "\n")
        logging.debug(f'Msg reçu: {val}')
    return val


def acked(err, msg):
    if err is not None:
        logging.debug(f'Failed to deliver message: {err}')
    else:
        logging.debug(f'Message envoyé: {str(msg.topic()), str(msg.partition()), str(msg.value())}')


def res_send(value, producer):
    result = json.dumps(value)
    producer.produce(KAFKA_AGGREGATION_TOPIC, value=result, callback=acked)


def get_metadata_name_and_id():
    for idx, consumer in enumerate(CONSUMERS_LIST.items()):
        if INFERENCE_PYTHON_FILE.split('_')[0] == consumer[0]:
            return idx, consumer[0], consumer[1]
    return 'Rien'


def main():
    # On créé l'instance producer pour envoyer les résultats qui seront calculés
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    logging.debug('Producer done')

    c = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_NAME,
        'auto.offset.reset': 'earliest'
    })
    logging.debug('Consumer done')

    c.subscribe([KAFKA_TOPIC])
    logging.debug('Subscription done')

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
                val = msg_process(msg)
                try:
                    res_send(val, p)
                    p.flush()
                except Exception as e:
                    logging.debug(f'Error while sending message: {e}')

    except KeyboardInterrupt:
        pass
    finally:
        c.close()


if __name__ == "__main__":
    id, METADATA_NAME, RETURN_TYPE = get_metadata_name_and_id()
    KAFKA_GROUP_NAME = "group" + str(id + 1)

    logging.basicConfig(filename='logs_' + METADATA_NAME + '.log', encoding='utf-8', level=logging.DEBUG)

    logging.debug(f"Kafka bootstrap servers : {KAFKA_BOOTSTRAP_SERVERS}")
    logging.debug(f'Kafka topic : {KAFKA_TOPIC}')
    logging.debug(f"Kafka topic sur lequel sont postées les données aggrégées : {KAFKA_AGGREGATION_TOPIC}")
    logging.debug(f'Inference python file name : {INFERENCE_PYTHON_FILE}')
    logging.debug(f'Inference classifier name : {INFERENCE_CLASSIFIER_NAME}')
    logging.debug(f'Inference classifier model name : {INFERENCE_PYTHON_MODEL}')
    logging.debug(f'Liste des producteurs de métadonnées : {CONSUMERS_LIST}')
    logging.debug(f'Type de la métadonnée produite : {RETURN_TYPE}')
    logging.debug(f'Le nom de la métadonnée produite:  {METADATA_NAME}')
    logging.debug(f'Kafka group name : {KAFKA_GROUP_NAME}')

    inference = __import__(INFERENCE_PYTHON_FILE)

    if INFERENCE_CLASSIFIER_NAME != 'None':
        logging.debug(f'Il y a une classe en plus')
        locals()[INFERENCE_CLASSIFIER_NAME] = getattr(inference, INFERENCE_CLASSIFIER_NAME)

    model_path = "./" + INFERENCE_PYTHON_MODEL
    model = inference.load_model(model_path)

    main()

