"""This module enables publishing messages to Kafka Brokers"""
from json import dumps
from logging import log

from confluent_kafka import Producer as ConfluentKafkaProducer


class Producer:
    def __init__(self, brokers: iter, logger: log = None):
        """Instantiate Kafka producer.

        Args:
            brokers (iter): iterable with at least one "broker:port" str,
                as in: "localhost:9092"
            logger (logging.log): Python's logging logger method
        """
        self._counter = 0

        settings = {'bootstrap.servers': ','.join(brokers)}
        self.__kafka = ConfluentKafkaProducer(settings)

        self._logger = logger
        self.log_debug(f'Connected to: {settings["bootstrap.servers"]!r}')

    def stream(self, messages: iter, topic: str, key: str = None):
        """Stream (produce, publish) messages

        Args:
            messages (iter with dicts): Dict messages to be streamed, as in: [{'key': 'value'}]
            topic (str): Topic to send the messages to
            key (str, optional): Tag the message envelope at topic level
        """
        for message in messages:
            params = {
                'timestamp': int(message.pop('epoch') * 10 ** 3),
                'topic': topic,
                'key': key.encode() if key else None,
                'value': dumps(message, separators=(',', ':'), default=str).encode(),
                'callback': self.__report,
            }

            self.__kafka.produce(**{k: v for k, v in params.items() if v})
            self._counter += 1

        self.__kafka.poll(timeout=9)
        self.__kafka.flush(timeout=3)
        self.log_debug(f'Streamed: {self._counter} messages')

    def __report(self, error: str = None, msg: object = None):
        if error is not None:
            self.log_debug(f'Message not delivered: {error}')
        elif msg:
            self.log_debug(f"Delivered to {msg.topic()!r} at part. #{msg.partition()}, offset {msg.offset()}")

    def log_debug(self, msg: str):
        """Log a debug message

        Args:
            msg (str): Message to be logged
        """
        if not self._logger:
            return

        self._logger.log(10, f'[Kafka] {msg}')
