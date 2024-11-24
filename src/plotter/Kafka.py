"""Kafka module to consume messages for Telemetry"""
from copy import deepcopy
from datetime import datetime as _dt, timedelta
from json import loads

from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.cimpl import Message


class KafkaConsumer:
    def __init__(self, server: str, kafka_topics: list, consumer_id: str = None):
        """Kafka consumer abstract class

        Args:
            server (str): Broker's host and port, as in '127.0.0.1:9092'
            kafka_topics (list): Topics in Broker to consume from
            consumer_id (str, optional): ID to avoid skipping messages consumed by others
        """
        config = {
            'bootstrap.servers': server,
            'group.id': consumer_id or 'consumer',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': 'false',
        }

        self.consumer = Consumer(config)
        self.topics = kafka_topics
        self.consumer.subscribe(self.topics)
        self.available_hosts = set()

    def _assign(self, include_debug: bool = False):
        partitions = []
        params = {'offset': 0}
        params = {}

        for topic in (t for t in self.topics if include_debug | (t != 'log-debug')):
            metadata = self.consumer.list_topics(topic, timeout=5)
            for partition in metadata.topics[topic].partitions:
                params.update({'topic': topic, 'partition': partition})
                tp = TopicPartition(**params)
                partitions.append(tp)

        self.consumer.assign(partitions)

    def _handler(self, msg: Message, threshold_hours: int = None, filter_keys: list = None):
        raise NotImplementedError('Method may be optionally implemented in a child, and can only called from it')


class KafkaTelemetryConsumer(KafkaConsumer):
    def __init__(self, server: str, topic: str = 'telemetry', consumer_id: str = 'telemetry'):
        super().__init__(server, [topic], consumer_id)

    def fetch(self, threshold_days: int, filter_host: str) -> iter:
        """Fetch messages"""
        since = (_dt.utcnow() - timedelta(days=threshold_days)).timestamp()
        self._assign()

        previous = {}
        tpl = {
            'cpu': 0.0,
            'ram': 0.0,
            'net': {},
        }

        while True:
            msg = self.consumer.poll(timeout=5)  # Takes around 3.03s to fetch

            if msg is None:
                break

            if not msg.key():
                continue

            epoch = msg.timestamp()[1] / 10 ** 3

            if since and (epoch < since):
                continue

            host = msg.key().decode()

            if host != filter_host:
                if isinstance(self.available_hosts, set):
                    self.available_hosts.add(host)
                continue

            if isinstance(self.available_hosts, set):
                self.available_hosts = None

            decoded = msg.value().decode(errors='replace')
            loaded = loads(decoded)
            res = deepcopy(tpl)  # Prevent yielding same dicts

            cpu = loaded.get('cpu', {}).get('usage')
            if isinstance(cpu, (float, int)):
                res['cpu'] = cpu  # non-accumulative values are not calculated

            ram = loaded.get('ram', {}).get('usage')
            if isinstance(ram, (float, int)):
                res['ram'] = ram  # non-accumulative values are not calculated

            net = loaded.get('net', {})
            if net and previous.get('net'):
                delta = (epoch - previous['epoch']) / 60  # per minute

                for dev, data in net.items():
                    prev_data = previous.get('net', {}).get(dev)

                    resume = False
                    if all([isinstance(v, (float, int)) for v in (data.get('in'), prev_data.get('in'))]):
                        if 'net' not in res:
                            res['net'] = {}
                        if dev not in res['net']:
                            res['net'][dev] = {}
                        resume = True

                    if resume and all([isinstance(v, (float, int)) for v in (data.get('out'), prev_data.get('out'))]):
                        res['net'][dev] = {
                            'in': (data['in'] - prev_data['in']) / delta,
                            'out': (data['out'] - prev_data['out']) / delta,
                        }

            if res:
                yield {'id': float(f'{msg.offset()}.{msg.partition()}'), 'epoch': epoch} | res

            previous.update({'epoch': epoch, 'net': net})
