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


class SsidHandler(BaseHandler):
    """
    """
    @gen.coroutine
    def get(self, user_id):
        print user_id
        ssid = yield self.session.query("""SELECT id,name,pass_word,is_activated FROM "ssidconfig"
                                        WHERE user_id='{0}' LIMIT 1""".format(int(user_id)))
        data = {
            "code": "1",
            "msg": "success",
        }
        if not ssid:
            data['content'] = None
        else:
            data['content'] = {
                "ssid_name": ssid[0]['name'],
                "id": ssid[0]['id'],
                "pass_word": ssid[0]['pass_word'],
                "is_activated": "1" if ssid[0]['is_activated'] else "0"
            }
        self.finish(data)
        ssid.free()

    @gen.coroutine
    def post(self):
        print self.request.body
        json_data = json.loads(self.request.body)
        user_id = json_data.get("user_id", None)
        ssid_name = json_data.get("ssid_name", None)
        pass_word = json_data.get("pass_word", None)
        if not user_id or not ssid_name or not pass_word:
            self.finish({
                "code": "0",
                "msg": "No user_id or ssid_name or pass_word."
            })
            return

        try:
            ssid = yield self.session.query("""INSERT INTO "ssidconfig" (user_id, name, pass_word)
                                            VALUES ('{0}', '{1}', '{2}')""".format(int(user_id),
                                            ssid_name, pass_word))
            ssid.free()
        except Exception as e:
            print "Add ssid error:{0}".format(e)
            if str(e).find("name_key") >= 0:
                data = {
                    "code": "0",
                    "msg": "Ssid exists."
                }
            else:
                data = {
                    "code": "0",
                    "msg": "Database error."
                }
            self.finish(data)
            return

        user = yield self.session.query("""SELECT id FROM "user" WHERE id='{0}'
                                        LIMIT 1""".format(int(user_id)))
        if not user:
            user.free()
            self.finish({
                "code": "0",
                "msg": "Login failed."
            })
            return
        #login
        self.finish({
            "code": "1",
            "msg": "success",
            "content": {
                "user_id": user[0]['id']
            }
        })
        user.free()


class EditSsidHander(BaseHandler):
    """
    """
    @gen.coroutine
    def post(self):
        print self.request.body
        json_data = json.loads(self.request.body)
        user_id = json_data.get("user_id", None)
        orig_ssid_id = json_data.get("orig_ssid_id", None)
        ssid_name = json_data.get("ssid_name", None)
        pass_word = json_data.get("pass_word", None)
        is_activated = json_data.get("is_activated", None)
        if not user_id or not orig_ssid_id or not ssid_name \
            or not pass_word or not is_activated:
            self.finish({
                "code": "0",
                "msg": "Some parameters needed."
            })
            return

        ssid = yield self.session.query("""SELECT id FROM "ssidconfig" WHERE id='{0}'
                                        LIMIT 1""".format(int(orig_ssid_id)))
        if not ssid:
            ssid.free()
            self.finish({
                "code": "0",
                "msg": "No ssid."
            })
            return
        is_activated = True if is_activated == "1" else False
        try:
            result = yield self.session.query("""UPDATE "ssidconfig" SET name='{0}',
                                                pass_word='{1}', is_activated='{2}'
                                                WHERE id='{3}'""".format(ssid_name,
                                                pass_word, is_activated, int(orig_ssid_id)))
            result.free()
        except Exception as e:
            print "Update ssid error:{0}".format(e)
            if str(e).find("name_key") >= 0:
                data = {
                    "code": "0",
                    "msg": "Ssid name exists."
                }
            else:
                data = {
                    "code": "0",
                    "msg": "Database error."
                }
            self.finish(data)
            return
        self.finish({
            "code": "1",
            "msg": "success"
        })


