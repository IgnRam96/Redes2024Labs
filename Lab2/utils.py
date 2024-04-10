import connection
import constants
import logging
import sys
import threading

from errors import ClientDisconnectedError

logger = logging.getLogger("htfp_server")

def make_response(message, status_code=constants.CODE_OK):
    """
    Crea una respuesta con su codigo de status.
    """
    if not message:
        return f"{status_code} {constants.error_messages[status_code]}{constants.EOL}"
        
    response = (
        f"{status_code} {constants.error_messages[status_code]}{constants.EOL}"
    )
    return f"{response}{message}{constants.EOL}"

def _create_thread(socket_conn, addr, directory):

    def _thread_func(_socket_conn, _addr, _directory):

        conn = connection.Connection(_socket_conn, _directory)

        try:
            conn.handle()
        except ClientDisconnectedError:
            logger.info("client disconnected proceeding to close connection")
            
        socket_conn.close()
        logger.info("connection to %s closed", _addr)
    
    return threading.Thread(
        target=_thread_func, args=(socket_conn, addr, directory), daemon=True
    )

def _init_logger():
    """
    Inicializa el logger de la app
    """
    logger = logging.getLogger('hftp_server')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
