from datetime import datetime

http_date_format = "%a, %d %b %Y %H:%M:%S GMT"


def _list_slice_into_two_exclude(list, index):
    return list[:index], list[index + 1:]


def _list_slice_into_two_include_in_left(list, index):
    return list[:index + 1], list[index + 1:]


def _list_slice_into_two_include_in_right(list, index):
    return list[:index], list[index:]


class Request:
    def __init__(self, overflow=b'', cust_handlers=None,addr=()):
        if cust_handlers is None:
            cust_handlers = []
        self.cust_handlers = cust_handlers
        self.cookies = {}
        self.args = []
        self._content_len = 0
        self.data = b""
        self.headers = []
        self._partial = b""
        self.overflow = b''
        self.method = ''
        self.path = ''
        self._crlf0_done = False
        self.data_ready = False
        self.headers_over = False
        self.update(overflow)
        self.addr = addr

    def update(self, data):
        if self.data_ready:
            self.overflow += data
            return
        partial = self._partial + data
        crlf_split = partial.split(b'\r\n')
        self._partial = crlf_split.pop()
        if not self._crlf0_done:
            try:
                k = (crlf_split.pop(0).decode()).split(' ')
                k2 = []
                for i in k:
                    if i:
                        k2.append(i.strip())
                self.method = k2[0]
                k = self._process_url(k2[1])
                if len(k) > 1:
                    self.path, self.args = k
                else:
                    self.path = k[0]
            except IndexError:
                pass
        if not self.headers_over:
            for i in crlf_split:
                if i:
                    header = self._handle_header(i.decode(), custom_handlers=self.cust_handlers)
                    if header[0] == 'Cookie':
                        self.cookies = {**self.cookies, **header[1]}
                    elif header[0] == 'Content-Length':
                        self._content_len = header[1]
                    self.headers.append(header)
                else:
                    self.headers_over = True
                    data = data.split(b'\r\n\r\n')[1]
                    break
        if self.headers_over:
            self.data += data
            self.data, self.overflow = _list_slice_into_two_include_in_right(self.data, self._content_len)
            self.data_ready = (len(self.data) == self._content_len)

    @staticmethod
    def _handle_header(data, custom_handlers=()):
        headers = list(_list_slice_into_two_exclude(data, data.index(':')))
        if headers[0] in ('Accept', 'Accept-Charset', 'Accept-Encoding', 'Accept-Language'):
            headers[1] = headers[1].split(',')
            k = []
            for i in range(len(headers[1])):
                l = [n.strip() for n in headers[1][i].split(';')]
                if len(l) == 2:
                    l[1] = float(l[1].split('=')[1])
                k.append(l)
            headers[1] = k
        elif headers[0] in ('Content-Length', 'DNT', 'Early-Data', 'Upgrade-Insecure-Requests'):
            headers[1] = int(headers[1])
        elif headers[0] in ('Device-Memory', 'DPR'):
            headers[1] = float(headers[1])
        elif headers[0] in ('Cache-Control', 'Allow', 'Content-Dispostion', 'Content-Encoding', 'Content-Language',
                            'Content-Type', 'Forwarded', 'If-Match', 'If-None-Match', 'Keep-Alive', 'TE',
                            'Via', 'Want-Digest', 'X-Forwarded-For'
                            ):
            headers[1] = headers[1].split(',')
            k = []
            for i in range(len(headers[1])):
                l = headers[1][i].strip().split(';')
                for j in range(len(l)):
                    l[j] = l[j].strip()
                    if '=' in l[j]:
                        l[j] = l[j].split('=')
                k += l
            headers[1] = k
        elif headers[0] in ('Authenticate', 'Proxy-Authorization'):
            l = headers[1].split(" ")
            k = []
            for i in l:
                if i:
                    k.append(i)
            headers[1] = k
        elif headers[0] == 'Cookie':
            headers[1] = headers[1].split(';')
            k = {}
            for i in range(len(headers[1])):
                t = headers[1][i].split('=')
                k[t[0]] = t[1]
            headers[1] = k
        elif headers[0] in ('If-Modified-Since', 'If-Unmodified-Since', 'Date'):
            headers[1] = datetime.strptime(headers[1], http_date_format)
        else:
            headers[1] = headers[1].strip()
        for handler in custom_handlers:
            handler(data)

        # TODO: If-Range,Range headers
        return headers

    @staticmethod
    def _process_url(url):
        if '?' in url:
            k = url.split('?')
            l = k[1].split('&')
            k[1] = {}
            for i in range(len(l)):
                j = l[i].split('=')
                k[1][j[0]] = j[1]
            return tuple(k)
        else:
            return url,
