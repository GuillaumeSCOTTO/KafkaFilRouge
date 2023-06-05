from confluent_kafka import Consumer, KafkaError
import os
import json
import logging
# import importlib


def msg_process(msg):
    val = json.loads(msg.value().decode('utf-8'))
    val[inf_module_name.split('_')[0]] = inference.predict(model, val['tweet'])
    with open("result.txt", "a") as f:
        f.write(str(val) + "\n")
        logging.debug(f'##Msg reçu: {val}')


def send_msg(timestamp, value, producer, args):
    dico = {'timestamp': timestamp, 'pseudo': value[0], 'tweet': value[1]}
    result = json.dumps(dico)
    producer.produce(args.topic, key=args.filename, value=result, callback=acked)


def main():
    c = Consumer({
        'bootstrap.servers': kafka_bootstrap_servers,
        'group.id': kafka_group_name
    })

    logging.debug('Connexion done')

    c.subscribe([kafka_topic])

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
                msg_process(msg)
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

    # inference = importlib.import_module(inf_module_name)
    # model_path = "./" + inf_module_model_name
    # model = inference.load_model(model_path)

    inference = __import__(inf_module_name)

    if inf_classifier_name != 'None':
        logging.debug(f'## Il y a une classe en plus')
        locals()[inf_classifier_name] = getattr(inference, inf_classifier_name)

    model_path = "./" + inf_module_model_name
    model = inference.load_model(model_path)

    main()

