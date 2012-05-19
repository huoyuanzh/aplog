#!/usr/bin/env python
#-*-coding:utf-8-*-


__all__ = [
    "POST_PER_PAGE", "ADMIN_POST_PER_PAGE", "ADMIN_POST_PER_PAGE",
    "render", "admin_render",
    "render_template",
    ]


import os
import re
import web
import cgi
from web.contrib.template import render_jinja
from jinja2 import Environment, FileSystemLoader

from pygments import highlight
from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter


POST_PER_PAGE = 5
ADMIN_POST_PER_PAGE = 7
ADMIN_COMMENT_PER_PAGE = 8

cgi.maxlen = 5 * 1024 * 1024     # POST data maxlen: 5MB

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


# implement "read more..." feature
def post_excerpt(post):
    end = post.find('<!-- pagebreak -->')    # find <!-- pagebreak >
    if end != -1:
        return post[:end]
    else:
        return post

# highlight code in post content
def code_highlight(content):
    codes = re.findall('<code>.*?</code>', content, re.U | re.S)
    for c in codes:
        code = c[6:-7]
        try:
            lexer = guess_lexer(code)
        except:
            lexer = get_lexer_by_name('python', stripall=True)
        code = highlight(code, lexer, HtmlFormatter())
        content = content.replace(c, code)
    return content
    

        
# render template with specific template name
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)
    jinja_env.filters['excerpt'] = post_excerpt
    #jinja_env.filters['highlight'] = code_highlight
    
    #jinja_env.update_template_context(context)
    return jinja_env.get_template(template_name).render(context)





