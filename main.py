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

    # Initialise connection to OpenID Provider DB
    if config.mitreid_config:
        oidc_config = config.mitreid_config
        oidc_query = "SELECT client_id, client_name FROM client_details WHERE client_name IS NOT NULL;"
        oidc_flag = "mitreid"

    if config.keycloak_config:
        oidc_config = config.keycloak_config
        oidc_query = "SELECT client_id, name FROM client WHERE realm_id='" + oidc_config["realm"] + "' AND name IS NOT NULL;"
        oidc_flag = "keycloak"

    connect_oidc_str = (
        "dbname='" + oidc_config["dbname"]
        + "' user='" + oidc_config["user"]
        + "' host='" + oidc_config["host"]
        + "' password='" + oidc_config["password"] + "'"
    )

    try:
        connOIDC = psycopg2.connect(connect_oidc_str)
    except Exception as e:
        logging.error("Could not connect to OpenID Provider DB")
        logging.error(e)
        raise SystemExit("Could not connect to OpenID Provider DB")

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
    # Select OpenID Provider clients
    #
    logging.debug("Retrieving client details from OpenID Provider DB")
    try:
        cursorOIDC.execute(oidc_query)
    except Exception as e:
        logging.error("Could not retrieve client details from OpenID Provider DB")
        logging.error(e)
        raise SystemExit("Could not retrieve client details from OpenID Provider DB")

    clientDetails = cursorOIDC.fetchall()

    if oidc_flag == "keycloak":
        for i in range(len(clientDetails)):
            if clientDetails[i][1].startswith("${"):
                client_list = list(clientDetails[i])
                logging.info("Going to edit the client name: " + client_list[1])
                client_list[1] = "Keycloak-" + oidc_config["realm"] + "-" + client_list[0]
                logging.info("New client name: " + client_list[1])
                clientDetails[i] = tuple(client_list)

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
