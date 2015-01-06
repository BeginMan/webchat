# coding=UTF-8

import tornado.web
import tornado.escape
from base import BaseHandler
import logging



class LoginHandler(BaseHandler):
    """
    """
    def get(self):
        content = ('<h2>Login</h2>'
        + '<form class="form-inline" action="/login" method="post"> '
        + '<input type="hidden" name="start_direct_auth" value="1">'
        + '<input class="form-control" type="text" name="name" placeholder="Your Name"> '
        + '<input class="form-control" type="text" name="email" placeholder="Your Email"> '
        + '<input type="submit" class="btn btn-default" value="Sign in">'
        + '</form>')
        self.render_default("index.html", content=content)

    def post(self):
        """
        Callback for third party authentication (last step).
        """
        name = self.get_argument('name')
        email = self.get_argument('email')
        user = {'name':name, 'email':email}

        self.application.client.set("user:" + name, tornado.escape.json_encode(user))
        # Save user id in cookie.
        self.set_secure_cookie("user", name)
        self.application.usernames[user["email"]] =  user["email"]
        # Closed client connection
        if self.request.connection.stream.closed():
            logging.warning("Waiter disappeared")
            return
        self.redirect("/")

        


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect("/")
        
    
