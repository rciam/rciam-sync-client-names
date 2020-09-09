import psycopg2
from psycopg2.extras import execute_values
import sys
import config
import logging
import os

def sync(dry_run):
    pathname = str(os.path.dirname(os.path.realpath(__file__)))
    logging.basicConfig(filename=pathname + '/log/main.log',
                        level=logging.DEBUG,
                        filemode='a', format='%(asctime)s - %(message)s')

    # Initialise connection to MITREid Connect DB
    connect_oidc_str = "dbname='" + config.mitreid_config['dbname'] + \
        "' user='" + config.mitreid_config['user'] + \
        "' host='" + config.mitreid_config['host'] + \
        "' password='" + config.mitreid_config['password'] + "'"
    try:
        connOIDC = psycopg2.connect(connect_oidc_str)
    except Exception as e:
        logging.error("Could not connect to MITREid Connect DB")
        logging.error(e)
        raise SystemExit("Could not connect to MITREid Connect DB")

    # Create psycopg2 cursor that can execute queries
    cursorOIDC = connOIDC.cursor()

    # Initialise connection to proxystatistics DB
    connect_proxystats_str = "dbname='" + \
        config.proxystats_config['dbname'] + \
        "' user='" + config.proxystats_config['user'] + \
        "' host='" + config.proxystats_config['host'] + \
        "' password='" + config.proxystats_config['password'] + "'"
    try:
        connProxystats = psycopg2.connect(connect_proxystats_str)
    except Exception as e:
        logging.error("Could not connect to proxystatistics DB")
        logging.error(e)
        raise SystemExit("Could not connect to proxystatistics DB")

    # Create psycopg2 cursor that can execute queries
    cursorProxystats = connProxystats.cursor()

    #
    # Select MITREid Connect clients
    #
    logging.debug("Retrieving client details from MITREid Connect DB")
    try:
        cursorOIDC.execute("SELECT client_id, client_name "
        "FROM client_details WHERE client_name IS NOT NULL;")
    except Exception as e:
        logging.error("Could not retrieve client details from MITREid "
                      "Connect DB")
        logging.error(e)
        raise SystemExit("Could not retrieve client details from MITREid "
                         "Connect DB")

    clientDetails = cursorOIDC.fetchall()

    #
    # Insert client names into SSPMOD_proxystatistics DB
    #
    query = ("INSERT INTO serviceprovidersmap (identifier, name) VALUES %s "
    "ON CONFLICT (identifier) DO UPDATE SET name = EXCLUDED.name "
    "WHERE serviceprovidersmap.name IS DISTINCT FROM EXCLUDED.name;")

    logging.debug("Updating proxystatistics DB")
    try:
        # https://www.psycopg.org/docs/extras.html#psycopg2.extras.execute_values
        execute_values(cursorProxystats, query, clientDetails)
    except Exception as e:
        logging.error("Could not update proxystatistics DB query")
        logging.error(e)
        raise SystemExit("Could not update proxystatistics DB query")

    if not dry_run:
        logging.info("Commit proxystatistics DB update")
        connProxystats.commit()

    cursorOIDC.close()
    cursorProxystats.close()

    connOIDC.close()
    connProxystats.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "-n":
        dry_run_flag = True
    else:
        dry_run_flag = False
    sync(dry_run_flag)
