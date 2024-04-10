# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import os
from time import sleep
from constants import *
import base64
import traceback
import logging
import string

from errors import ClientDisconnectedError, InvalidCommand, NewlineOutsideEOL
from utils import make_response

logger = logging.getLogger("hftp_server")

class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory):
        self.socket = socket
        self.directory = directory
        self.buffer = ""

    def _newline_outside_eol(self, string):

        for i, char in enumerate(string):
            if char == "\n":
                if i - 1 < 0 or string[i - 1] != "\r":
                    return True
        
        return False
    
    def _send_response(self, response):
        """
        Envia la respuesta al cliente
        """
        try:
            bytes_response = response.encode("ascii")
        except UnicodeEncodeError:
            logger.error("Could not encode response")
            bytes_response = make_response("", INTERNAL_ERROR).encode("ascii")
        
        logger.debug("sending response %s", repr(bytes_response.decode("ascii")))
    

        self.socket.send(bytes_response)

    def parse_command(self, string): 
        """
        Parsea el comando devolviendo una tupla de (comando, opciones).
        """

        if self._newline_outside_eol(string):
            raise NewlineOutsideEOL

        command = string.strip(EOL).split()

        if not command:
            raise InvalidCommand("invalid command %s" % (repr(string),))

        return command[0], command[1:]
    
    def _get_EOL_index(self):

        index = self.buffer.find(EOL)

        if index == -1:
            return None
        
        return index
    
    def execute_command(self, cmd, options):
        """
        Ejecuta el comando con las opciones y devuelve la respuesta en forma de
        string de bytes.
        """

        func = getattr(self, cmd)
        response = func(*options)
        return response

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        keep_alive = True
        while keep_alive:
            bytes_received = self.socket.recv(1024)

            if not bytes_received:
                raise ClientDisconnectedError

            try:
                logger.debug("received: %s", repr(bytes_received.decode("ascii")))
                self.buffer += bytes_received.decode("ascii")
                logger.debug("current buffer %s", repr(self.buffer))
            except UnicodeDecodeError:
                response = make_response("", BAD_REQUEST)
                self._send_response(response)
            
            index = self._get_EOL_index()
            if index is not None:
                command = self.buffer[:index]
                self.buffer = self.buffer[index + len(EOL):]

                try:
                    cmd, options = self.parse_command(command)
                    response = self.execute_command(cmd, options)

                    if cmd == "quit" or response[0] == "1":
                        keep_alive = False

                except NewlineOutsideEOL:
                    response = make_response("", BAD_EOL)
                except InvalidCommand:
                    logger.debug(traceback.format_exc())
                    response = make_response("", BAD_REQUEST)
                except AttributeError:
                    response = make_response("", INVALID_COMMAND)
                except TypeError:
                    logger.error(traceback.format_exc())
                    response = make_response("", INVALID_ARGUMENTS)
                except Exception:
                    logger.error(traceback.format_exc())
                    response = make_response("", INTERNAL_ERROR)
               
                        
                
                self._send_response(response)

    def quit(self):
        respuesta = ""
        return make_response(respuesta)

    def get_file_listing(self):
        respuesta = ""
        for elem in os.listdir(self.directory):
            respuesta += elem + EOL
        return make_response(respuesta)
                      
    def get_metadata(self, filename):
        respuesta = ""
        
        file = os.path.join(self.directory, filename)
        
        if not os.path.isfile(file):
            return make_response(respuesta, FILE_NOT_FOUND)
        
        respuesta += str(os.path.getsize(file))

        return make_response(respuesta)
    
    def get_slice(self, filename, offset, size):
        respuesta = ""
        
        if not offset.isnumeric() or not size.isnumeric():
            return make_response(respuesta, INVALID_ARGUMENTS)
        
        file = os.path.join(self.directory, filename)
        slice_offset = int(offset)
        slice_size = int(size)
        
        if not os.path.isfile(file):
            return make_response(respuesta, FILE_NOT_FOUND)
        if slice_offset < 0 or slice_offset > os.path.getsize(file):
            return make_response(respuesta, BAD_OFFSET)
        if slice_size < 0:
            return make_response(respuesta, INVALID_ARGUMENTS)
        
        with open(file, "rb") as buffer:
            buffer.seek(slice_offset)
            bytes = buffer.read(slice_size)
            encoded_bytes = base64.b64encode(bytes)
            respuesta += encoded_bytes.decode("ascii")
        
        return make_response(respuesta)