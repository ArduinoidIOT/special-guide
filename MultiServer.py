import selectors as sels
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from HTTPRequestParser import Request
from HTTPResponseGenerator import Response, NullResponse
from datetime import datetime

http_date_format = "%a, %d %b %Y %H:%M:%S GMT"
err_500_template = """
<!DOCTYPE html>
<html>
<head>
<title> Internal Server Error </title>
<meta charset='utf-8'/> 
</head>
<body>
<h1> 500 Internal Server Error </h1>
<p> The server encountered an error while trying to process your request </p>
</body>
</html>
"""

err_404_template = """
<!DOCTYPE html>
<html>
<head>
<title> Not Found </title>
<meta charset='utf-8'/> 
</head>
<body>
<h1> 404 Not Found </h1>
<p> The server could not find the requested resource </p>
</body>
</html>
"""

err_501_template = """
<!DOCTYPE html>
<html>
<head>
<title> Not Implemented </title>
<meta charset='utf-8'/> 
</head>
<body>
<h1> 501 Not Implemented </h1>
<p> The server has not implemented requested resource </p>
</body>
</html>
"""
err_405_template = """
<!DOCTYPE html>
<html>
<head>
<title> Method Not Allowed </title>
<meta charset='utf-8'/> 
</head>
<body>
<h1> 405 Not Allowed</h1>
<p> This method is not allowed for the requested resource </p>
</body>
</html>
"""


class Server:
    def __init__(self, port=5000, addr='127.0.0.1', custom_header_handlers=[], custom_responses={}):
        self.sel = sels.DefaultSelector()
        self.conndata = {}
        self.sock = socket()
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((addr, port))
        self.sock.listen()
        self.sel.register(self.sock, sels.EVENT_READ, self._accept)
        self._routes = {}
        self._route_methods = {}
        self._err_handlers = {}
        self._custom_header_handlers = custom_header_handlers
        self._cust_resps = custom_responses

    def run(self):
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)

    def _accept(self, sock):
        conn, addr = sock.accept()  # Should be ready
        conn.setblocking(False)
        self.conndata[conn] = Request(cust_handlers=self._custom_header_handlers)
        self.sel.register(conn, sels.EVENT_READ, self._read)

    def _read(self, sock):
        data = sock.recv(1000)  # Should be ready

        if data:
            try:
                self.conndata[sock].update(data)
                if self.conndata[sock].headers_over and ['Expect', '100-continue'] in self.conndata[sock].headers:
                    self.sock.send(NullResponse(100).ready_socket_send())
            except:
                try:
                    resp = self._err_handlers[400]()
                except:
                    resp = self._default_400_bad_request_handler
                self.sock.send(resp.ready_socket_send())
                del self.conndata[sock]
                self.sel.unregister(sock)
                sock.close()
                return
            if self.conndata[sock].data_ready:
                sock.send(self._process_request(self.conndata[sock]))
                del self.conndata[sock]
                self.sel.unregister(sock)
                sock.close()
        else:
            del self.conndata[sock]
            self.sel.unregister(sock)
            sock.close()

    def _process_request(self, req):
        print(req.method, req.path)
        if req.method == 'OPTIONS' and req.path == '*':
            return Response(204, headerlist=[['Allow', ', '.join(
                ['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'DELETE'])]], content_len_autodetect=False).ready_socket_send()
        for i, j in self._routes.items():
            if self._url_match(i, req.path):
                if req.method == 'OPTIONS':
                    return Response(204, headerlist=[['Allow', ', '.join(self._route_methods[i])]],
                                    content_len_autodetect=False).ready_socket_send()
                elif req.method in self._route_methods[i]:
                    try:
                        resp = self._to_response(j(req))
                    except NotImplementedError:
                        try:
                            resp = self._to_response(self._err_handlers[501]())
                        except:
                            resp = self._to_response(self._default_501_noti_handler())
                    except:
                        try:
                            resp = self._to_response(self._err_handlers[500]())
                        except:
                            resp = self._to_response(self._default_500_isa_handler())
                else:
                    try:
                        resp = self._to_response(self._err_handlers[405]())
                    except:
                        resp = self._to_response(self._default_405_mna_handler())

                break
        else:
            try:
                resp = self._err_handlers[404]()
            except:
                resp = self._default_404_not_found_handler()
        if int(resp.http_resp_code) in [200, 201, 202, 203, 206] and req.method == 'HEAD':
            resp.http_resp_code = '204'
            resp.resp_name = 'No Content'
        return resp.ready_socket_send(send_data=not req.method == 'HEAD')

    def register_route(self, route, handler, methods=[]):
        methods += ['GET', 'HEAD', 'OPTIONS']
        methods = list(set(methods))
        self._routes[route] = handler
        self._route_methods[route] = methods

    @staticmethod
    def _url_match(parser_str, parsed_str):
        return parsed_str == parser_str

    def _default_400_bad_request_handler(self):
        return NullResponse(400, cust_resp_codes=self._cust_resps)

    def _default_500_isa_handler(self):
        return Response(500, err_500_template, headerlist=[['Content-Type', 'text/html']],
                        cust_response_codes=self._cust_resps)

    def _default_501_noti_handler(self):
        return Response(501, data=err_501_template, headerlist=[['Content-Type', 'text/html']],
                        cust_response_codes=self._cust_resps)

    def _default_405_mna_handler(self):
        return Response(405, err_405_template, headerlist=[['Content-Type', 'text/html']],
                        cust_response_codes=self._cust_resps)

    def _default_404_not_found_handler(self):
        return Response(404, err_404_template, headerlist=[['Content-Type', 'text/html']],
                        cust_response_codes=self._cust_resps)

    def _to_response(self, resp):
        if type(resp) in (str, bytes):
            resp = Response.from_data(data=resp)
        elif type(resp) in (list, set, frozenset, tuple):
            resp = Response.from_tuple(respcode=resp[0], data=resp[1])
        elif isinstance(resp, Response):
            pass
        else:
            resp = self._err_handlers[500]()
            if type(resp) == str:
                resp = Response.from_data(data=resp)
            elif type(resp) == tuple:
                resp = Response.from_tuple(respcode=resp[0], data=resp[1])
            elif isinstance(resp, Response):
                pass
            else:
                resp = self._default_500_isa_handler()
        resp.add_headers(['Server', 'NoobServer v1.0'])
        resp.add_headers(['Date', datetime.utcnow().strftime(http_date_format)])
        return resp

    def register_err_handler(self, code, handler):
        self._err_handlers[code] = handler

    def route(self, route, **kwargs):
        if 'methods' not in kwargs:
            methods = []
        else:
            methods = kwargs['methods']

        def nothing(handler):
            self.register_route(route, handler, methods=methods)

        return nothing

    def error_handler(self, route, **kwargs):
        def nothing(handler):
            self.register_err_handler(route, handler)

        return nothing


if __name__ == '__main__':
    k = Server(port=3000)


    @k.route('/')
    def noob(req):
        raise NotImplementedError


    @k.error_handler(404)
    def pro(req):
        pass


    k.run()