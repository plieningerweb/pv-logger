# Pytho PV Logger

Logging of photovoltaic inverters
* to local cache (sqlite)
* to InfluxDB (can be remote over ssh)

## Kaco over RS485

```
pip install pv_logger
```

create a config file `config.yaml`:
```
archive_older_than_days: 30
# path to sqlite database
engine: "sqlite:///:memory:"
influx:
  dbname: pv-nodes
  host: localhost
  password: no-need
  port: 8086
  user: no-need
tags:
  host: testhost.de
  region: europe
port: "/dev/ttyUSB*"
inverter_ids: [1,2,3]
read_interval_seconds: 10
```

run logger in folder where `config.yaml` is located
```
kaco_logger
```

## SMA Sunny Boy over RS485

TODO

## SMA Sunny Mini Central over Bluetooth

TODO
