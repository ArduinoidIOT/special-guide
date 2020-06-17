from MultiServer import Server

s = Server(port=10000)


@s.route('/')
def route(request):
    return "Hello world"


if __name__ == '__main__':
    s.run()
