"""
    File Name: app.py.
    Description: Tornado's application.
"""
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options


define("port", default=7000, help="Run server on the given port!", type=int)


class IndexHandler(tornado.web.RequestHandler):
    """
    """
    def get(self):
        self.render("index.html")


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r'/', IndexHandler)],
                                  template_path=os.path.join(os.path.dirname(__file__),
                                                             "templates"),
                                  debug=True)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

