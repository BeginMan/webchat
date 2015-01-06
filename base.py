# coding=UTF-8

import tornado.web

import logging


class BaseHandler(tornado.web.RequestHandler):
    """
    """
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)


    def _get_current_user(self, callback):
        """
        一个异步方法加载当然用户,callback 函数将接受当前用户或None作为参数'user'
        """
        user_id = self.get_secure_cookie("user")
        if not user_id:
            logging.warning(u"用户Cookie没有找到")
            callback(user=None)
            return


        def query_callback(result):
            if result == "null" or not result:
                logging.warning(u"用户不存在")
                user = {}
            else:
                user = tornado.escape.json_decode(result)

            self._current_user = user
            self.current_user = user
            callback(user=user)

        # query_callback 作为回调函数加载当前用户
        # 存储： user:name, 如： user:fangpeng
        return self.application.client.get("user:" + user_id, query_callback)



    def render_default(self, template_name, **kwargs):
        # 设置模板变量
        if not hasattr(self, '_current_user'):
            self._current_user = None

        kwargs['user'] = self._current_user
        kwargs['path'] = self.request.path;
        if hasattr(self, 'room'):
            kwargs['room'] = int(self.room)
        else: kwargs['room'] = None
        kwargs['apptitle'] = self.application.settings['apptitle']

        if not self.request.connection.stream.closed():
            try:
                self.render(template_name, **kwargs)
            except: pass
    
