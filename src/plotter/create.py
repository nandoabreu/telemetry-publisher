#!/usr/bin/env python3
"""Create plots from telemetry data"""
from os import environ
from pandas import DataFrame, to_datetime
from pathlib import Path
from sys import exit

try:
    from tomllib import load  # noqa
    from tomllib import TOMLDecodeError  # noqa
except ModuleNotFoundError:
    from tomli import load  # noqa
    from tomli import TOMLDecodeError  # noqa

from Kafka import KafkaTelemetryConsumer
from Plot import plot_usage_data, plot_net_data

REQUIRED = {
    'KAFKA_BROKER': '<IP-or-host>:<port>',
    'BROKER_TOPIC': '<topic-name>',
    'TARGET_HOST': '<short-hostname>',
    'TARGET_NETWORK_DEVICE_NAME': '<device-name (eth0|eth1|wlp0s20f3|etc)>',
}


if __name__ == '__main__':
    # Fetch config from env.toml
    if Path('env.toml').is_file():
        with open('env.toml', 'br') as f:
            toml = load(f)

    env = toml['prod']

    # Update config with required vars in env vars
    for key in REQUIRED:
        val = environ.get(key)
        if val:
            env[key] = val

    # Connect broker, fetch data, set data frame
    consumer = KafkaTelemetryConsumer(env['KAFKA_BROKER'])
    data_generator = consumer.fetch(threshold_days=7, filter_host=env['TARGET_HOST'])
    df = DataFrame(data_generator)

    if df.empty:
        print(f"No message fetched. Hosts available in topic {env['BROKER_TOPIC']}: {consumer.available_hosts}")
        exit(1)

    # Transform data
    df.drop_duplicates(subset=['epoch'], inplace=True)
    df['epoch'] = to_datetime(df['epoch'], unit='s')
    df.rename(columns={'epoch': 'moment'}, inplace=True)
    df.sort_values(by='moment', inplace=True)

    # Add general hour aggregator
    df['hour'] = df['moment'].dt.floor('h')
    df.reset_index(drop=True, inplace=True)

    # Set destination dir
    dst_dir = Path(env['DATA_STORAGE_DIR'])
    dst_dir.mkdir(exist_ok=True)

    dst = dst_dir / f"usage.{env['TARGET_HOST']}.png"
    plot_usage_data(df, dst)

    dst = dst_dir / f"networking.{env['TARGET_HOST']}.png"
    plot_net_data(df, env['TARGET_NETWORK_DEVICE_NAME'], dst)
