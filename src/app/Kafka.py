"""This module enables publishing messages to Kafka Brokers"""
from json import dumps
from re import sub

from confluent_kafka import Producer as KafkaProducer
from confluent_kafka.admin import (
    AdminClient,
    ConfigResource,
    NewTopic,
    RESOURCE_TOPIC,
)

from .config import (
    KAFKA_BROKERS,
    KAFKA_PARTITIONS,
    KAFKA_RETENTION_DAYS,
)

if len(KAFKA_BROKERS) < 2:
    KAFKA_PARTITIONS = min(KAFKA_PARTITIONS, 2)

KAFKA_SERVERS_SETTINGS = {'bootstrap.servers': ','.join(KAFKA_BROKERS)}


class Producer:
    def __init__(self):
        # todo: parametrize brokers
        self.__producer = KafkaProducer(KAFKA_SERVERS_SETTINGS)  # todo: parse from params
        self.__adm = AdminClient(KAFKA_SERVERS_SETTINGS)

        self.__topics = dict()
        self.__topics_update()

        self.__counter = 0

    def produce(self, data: (dict, iter), topic: str = 'my_topic', key=None, epoch_ms=None):
        """Publish messages to Kafka"""
        if not self.__counter:
            self.topic_setup(topic)
        self.__producer.poll(timeout=0)

        if isinstance(data, dict):
            data = [data]

        for d in data:
            if not isinstance(d, dict):
                continue

            params = dict(
                timestamp=epoch_ms,
                topic=topic,
                headers=[],
                key=key.encode() if key else None,
                value=dumps(d, separators=(',', ':'), default=str).encode(),
                callback=self.__report,
            )

            self.__producer.produce(**{k: v for k, v in params.items() if v})  # todo: can it publish a list?
            self.__counter += 1

        self.__producer.poll(timeout=9)
        self.__producer.flush(timeout=3)

    def topic_setup(self, topic: str):
        """Create the topic in case not previously created"""
        if topic.startswith('_'):
            raise ValueError('Custom topics must not start with _')

        if topic not in self.__topics:
            requested = int(KAFKA_RETENTION_DAYS * 24 * 60 * 60 * 1000)
            partitions = min(KAFKA_PARTITIONS, 2) if len(KAFKA_BROKERS) == 1 else KAFKA_PARTITIONS
            topic = NewTopic(topic=topic, num_partitions=partitions, config={'retention.ms': str(requested)})
            self.__adm.create_topics([topic])

        else:
            current = self.__topics.get(topic, {}).get('retention.ms')
            requested = int(KAFKA_RETENTION_DAYS * 24 * 60 * 60 * 1000)

            if current != requested:
                resource = ConfigResource(RESOURCE_TOPIC, topic, set_config={'retention.ms': str(requested)})
                self.__adm.alter_configs([resource])

        self.__topics_update()

    @property
    def topics(self) -> dict:
        """Return fetched topics"""
        return self.__topics

    def __topics_update(self):
        for topic in self.__adm.list_topics(timeout=9).topics:
            if topic.startswith('__'):
                continue

            resource = ConfigResource(RESOURCE_TOPIC, topic)
            res = list(self.__adm.describe_configs([resource]).values())[0].result()
            self.__topics[topic] = self.__clean_config_values(res)

    def __report(self, error, message=None):
        pass

    @staticmethod
    def __clean_config_values(d: dict) -> dict:
        fetching = (
            'cleanup.policy',
            'message.timestamp.type',
            'flush.messages',
            'flush.ms',
            'max.message.bytes',
            'retention.ms',
        )

        res = {}
        for k in fetching:
            key = k
            v = sub(r'.*"(\w+)".*', r'\1', str(d.get(k)))

            if v.isnumeric():
                v = int(v)

            if k == 'retention.ms':
                res[k] = v

            if k.endswith('ms'):
                v /= 1000
                if v > 24 * 60 * 60:
                    v /= 24 * 60 * 60
                    key = sub('ms', 'days', k)
                elif v > 60 * 60:
                    v /= 60 * 60
                    key = sub('ms', 'hours', k)
                elif v > 60:
                    v /= 60
                    key = sub('ms', 'minutes', k)
                else:
                    key = sub('ms', 'seconds', k)

                v = int((v * 10) / 10)

            res[key] = v

        return res
