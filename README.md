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
