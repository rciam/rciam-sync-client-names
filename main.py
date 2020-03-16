import psycopg2  # pip install psycopg2-binary
import sys
import config
import logging


def sync(dry_run):
    logging.basicConfig(filename='log/insertClientNames.log', level=logging.DEBUG,
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
        cursorOIDC.execute("""SELECT client_name, client_id FROM client_details WHERE client_name IS NOT NULL;""")
    except Exception as e:
        logging.error("Uh oh, can't SEexecute query.")
        logging.error(e)
        sys.stderr.write("Can't execute 'Select MITREiD clients' query!")

    clientDetails = [{'client_name': row[0], 'client_id': row[1]}
                     for row in cursorOIDC.fetchall()]

    #
    # Insert client names into SSPMOD_proxystatistics DB
    #
    params = []
    for client in clientDetails:
        # TODO: special character escape
        params.append("('" + client['client_id'] + "', '" +
                      client['client_name'].replace("'", "''") + "')")

    query = 'INSERT INTO serviceprovidersmap (identifier, name) VALUES %s ' + \
        'ON CONFLICT (identifier) DO UPDATE SET name = EXCLUDED.name ' + \
        'WHERE serviceprovidersmap.name IS DISTINCT FROM EXCLUDED.name;' % ', '.join(params)

    try:
        logging.debug(
            "Executing 'Insert client names into SSPMOD_proxystatistics DB' query!")
        cursorProxystats.execute(query, clientDetails)
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
