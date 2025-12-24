#!/usr/bin/env python3

import os
import json
import ctypes
import socket
import threading
from queue import Queue

def _set_thread_name(name):
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(15, name.encode())

class KlippyRPCShim:
    def __init__(self, socket_path=None):
        """
        Init socket client
        By default kiauh style socket path is used
        :param socket_path:
        """
        home_path = f"/home/{os.environ['USER']}"
        if socket_path is None:
             socket_path = f"{home_path}/printer_data/comms/klippy.sock"
        self._socket_path = socket_path
        self._sock = self._new_connection()
        self._is_running = True
        self.__rth = threading.Thread(target=self._reader, name="reader", daemon=True)
        # Variable below are protected with lock
        self._lock = threading.Lock()
        self._inflight = {}
        self._actions = {}
        self._id = 1
        # Run reader
        self.__rth.start()
    def shutdown(self):
        """ Stops all communications """
        self._is_running = False
        self._sock.shutdown(socket.SHUT_RDWR)
        self.__rth.join()
        self._inflight = {}
        self._actions = {}
    def _new_connection(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self._socket_path)
        return sock
    def _stream_decoder(self, stream):
        buf = ""
        while True:
            resp = stream.recv(4096).decode()
            if len(resp) == 0:
                break
            buf += resp
            if "\x03" not in buf:
                continue
            msg, buf = buf.split("\x03", 1)
            response = json.loads(msg)
            yield response
        try:
            stream.close()
        except OSError:
            pass
    def _reader(self):
        _set_thread_name("reader")
        for response in self._stream_decoder(self._sock):
            id_value = response.get("id", None)
            if not self._is_running:
                return
            with self._lock:
                if id_value in self._inflight:
                    self._inflight[id_value].put(response)
            action = response.get("remote_method", None)
            params = response.get("params", None)
            if action in self._actions:
                self._actions[action](params)
    def _verify_id(self, request):
        if request.get("id") is None:
            with self._lock:
                request["id"] = "KRPC_" + hex(self._id)
                self._id += 1
        return request
    def _socket_write(self, msg, sock=None):
        if sock is None:
            sock = self._sock
        str_line = msg + "\x03"
        raw_line = str_line.encode()
        sock.sendall(raw_line)
    def query_async(self, request):
        """
        Accepts dict object
        Returns callback which block upon call
        :param request:
        :return:
        """
        request = self._verify_id(request)
        req_json = json.dumps(request)
        id_value = request["id"]
        with self._lock:
            self._inflight[id_value] = Queue(1)
        self._socket_write(req_json)
        def promise():
            response = self._inflight[id_value].get()
            with self._lock:
                del self._inflight[id_value]
            return response
        return promise
    def query(self, request):
        """
        Accepts dict object
        Blocks until response is received
        :param request:
        :return:
        """
        prom = self.query_async(request)
        return prom()
    def subscribe(self, request):
        """
        Accepts dict object
        Returns generator function and shutdown function to call/use
        :param request:
        :return:
        """
        request = self._verify_id(request)
        conn = self._new_connection()
        req_json = json.dumps(request)
        self._socket_write(req_json, conn)
        def gen():
            for response in self._stream_decoder(conn):
                yield response
        def close_conn():
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            # conn.close()
        return gen, close_conn
    # Allow register remote methods
    # Callback will be evaluated from the other Thread
    def register_remote_method(self, callback, remote_method, response_template=None):
        """
        Accepts callback to call upon receive of message
        Name of remote method to use will be defined
        remote_method name reused as the key to receive data
        reponse template can have any keys except `remote_method`
        returns nothing
        :param callback:
        :param remote_method:
        :param response_template:
        :return:
        """
        if response_template is None:
            response_template = {}
        response_template["remote_method"] = remote_method
        request = {
            "method": "register_remote_method",
            "params": {
                "response_template": response_template,
                "remote_method": remote_method
            }
        }
        request = self._verify_id(request)
        with self._lock:
            self._actions[remote_method] = callback
        req_json = json.dumps(request)
        self._socket_write(req_json)
