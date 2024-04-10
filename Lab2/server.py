#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import threading
import socket
import connection
import sys
import logging
from constants import *
from errors import ClientDisconnectedError
from utils import _create_thread, _init_logger

logger = logging.getLogger("hftp_server")

class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print("Serving %s on %s:%s." % (directory, addr, port))

        self.socket_obj = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM
        )
        
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_obj.bind((addr, port))
        self.directory = directory

    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        self.socket_obj.listen(1)
        connections = []
        
        try:
            while True:
                socket_conn, addr = self.socket_obj.accept()
                logger.info("connected to %s", addr)

                client_connection = _create_thread(socket_conn, addr, self.directory)
                client_connection.start()
                connections.append((client_connection, socket_conn))
        except KeyboardInterrupt:
            logger.info("apagando servidor...")
            self.socket_obj.close()
            for _, sock in connections:
                sock.close()

def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help="Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help="Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)

    server = Server(options.address, port, options.datadir)
    server.serve()


if __name__ == '__main__':
    _init_logger()
    main()
