"""Application main module"""
from datetime import datetime as _dt
from random import randint
from sys import exit, version

from .config import (
    APP_NAME,
    APP_VERSION,
    KAFKA_BROKERS,
    KAFKA_TOPIC,
)
from .Logger import Logger

from .Collector import Collector
from .Kafka import Producer

cid = str(randint(1000, 9999))
obj = Logger(cid=cid)
log = obj.logger


def start():
    """Application runner"""
    log.info('{s}- Start {a} v{v} {s}-'.format(s='-*' * 5, a=APP_NAME, v=APP_VERSION))
    log.info('Running over Python v{}'.format(version.replace('\n', '')))
    # todo: log OS info

    try:
        collector = Collector(logger=log)
        log.debug(f'Device: {collector.device}')

    except OSError as e:
        log.debug(e)
        log.critical('Could not start Collector: ABORT!')
        log.warning('Note: increase the log level to get more details on this error')
        exit(1)

    data = {}

    try:
        data = {
            'device': collector.device,
            'collected_at': _dt.utcnow().strftime("%F %T +00:00"),
        }
        data.update({k: v for k, v in collector.data.items() if k != 'epoch'})

    except OSError as e:
        for err in str(e).split('\n'):
            log.debug(err)

    finally:
        log.debug(f"To stream: {data}")

    producer = Producer(brokers=KAFKA_BROKERS, logger=log)
    producer.stream(messages=[data], topic=KAFKA_TOPIC, key=collector.device)
    log.info("Published data points for cid #{}: [{}]".format(cid, ', '.join(data.keys())))


if __name__ == "__main__":
    start()
