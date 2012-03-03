#!/usr/bin/env python
#-*-coding:utf-8-*-

from web.contrib.template import render_jinja

def getAdminRender():
    render = render_jinja(
        'templates/admin',                      # set template directory
        encoding = 'utf-8',               # encoding
    )
    return render

admin_render = getAdminRender()


# Add/override some global functions
# render._lookup.globals.update(
#         var = newvar,
#         var2 = newvar2,
#)


