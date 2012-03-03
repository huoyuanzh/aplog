#!/usr/bin/env python
#-*-coding:utf-8-*-

import web
from web.contrib.template import render_jinja

POST_PER_PAGE = 5
ADMIN_POST_PER_PAGE = 7
ADMIN_COMMENT_PER_PAGE = 8

def getRender():
    """ get render for public pages """
    render = render_jinja(
        'templates',                      # set template directory
        encoding = 'utf-8',               # encoding
    )
    return render

def getAdminRender():
    render = render_jinja(
        'templates/admin',                      # set template directory
        encoding = 'utf-8',               # encoding
    )
    return render

render = getRender()
admin_render = getAdminRender()


# Add/override some global functions
# render._lookup.globals.update(
#         var = newvar,
#         var2 = newvar2,
#)


