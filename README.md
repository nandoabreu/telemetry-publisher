# telemetry-publisher

Telemetry publisher to Apache Kafka

This app can query telemetry against local or remore hosts.
It is designed to run locally, sending local data to a remote broker,
but remote hosts can be set, in case the app can not run from some devices.


## Requirements

If the app is set in the same host it queries, this host must have all requirements from
both [Hosts running](#hosts-running-this-app) and [Target hosts](#target-hosts-for-this-app).

### Hosts running this app

#### OS packages

- nmap
- ping
- ssh


### Target hosts for this app

#### OS packages

- ~vcgencmd~ (to be discontinued)
- lm-sensors (in case the kernel doesn't handle ACPI by itself)
