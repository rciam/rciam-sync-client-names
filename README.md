# rciam-insert-client-names

A script that synchronizes client names from MITREiD DB to simplesamlphp-module-proxystatistics DB.

## Instalation

Copy the repo and config the script

```bash
git clone https://github.com/nikosev/rciam-insert-client-names.git
cd rciam-insert-client-names
cp config-example.py config.py
nano config.py
```

Create a virtualenv and run the script

```bash
virtualenv -p python3 venv
source venv/bin/activate
(venv) pip install psycopg2-binary
(venv) python3 main.py
```

## Configuration

The following configuration options are available:

## Compatibility matrix

This table matches the module version with the supported SimpleSAMLphp version.

| Script |  SimpleSAMLphp-module |
|:------:|:---------------------:|
|        |                       |

## License

Licensed under the Apache 2.0 license, for details see `LICENSE`.
