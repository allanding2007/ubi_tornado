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


class RegisterHandler(BaseHandler):
    """
    """
    @gen.coroutine
    def get(self):
        result = yield self.session.query('SELECT id,user_name FROM "user" LIMIT 1')
        self.write({"content": result.items(),
                    "code": "1"})
        self.finish()
        result.free()

    @gen.coroutine
    def post(self):
        print self.request.body
        json_data = json.loads(self.request.body)
        phone = json_data.get("phone", None)
        code = json_data.get("code", None)
        if not phone or not code:
            self.set_status(200)
            self.finish({
                "code": "0",
                "msg": "Need phone or code."
            })
            return

        verify_code = yield self.session.query("""SELECT id, code FROM "verifycode" WHERE
                                                phone='{0}' ORDER BY id DESC LIMIT 1"""\
                                               .format(phone))
        if not verify_code:
            self.set_status(200)
            self.finish({
                "code": "0",
                "msg": "NO  code."
            })
            verify_code.free()
            return

        if verify_code[0]['code'] != code:
            self.set_status(200)
            self.finish({
                "code": "0",
                "msg": "Phone and Code not match."
            })
            verify_code.free()
            return

        exist_user = yield self.session.query("""SELECT id FROM "user" WHERE phone='{0}'
                                                LIMIT 1""".format(phone))
        time_stamp = datetime.datetime.utcnow()
        if not exist_user:
            try:
                result = yield self.session.query("""INSERT INTO "user" (user_name, phone, join_date\
                                                     ) VALUES ('{0}', '{1}', '{2}')""".format(phone,
                                                    phone, time_stamp))
                result.free()
            except Exception as e:
                print "Add user error:{0}".format(e)
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
                self.set_status(200)
                self.finish(data)
                return

            exist_user = yield self.session.query("""SELECT id FROM "user" WHERE phone='{0}'
                                                    LIMIT 1""".format(phone))
        if not exist_user:
            self.set_status(200)
            self.finish({
                "code": "0",
                "msg": "Register user error."
            })
            exist_user.free()
            return

        ssid_config = yield self.session.query("""SELECT id FROM "ssidconfig" WHERE user_id={0}
                                                LIMIT 1""".format(exist_user[0]['id']))
        data = {
            "code": "1",
            "msg": "success",
            "content": {}
        }
        if not ssid_config:
            data['content']['has_ssid'] = "no"
        else:
            data['content']['has_ssid'] = "yes"
        self.finish(data)
        ssid_config.free()


class UnregisterHandler(BaseHandler):
    """
    """
    def post(self):
        print self.request.body
        json_data = json.loads(self.request.body)
        if "user_id" not in json_data:
            self.finish({
                "code": "0",
                "msg": "No user_id."
            })


class IndexHandler(tornado.web.RequestHandler):
    """
    """
    def get(self):
        self.render("index.html")


url_map = [(r'/', IndexHandler),
           (r'/auth/register/v1', RegisterHandler),
           (r'/auth/unregister/v1', None)
           ]


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=url_map,
                                  template_path=os.path.join(os.path.dirname(__file__),
                                                             "templates"),
                                  debug=config.DEBUG)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

