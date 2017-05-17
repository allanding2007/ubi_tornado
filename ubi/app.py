"""
    File Name: app.py.
    Description: Tornado's application.
"""
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado import gen
import queries
import json
import datetime
from tornado.options import define, options
from settings import check_env


define("port", default=7000, help="Run server on the given port!", type=int)
config = check_env()

class BaseHandler(tornado.web.RequestHandler):
    """
    """
    def initialize(self):
        self.session = queries.TornadoSession(config.POSTGRES_URI)


class UserHandler(BaseHandler):
    """
    """
    @gen.coroutine
    def get(self):
        result = yield self.session.query('SELECT id,name FROM "user"')
        self.write({"content": result.items(),
                    "code": "1"})
        self.finish()
        result.free()

    @gen.coroutine
    def post(self):
        print self.request.body
        json_data = json.loads(self.request.body)
        user_name = json_data.get("user_name", None)
        phone = json_data.get("phone", None)
        is_activated = json_data.get("is_activated", None)
        if not phone or not is_activated:
            self.write({
                "code": "0",
                "msg": "Need phone or is_activated."
            })

        is_activated = True if is_activated == "1" else False
        if not user_name:
            user_name = phone
        time_stamp = datetime.datetime.utcnow()
        try:
            result = yield self.session.query("""INSERT INTO "user" (name, phone, join_date, \
                                              is_activated) VALUES ('{0}', '{1}', '{2}', '{3}')"""\
                                              .format(user_name, phone, time_stamp, is_activated))
            self.write({"code": "1", "msg": "success"})
            result.free()
        except Exception as e:
            data = dict()
            if str(e).find("user_name_key") >= 0:
                data = {
                    "code": "0",
                    "msg": "User exists."
                }
            else:
                data = {
                    "code": "0",
                    "msg": "Database error."
                }
            self.write(data)

        self.finish()


class IndexHandler(tornado.web.RequestHandler):
    """
    """
    def get(self):
        self.render("index.html")


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r'/', IndexHandler),
                                            (r'/user/', UserHandler),
                                            ],
                                  template_path=os.path.join(os.path.dirname(__file__),
                                                             "templates"),
                                  debug=config.DEBUG)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