class ProfileHandle(BaseHandler):
    """
    """
    @gen.coroutine
    def get(self, user_id):
        print user_id
        user = yield self.session.query("""SELECT id,user_name,phone,join_date,email
                                        FROM "user" WHERE id='{0}' LIMIT 1"""\
                                        .format(int(user_id)))
        data = {
            "code": "1",
            "msg": "success"
        }
        if not user:
            data['content'] = None
        else:
            data['content'] = {
                "user_id": user[0]['id'],
                "user_name": user[0]['user_name'],
                "phone": user[0]['phone'],
                "email": user[0]['email']
            }
        self.finish(data)
        user.free()

    @gen.coroutine
    def post(self):
        print self.request.body
        json_data = json.loads(self.request.body)
        user_id = json_data.get("user_id", None)
        user_name = json_data.get("user_name", "")
        email = json_data.get("email", "")
        if not user_id:
            self.finish({
                "code": "0",
                "msg": "Need user_id."
            })
            return

        user = yield self.session.query("""SELECT id FROM "user" WHERE id='{0}'
                                        LIMIT 1""".format(int(user_id)))
        if not user:
            user.free()
            self.set_status(404)
            self.finish({
                "code": "0",
                "msg": "No user."
            })
            return

        try:
            result = yield self.session.query("""UPDATE "user" SET user_name='{0}',
                                                email='{1}' WHERE id='{2}'"""\
                                                .format(user_name, email, int(user_id)))
            result.free()
        except Exception as e:
            print "Update user error:{0}".format(e)
            data = {
                "code": "0",
            }
            if str(e).find("name_key") >= 0:
                data['msg'] = "User name exists."
            elif str(e).find("email_key") >= 0:
                data['msg'] = "Email exists."
            else:
                data['msg'] = "Database error."
            self.finish(data)
            return

        self.finish({
            "code": "1",
            "msg": "success"
        })


class DeviceHandle(BaseHandler):
    """
    """
    @gen.coroutine
    def get(self, user_id, page, size):
        pass

    @gen.coroutine
    def post(self):
        print self.request.body
        json_data = json.loads(self.request.body)
        description = json_data.get("description", "")
        mac_address = json_data.get("mac_address", None)
        is_activated = json_data.get("is_activated", "1")
        user_id = json_data.get("user_id", None)
        if not user_id or not mac_address:
            self.finish({
                "code": "0",
                "msg": "No user_id or mac_address."
            })
            return

        mac_address = mac_address.lower()
        is_activated = True if is_activated == "1" else False
        join_date = datetime.datetime.utcnow()
        try:
            result = yield self.session.query("""INSERT INTO "device" (user_id,\
                                                mac_address, description, is_activated,\
                                                join_date) VALUES ('{0}', '{1}', '{2}',\
                                                '{3}', '{4}')""".format(int(user_id, mac_address,
                                                description, is_activated, join_date)))
            result.free()
        except Exception as e:
            print "Add device error:{0}".format(e)
            data = {
                "code": "0"
            }
            if str(e).find("mac_address_key") >= 0:
                data['msg'] = "Mac address exists."
            else:
                data['msg'] = "Database error."
            self.finish(data)
            return

        self.finish({
            "code": "1",
            "msg": "success"
        })



class PerDeviceHandler(BaseHandler):
    """
    """
    @gen.coroutine
    def get(self, user_id, device_id):
        pass

    @gen.coroutine
    def post(self):
        pass


class IndexHandler(tornado.web.RequestHandler):
    """
    """
    def get(self):
        self.render("index.html")


url_map = [(r'/', IndexHandler),
           (r'/auth/register/v1', RegisterHandler),
           (r'/auth/unregister/v1', None),
           (r'/ssid/add/v1', SsidHandler),
           (r'/ssid/get/(?P<user_id>[0-9]+)/v1', SsidHandler),
           (r'/ssid/edit/v1', EditSsidHander),
           (r'/profile/get/(?P<user_id>[0-9]+)/v1', ProfileHandle),
           (r'/profile/edit/v1', ProfileHandle),
           (r'/devices/device/add/v1', DeviceHandle),
           (r'/devices/get/(?P<user_id>[0-9]+)/(?P<page>[0-9]+)/(?P<size>[0-9])+/v1',
            DeviceHandle),
           (r'/devices/device/delete/v1', PerDeviceHandler),
           (r'/devices/device/get/(?P<user_id>[0-9]+)/(?P<device_id>)/v1',
            PerDeviceHandler)
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

