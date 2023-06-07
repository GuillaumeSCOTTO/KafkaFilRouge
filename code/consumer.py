from confluent_kafka import Consumer, KafkaError, Producer
import os
import json
import logging

TOPIC_FOR_SEND = "inner_topic"


def msg_process(msg):
    val = json.loads(msg.value().decode('utf-8'))
    result = int(inference.predict(model, val['tweet']))
    val[inf_module_name.split('_')[0]] = result
    with open("result.txt", "a") as f:
        f.write(str(val) + "\n")
        logging.debug(f'##Msg reçu: {val}')
    return val


def acked(err, msg):
    if err is not None:
        logging.debug(f'##Failed to deliver message: {err}')
    else:
        logging.debug(f'##Message envoyé: {str(msg.topic()), str(msg.partition()), str(msg.value())}')


def res_send(value, producer):
    result = json.dumps(value)
    producer.produce(TOPIC_FOR_SEND, value=result, callback=acked)


def main():
    # On créé l'instance producer pour envoyer les résultats qui seront calculés
    p = Producer({'bootstrap.servers': kafka_bootstrap_servers})
    logging.debug('Producer done')

    c = Consumer({
        'bootstrap.servers': kafka_bootstrap_servers,
        'group.id': kafka_group_name
    })
    logging.debug('Consumer done')

    c.subscribe([kafka_topic])
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
    logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
    inf_module_name = os.getenv('INFERENCE_PYTHON_FILE')
    inf_module_model_name = os.getenv('INFERENCE_PYTHON_MODEL')
    inf_classifier_name = os.getenv('INFERENCE_CLASSIFIER_NAME')

    kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
    kafka_topic = os.getenv('KAFKA_TOPIC')
    kafka_group_name = os.getenv('KAFKA_GROUP_NAME')

    logging.debug(f'##Kafka group ID: {kafka_group_name}')
    logging.debug(f'##Kafka topic: {kafka_topic}')
    logging.debug(f'##Inference classifier name: {inf_classifier_name}')

    inference = __import__(inf_module_name)

    if inf_classifier_name != 'None':
        logging.debug(f'## Il y a une classe en plus')
        locals()[inf_classifier_name] = getattr(inference, inf_classifier_name)

    model_path = "./" + inf_module_model_name
    model = inference.load_model(model_path)

    main()

