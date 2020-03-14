from MultiServer import Server
from HTTPResponseGenerator import redirect, Response, NullResponse

if __name__ == '__main__':
    app = Server()
    @app.route('/')
    def noob(req):
        return "<h1>HEY NOOBS</h1>"

    @app.error_handler(404)
    def nobo(req):
        return 404,"<H1>HEY NOOB, THERE'S NOTHING HERE</H1>"

    app.run()