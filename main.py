import psycopg2  # pip install psycopg2-binary
from psycopg2.extras import execute_values
import sys
import config
import logging
import os

def sync(dry_run):
    pathname = str(os.path.dirname(os.path.realpath(__file__)))
    logging.basicConfig(filename=pathname + '/log/insertClientNames.log', level=logging.DEBUG,
                        filemode='a', format='%(asctime)s - %(message)s')

    #
    # Initialize connection to MITREiD Connect Database
    #
    connect_oidc_str = "dbname='" + config.mitreid_config['dbname'] + \
        "' user='" + config.mitreid_config['user'] + \
        "' host='" + config.mitreid_config['host'] + \
        "' password='" + config.mitreid_config['password'] + "'"
    try:
        # use our connection values to establish a connection
        connOIDC = psycopg2.connect(connect_oidc_str)
    except Exception as e:
        logging.error(
            "Uh oh, can't connect. Invalid dbname, user or password?")
        logging.error(e)
        sys.stderr.write("Can't connect to MITREiD Database!")

    # create a psycopg2 cursor that can execute queries
    cursorOIDC = connOIDC.cursor()

    #
    # Initialize connection to SSPMOD_proxystatistics Database
    #
    connect_proxystats_str = "dbname='" + config.proxystats_config['dbname'] + \
        "' user='" + config.proxystats_config['user'] + \
        "' host='" + config.proxystats_config['host'] + \
        "' password='" + config.proxystats_config['password'] + "'"
    try:
        # use our connection values to establish a connection
        connProxystats = psycopg2.connect(connect_proxystats_str)
    except Exception as e:
        logging.error(
            "Uh oh, can't connect. Invalid dbname, user or password?")
        logging.error(e)
        sys.stderr.write("Can't connect to COManage Database!")

    # create a psycopg2 cursor that can execute queries
    cursorProxystats = connProxystats.cursor()

    #
    # Select MITREiD clients
    #
    try:
        logging.debug("Executing 'Select MITREiD clients' query!")
        cursorOIDC.execute("""SELECT client_id, client_name FROM client_details WHERE client_name IS NOT NULL;""")
    except Exception as e:
        logging.error("Uh oh, can't SEexecute query.")
        logging.error(e)
        sys.stderr.write("Can't execute 'Select MITREiD clients' query!")

    clientDetails = cursorOIDC.fetchall()

    #
    # Insert client names into SSPMOD_proxystatistics DB
    #
    query = 'INSERT INTO serviceprovidersmap (identifier, name) VALUES %s ' + \
        'ON CONFLICT (identifier) DO UPDATE SET name = EXCLUDED.name ' + \
        'WHERE serviceprovidersmap.name IS DISTINCT FROM EXCLUDED.name;'

    try:
        logging.debug(
            "Executing 'Insert client names into SSPMOD_proxystatistics DB' query!")
        # https://www.psycopg.org/docs/extras.html#psycopg2.extras.execute_values
        execute_values(cursorProxystats, query, clientDetails)
    except Exception as e:
        logging.error("Uh oh, can't execute query.")
        logging.error(e)
        sys.stderr.write(
            "Can't execute 'Insert client names into SSPMOD_proxystatistics DB' query!")

    if not dry_run:
        logging.info("commit")
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
