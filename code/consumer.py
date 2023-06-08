from confluent_kafka import Consumer, KafkaError, Producer
import os
import json
import logging


KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_GROUP_NAME = os.getenv('KAFKA_GROUP_NAME')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_AGGREGATION_TOPIC = os.getenv('KAFKA_AGGREGATION_TOPIC')

INFERENCE_PYTHON_FILE = os.getenv('INFERENCE_PYTHON_FILE')
INFERENCE_CLASSIFIER_NAME = os.getenv('INFERENCE_CLASSIFIER_NAME')
INFERENCE_PYTHON_MODEL = os.getenv('INFERENCE_PYTHON_MODEL')


def msg_process(msg):
    val = json.loads(msg.value().decode('utf-8'))
    result = int(inference.predict(model, val['tweet']))
<<<<<<< HEAD
    val[inf_module_name.split('_')[0]] = result
=======
    val[INFERENCE_PYTHON_FILE.split('_')[0]] = result
>>>>>>> antoine
    with open("result.txt", "a") as f:
        f.write(str(val) + "\n")
        logging.debug(f'## Msg reçu: {val}')
    return val


def acked(err, msg):
    if err is not None:
<<<<<<< HEAD
        logging.debug(f'##Failed to deliver message: {err}')
    else:
        logging.debug(f'##Message envoyé: {str(msg.topic()), str(msg.partition()), str(msg.value())}')
        
def res_send(value,producer):
    
    try:
        result = json.dumps(value)
    except Exception as e:
        logging.debug(f'##Error while dumping message: {e}')

    try:
        producer.produce(TOPIC_FOR_SEND, value=result, callback=acked)
    except Exception as e:
        logging.debug(f'##Error when loading the producer: {e}')
   
=======
        logging.debug(f'## Failed to deliver message: {err}')
    else:
        logging.debug(f'## Message envoyé: {str(msg.topic()), str(msg.partition()), str(msg.value())}')


def res_send(value, producer):
    result = json.dumps(value)
    producer.produce(KAFKA_AGGREGATION_TOPIC, value=result, callback=acked)
>>>>>>> antoine


def main():
    # On créé l'instance producer pour envoyer les résultats qui seront calculés
<<<<<<< HEAD
    producer_for_res = Producer({'bootstrap.servers': "kafka:29092",
            'client.id': socket.gethostname()})

=======
    p = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    logging.debug('## Producer done')
>>>>>>> antoine

    c = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_NAME
    })
    logging.debug('## Consumer done')

    c.subscribe([KAFKA_TOPIC])
    logging.debug('## Subscription done')

    try:
        while True:
            msg = c.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logging.debug(f'## End of partition reached: {msg.topic()}[{msg.partition()}]')
                else:
                    logging.debug(f'## Error while consuming message: {msg.error()}')
            else:
                val = msg_process(msg)
                try:
                    res_send(val, p)
                    p.flush()
                except Exception as e:
                    logging.debug(f'## Error while sending message: {e}')

    except KeyboardInterrupt:
        pass
    finally:
        c.close()


if __name__ == "__main__":
    logging.basicConfig(filename='LOGS.log', encoding='utf-8', level=logging.DEBUG)

    logging.debug(f"## Kafka bootstrap servers : {KAFKA_BOOTSTRAP_SERVERS}")
    logging.debug(f'## Kafka group ID: {KAFKA_GROUP_NAME}')
    logging.debug(f'## Kafka topic: {KAFKA_TOPIC}')
    logging.debug(f"## Kafka topic sur lequel sont postées les données aggrégées: {KAFKA_AGGREGATION_TOPIC}")
    logging.debug(f'## Inference python file name: {INFERENCE_PYTHON_FILE}')
    logging.debug(f'## Inference classifier name: {INFERENCE_CLASSIFIER_NAME}')
    logging.debug(f'## Inference classifier model name: {INFERENCE_PYTHON_MODEL}')

    inference = __import__(INFERENCE_PYTHON_FILE)
    logging.debug(f'## After INFERENCE_PYTHON_FILE')

    if INFERENCE_CLASSIFIER_NAME != 'None':
        logging.debug(f'## Il y a une classe en plus')
        locals()[INFERENCE_CLASSIFIER_NAME] = getattr(inference, INFERENCE_CLASSIFIER_NAME)

    model_path = "./" + INFERENCE_PYTHON_MODEL
    model = inference.load_model(model_path)
    logging.debug(f'## After INFERENCE_PYTHON_MODEL')

    main()

