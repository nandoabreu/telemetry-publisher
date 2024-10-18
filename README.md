# telemetry-publisher

Telemetry publisher to Apache Kafka

This app queries telemetry data from Linux-based hosts and publish them to a Kafka broker.

## Requirements

If the app is set in the same host it queries, this host must have all requirements from
both [Hosts running](#hosts-running-this-app) and at least one from the [Target hosts](#target-hosts-for-this-app).

### Query data

This program probes data from several sources and present all found.
At least one of the following is required to return data.

#### OS packages


- lm-sensors (CPU recommended)
- nvidia-smi (NVIDIA GPU recommended)

#### CPU thermal zones

Files in `/sys/class/thermal/thermal_zone*` are queried. Some distro report in this structure.


## Installation

### Source install

The simplest way to install this app is to clone the repository and run the following Makefile command:

```shell
install-source
```

### Compile and distribute

To build and pack binaries to run this app, you must set the environment:

```shell
make env-setup
```

> Note: [Poetry](https://python-poetry.org/) is the dev env requirement for this project.

The following commands should create the binaries and pack them to distribute:

```shell
make build distro-pack
```

> Note: currently the dev env must be loaded with the same Python version than the target device.
> Also, the devices must have one or more [requirements](#os-packages) installed to run the app.
