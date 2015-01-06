# coding=utf-8

import os, os.path
import logging
import sys
from threading import Timer
import string
import random

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.auth
import tornado.options
import tornado.escape
from tornado.options import define, options

from tornado import gen

import brukva

from base import BaseHandler
from auth import LoginHandler
from auth import LogoutHandler

tornado.options.define("port", default=8888, help="run on the given port", type=int)



class MainHandler(BaseHandler):
    """
    聊天主函数
    """

    @tornado.web.asynchronous
    def get(self, room=None):
        if not room:
            self.redirect("/room/1")
            return
        self.room = str(room)
        # 获取当前用户.
        self._get_current_user(callback=self.on_auth)


    def on_auth(self, user):
        if not user:
            self.redirect("/login")
            return
        # 加载这个房间中50条历史记录.
        self.application.client.lrange(self.room, -50, -1, self.on_conversation_found)


    def on_conversation_found(self, result):
        if isinstance(result, Exception):
            raise tornado.web.HTTPError(500)

        # JSON-decode messages.
        messages = []
        for message in result:
            messages.append(tornado.escape.json_decode(message))

        content = self.render_string("messages.html", messages=messages)
        self.render_default("index.html", content=content, chat=1)



class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    """
    websocket
    """

    @gen.engine
    def open(self, room='root'):
        """
        当socket已经打开，通过Redis Pub/Sub开始订阅该聊天组
        """
        # 检查房间是否设置.
        if not room:
            self.write_message({'error': 1, 'textStatus': 'Error: No room specified'})
            self.close()
            return
        self.room = str(room)
        self.new_message_send = False

        # 创建redis连接.
        self.client = redis_connect()

        # 订阅一个给定的聊天组.
        self.client.subscribe(self.room)
        self.subscribed = True
        self.client.listen(self.on_messages_published)      # 监听
        logging.info(u'新用户已连接房间： ' + room)

    #发布消息
    def on_messages_published(self, message):
        m = tornado.escape.json_decode(message.body)
        # 发送消息给另一个客户端并结束连接
        self.write_message(dict(messages=[m]))


    def on_message(self, data):
        """
        Callback ：当有新消息通过socket时.
        """
        logging.info(u'接受新消息 %r', data)
        try:
            datadecoded = tornado.escape.json_decode(data)
            message = {
                '_id': ''.join(random.choice(string.ascii_uppercase) for i in range(12)),
                'from': self.get_secure_cookie('user'),
                'body': tornado.escape.linkify(datadecoded["body"]),
            }

            if not message['from']:
                logging.warning(u"用户Guest认证失败")
                message['from'] = 'Guest'

        except Exception, err:
            self.write_message({'error': 1, 'textStatus': u'错误的输入 ... ' + str(err) + data})
            return

        # Redis处理消息.
        try:
            # 转换json文本.
            message_encoded = tornado.escape.json_encode(message)
            # 持久存储信息的使用.
            self.application.client.rpush(self.room, message_encoded)
            # 在redis频道中发布消息.
            self.application.client.publish(self.room, message_encoded)
        except Exception, err:
            e = str(sys.exc_info()[0])
            self.write_message({'error': 1, 'textStatus': u'写入数据库失败: ' + str(err)})
            return


        self.write_message(message)
        return


    def on_close(self):
        """
        socket关闭时,释放相关资源.
        """
        logging.info(u"Socket关闭，释放资源....")
        if hasattr(self, 'client'):
            # Unsubscribe 取消订阅尚未结束.
            if self.subscribed:
                self.client.unsubscribe(self.room)
                self.subscribed = False

            # issue: https://github.com/evilkost/brukva/issues/25
            t = Timer(0.1, self.client.disconnect)
            t.start()



class Application(tornado.web.Application):
    def __init__(self):

        handlers = [
            (r"/", MainHandler),
            (r"/room/([a-zA-Z0-9]*)$", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/socket", ChatSocketHandler),
            (r"/socket/([a-zA-Z0-9]*)$", ChatSocketHandler),
        ]

        # Settings:
        settings = dict(
            cookie_secret = "43osdETzKXasdQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url = "/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            # xsrf_cookies= True,
            autoescape="xhtml_escape",

            db_name = 'chat',
            # 模板标题.
            apptitle = 'WebChat: Tornado/Redis/brukva/Websockets',
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        # 存储用户.
        self.usernames = {}

        # 连接Redis.
        self.client = redis_connect()


def redis_connect():
    """
    通过Heroku建立一个异步的redis服务器
    """
    redistogo_url = os.getenv('REDISTOGO_URL', None)
    if redistogo_url == None:
        REDIS_HOST = 'localhost'
        REDIS_PORT = 6379
        REDIS_PWD = None
        REDIS_USER = None
    else:
        redis_url = redistogo_url
        redis_url = redis_url.split('redis://')[1]
        redis_url = redis_url.split('/')[0]
        REDIS_USER, redis_url = redis_url.split(':', 1)
        REDIS_PWD, redis_url = redis_url.split('@', 1)
        REDIS_HOST, REDIS_PORT = redis_url.split(':', 1)

    client = brukva.Client(host=REDIS_HOST, port=int(REDIS_PORT), password=REDIS_PWD)
    client.connect()
    return client



def main():
    tornado.options.parse_command_line()
    application = Application()
    application.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()