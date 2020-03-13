redirect_template = """
<!DOCTYPE html>
<html>
<head>
<title>Redirect</h1>
<meta charset='utf-8'/>
</head>
<body>
<p>Click to redirect to <a> {} </p>
</body>
</html>
"""
http_codes = {
    100: 'Continue',
    101: 'Switching Protocols',
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authorititative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    422: "Unprocessable Entity",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required"

}


class Response:
    def __init__(self, httpcode=200, data='', headerlist=[], cust_response_codes=None, data_encoding='utf-8',
                 content_len_autodetect=True):
        if cust_response_codes is None:
            cust_response_codes = {}
        self.autodetect = content_len_autodetect
        self.http_resp_code = str(httpcode)
        self.encoding = data_encoding
        if hasattr(data, 'encode'):
            self.data = data.encode(encoding=data_encoding)
        else:
            self.data = data
        self.headers = headerlist
        if content_len_autodetect:
            self.headers.append(['Content-Length', str(len(data))])
        self.resp_name = {**http_codes, **cust_response_codes}[httpcode]

    def add_headers(self, header):
        self.headers.append(header)

    def ready_socket_send(self, send_data=True):
        data = "HTTP/1.0 " + self.http_resp_code + " " + self.resp_name + '\r\n'
        for i, j in self.headers:
            data += i + ": " + j + '\r\n'

        data += '\r\n'
        data = data.encode(self.encoding)
        if send_data:
            data += self.data
        return data

    def set_data(self, data):
        if hasattr(data, 'encode'):
            self.data = data.encode(encoding=self.encoding)
        else:
            self.data = data
        if self.autodetect:
            self.headers.append(['Content-Length', str(len(data))])

    @classmethod
    def from_data(cls, data):
        return cls(data=data, headerlist=[('Content-Type', 'text/html')])

    @classmethod
    def from_tuple(cls, respcode, data):
        return cls(respcode, data, [('Content-Type', 'text/html')])


def redirect(location, code=302):
    return Response(code, redirect_template.format(location), [('Location', location), ('Content-Type', 'text/html')])


class NullResponse(Response):
    def __init__(self, resp, cust_resp_codes=None):
        super().__init__(httpcode=resp, content_len_autodetect=False, cust_response_codes=cust_resp_codes)
