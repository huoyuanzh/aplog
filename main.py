#!/usr/bin/env python
#-*- coding:utf-8
import web
import admin

from controllers import *
from processors import load_sqla

urls = (
    '/(.*)/', 'redirect',             # ensure whether the url ends with a '/' will work
    '/admin', admin.app_admin,
    '/', 'index',
    '/tag/([-\w]+)', 'tag',
    '/category/([-\w]+)', 'category',
    '/archives/(\d{4})/(\d{1,2})', 'archives',
    '/search', 'search',
    '/archive/([-\w]+)', 'singlepost',
    '/page/([-\w]+)', 'singlepost',
    '/feed', 'feed',
)

app = web.application(urls, globals(), autoreload=True)


# tips: to fix the problem that session can't work at Debug mode
if web.config.get('_session') is None:
    store = web.session.DiskStore('sessions')                                       # the store object
    session = web.session.Session(app, store, initializer={'login': 0, 'username': ''})
    web.config._session = session
else:
    session = web.config._session

        
# make session available in sub-apps
def session_hook():
    web.ctx.session = session

    
app.add_processor(load_sqla)
app.add_processor(web.loadhook(session_hook))


app.notfound = notfound             # customize own notfound page

# ensure whether the url ends with a '/' will work
class redirect:
    def GET(self, path):
        web.seeother('/' + path)



if __name__ == '__main__':
    app.run()
