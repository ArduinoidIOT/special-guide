
from MultiServer import Server
from HTTPResponseGenerator import redirect, Response, NullResponse

if __name__ == '__main__':
    app = Server(addr='0.0.0.0',keep_alive=False)
    @app.route('/')
    def noob(req):
        return "<h1>HEY NOOBS {}</h1>".format(req.addr)

    # @app.errorhandler(404)
    # def nobo(er):
    #     return 404, "<h1>NOPE</h1>"

    app.run()