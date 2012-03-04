#!/usr/bin/env python
#-*-coding:utf-8-*-


__all__ = [
    "POST_PER_PAGE", "ADMIN_POST_PER_PAGE", "ADMIN_POST_PER_PAGE",
    "render", "admin_render",
    "render_template",
    ]


import os
import web
from web.contrib.template import render_jinja
from jinja2 import Environment, FileSystemLoader

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


# render template with specific template name
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    #jinja_env.update_template_context(context)
    return jinja_env.get_template(template_name).render(context)





