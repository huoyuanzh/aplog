#!/usr/bin/env python
#-*-coding:utf-8-*-

##################################
#  this module is for sidebar  
#     use of blog
##################################
import web
from sqlalchemy import func, extract
from models import Post, Term, Link, Comment


# get pages
def pages():
    pages = web.ctx.orm.query(Post).filter(Post.content_type=='page').\
            filter(Post.status=='publish').order_by('posts.menu_order DESC')
    return pages


# get categories
def categories():
    return web.ctx.orm.query(Term).filter(Term.type=='category').all()
           #order_by('terms.order')


# get tags
def tags(count=25):
    return web.ctx.orm.query(Term).filter(Term.type=='tag').\
           order_by("terms.count DESC")[:count]

# get links
def links():
    return web.ctx.orm.query(Link).all()

# get recent comments
def recentcomments(count=7):
    return web.ctx.orm.query(Comment).filter(Comment.status=='approved').\
           order_by("comments.created DESC")[:count]

# get archives
def archives():
    archive = web.ctx.orm.query(
        extract('month', Post.created).label('month'),
        Post.created,
        func.count('*').label('count')
    ).filter(Post.content_type=='post').group_by('month').all()
    ret = []
    for month, date, count in archive:
        d = {}
        d['date'] = date
        d['count'] = count
        ret.append(d)
    return ret
