# rciam-sync-client-names

A Python-based tool for synchronising client names from Keycloak or MITREid Connect DB to simplesamlphp-module-proxystatistics DB.

## Instalation

Install from git and configure

```bash
git clone https://github.com/rciam/rciam-sync-client-names.git
cd rciam-sync-client-names
cp config-example.py config.py
vi config.py
```

Create a Python virtualenv, install dependencies, and run the script

```bash
virtualenv -p python3 .venv
source .venv/bin/activate
(venv) pip3 install -r requirements.txt
(venv) python3 main.py
🍺
```

## License

Licensed under the Apache 2.0 license, for details see `LICENSE`.
