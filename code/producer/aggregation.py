from confluent_kafka import Consumer, KafkaError
import json

TOPIC_FOR_SEND = "inner_topic"
KAFKA_SERVER = 'localhost:9092'
KEYS = ['timestamp', 'pseudo', 'tweet']
NB_CONSUMERS = 2
KAFKA_GROUP_NAME = 'group3'
CHEMIN = 'results/'


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
                    with open(CHEMIN + "result.txt", "a") as f:
                        f.write(str(final_json) + "\n")
                    print(f'##Msg reçu: {final_json}')
        else:
            for key in val.keys():
                if key not in KEYS:
                    dico[val['timestamp']][key] = val[key]


def main():
    c = Consumer({'bootstrap.servers': KAFKA_SERVER,
        'group.id': KAFKA_GROUP_NAME})
    print(f'Serveur Kafka : {KAFKA_SERVER}')

    c.subscribe([TOPIC_FOR_SEND])
    print(f'Topic Kafka : {TOPIC_FOR_SEND}')

    dico = {}

    try:
        while True:
            msg = c.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f'End of partition reached: {msg.topic()}[{msg.partition()}]')
                else:
                    print(f'Error while consuming message: {msg.error()}')
            else:
                msg_process(msg, dico)

    except KeyboardInterrupt:
        pass
    finally:
        c.close()


if __name__ == "__main__":
    main()