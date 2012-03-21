#!/usr/bin/env python
#-*-coding:utf-8-*-

import web
from sqlalchemy import and_, or_, extract
from markdown import markdown

from models import *
from config import render, render_template                                   # render for jinja2
from config import POST_PER_PAGE
from forms import comment_form
from akismet import Akismet, AkismetError, APIKeyError
import sidebar


def get_sidebar():
    return {'pages': sidebar.pages(), 'categories': sidebar.categories(),
            'tags': sidebar.tags(), 'links': sidebar.links(),
            'recentcomments': sidebar.recentcomments(), 'archives': sidebar.archives()}


# customize your own notfound page
def notfound():
    return web.notfound(render.notfound())
    # can also use template result like below, either is ok:
    # return web.notfound(render.notfound())
    # return web.notfound(str(render.notfound()))


# the index page
class index:
    def GET(self):
        i = web.input(page=1)           # get input data
        try:
            page = int(i.page)
        except:
            page = 1
        context = {}
        post_count = web.ctx.orm.query(Post).\
                     filter(Post.content_type=='post').count()
        # calculate how many pages there should be
        if post_count % POST_PER_PAGE == 0:
            page_count = post_count / POST_PER_PAGE
        else:
            page_count = post_count / POST_PER_PAGE + 1
        context['widget'] = get_sidebar()
        context['page_count'] = page_count
        context['posts'] = web.ctx.orm.query(Post).\
                           filter(Post.status=='publish').\
                           filter(Post.content_type=='post').\
                           order_by('posts.created DESC')\
                           [(page-1)*POST_PER_PAGE:page*POST_PER_PAGE]     # get all posts
        context['page'] = page
        context['location'] = 'home'
        return render_template('index.html', **context)

# single post page
class singlepost:
    def get_post_by_slug(self, slug):
        post = web.ctx.orm.query(Post).\
               filter(Post.slug==slug).first()
        if post: return post
        else: return None

    def get_post_by_id(self, id):
        post = web.ctx.orm.query(Post).\
               filter(Post.id==id).first()
        if post: return post
        else: return None

    # get post by slug or id
    def get_post(self, arg):
        try:
            arg = int(arg)
            post = self.get_post_by_id(arg)
        except:
            post = self.get_post_by_slug(arg)
        return post

    # validate comment with akismet
    def validate_comment(self, comment):
        akismet_enable = web.ctx.orm.query(Option).\
                         filter(Option.name=='comment_akismet_enable').first()
        if (not akismet_enable) or (not akismet_enable.value):
            return
        akismet_key = web.ctx.orm.query(Option).\
                      filter(Option.name=='comment_akismet_key').first()
        domain = web.ctx.get('homedomain', '')
        # create an Akismet instance
        ak = Akismet(
            key=akismet_key.value,                  # akismet key
            blog_url=domain                         # your blog url
        )
        try:
            if ak.verify_key():
                data = {
                    'user_ip': web.ctx.get('ip', ''),
                    'user_agent': web.ctx.env.get('HTTP_USER_AGENT', ''),
                    'referer': web.ctx.env.get('HTTP_REFERER', 'unknown'),
                    'comment_type': 'comment',
                    'comment_author': comment.author.encode('utf-8')
                }
                if ak.comment_check(comment.content.encode('utf-8'), data=data, build_data=True):
                    comment.status = 'spam'
                    ak.submit_spam(comment.content.encode('utf-8'), data=data, build_data=True)
                    
        except (AkismetError, APIKeyError):
            pass
                
        
    def GET(self, arg):
        post = self.get_post(arg)
        f = comment_form()
        if post:
            post.view_count += 1
            widget = get_sidebar()
            widget['relative_posts'] = sidebar.relative_posts(post)               # get relative posts in sidebar widget
            return render_template('single.html',
                                   post=post, widget=widget,
                                   form=f, admin=web.ctx.session.username,
                                   location='single')
        else:
            raise web.notfound()
        
    def POST(self, arg):
        post = self.get_post(arg)
        f = comment_form()
        if not f.validates():
            return render.single(post=post, widget=get_sidebar(),
                                 form=f, location='single')
        else:
            # store the comment data here
            comment = Comment(
                author = f.author.value,
                email = f.email.value,
                url = f.url.value,
                content = markdown(f.comment.value),
                ip = web.ctx.get('ip', ''),
                post_id = post.id
            )
            web.ctx.orm.add(comment)
            post.comment_count += 1                   # update the comment_count of this post
            post.view_count -= 1                      # as we will redirect to the same page next, so~
           # self.validate_comment(comment)
            web.ctx.orm.commit()
            web.seeother(comment.get_absolute_url())


# posts by specific category
class category:
    def GET(self, arg):
        if not arg: raise web.notfound()
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        try:
            arg = int(arg)
            term = web.ctx.orm.query(Term).\
                   filter(Term.id==arg).\
                   filter(Term.type=='category').first()
        except:
            term = web.ctx.orm.query(Term).\
                   filter(Term.slug==arg).\
                   filter(Term.type=='category').first()
        if not term:
            raise web.notfound()
        posts = term.posts.filter(Post.status=='publish').\
                order_by('posts.created DESC')            # order by created datatime DESC
        return render_template('archive.html', archtype='category',
                               name=term.name, posts=posts,
                               page=page, widget=get_sidebar(),
                               location='category')

# posts by specific tag
class tag:
    def GET(self, arg):
        if not arg: raise web.notfound()
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        try:
            arg = int(arg)
            term = web.ctx.orm.query(Term).\
                   filter(and_(Term.id==arg,Term.type=='tag')).first()
        except:
            term = web.ctx.orm.query(Term).\
                   filter(Term.slug==arg).\
                   filter(Term.type=='tag').first()
        if not term: raise web.notfound()
        posts = term.posts.filter(Post.status=='publish').\
                order_by('posts.created DESC')           # order by created datetime DESC
        return render_template('archive.html', archtype='tag',
                               name=term.name, posts=posts,
                               page=page, widget=get_sidebar(),
                               location='tag')
            
# posts by specific date
class archives:
    def getPostByMonth(self, year, month):
        posts = web.ctx.orm.query(Post).\
                filter(and_(Post.content_type=='post', Post.status=='publish')).\
                filter(extract('year', Post.created)==int(year)).\
                filter(extract('month', Post.created)==int(month)).\
                order_by('posts.created DESC')
        return posts
        
    def GET(self, year, month):
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        if year and month:
            posts = self.getPostByMonth(year, month)
            return render_template('archive.html', archtype='archive',
                                   year=year, month=month, posts=posts,
                                   page=page, widget=get_sidebar(),
                                   location='archives')
        else:
            raise web.notfound()
        
    
class search(object):

    def GET(self):
        i = web.input()
        page = i.get('page', 1)
        referer = web.ctx.env.get('HTTP_REFERER', '/')
        keyword = i.s               # get search stuff
        if not keyword:             # if search nothing, just come back
            raise web.seeother(referer)
        keyword = "%s%s%s" % ('%', keyword, '%')
        query = web.ctx.orm.query(Post).filter(Post.content_type=='post').\
                filter(Post.status=='publish')
        # search title and content
        posts = query.filter(or_(Post.title.like(keyword), Post.content.like(keyword))).\
                             order_by("posts.created DESC")
        return render_template('search.html', posts=posts,
                               query=keyword[1:-1], page=page,
                               widget=get_sidebar(), location='search')

# rss feed                                                        
class feed:
    def GET(self):
        posts = web.ctx.orm.query(Post).filter(Post.content_type=='post').\
                order_by("posts.created DESC").all()[:10]
        web.header('Content-Type', 'text/xml')
        domain = web.ctx.get('homedomain', 'http://example.com')
        return render_template('feed.xml', domain=domain, posts=posts)

class sitemap:
    def GET(self):
        pages = web.ctx.orm.query(Post).filter(Post.content_type=='page').\
                filter(Post.status=='publish').\
                order_by("posts.created DESC")
        posts = web.ctx.orm.query(Post).filter(Post.content_type=='post').\
                filter(Post.status=='publish').\
                order_by("posts.created DESC")
        terms = web.ctx.orm.query(Term).all()
        archives = sidebar.archives()
        domain = web.ctx.get('homedomain', 'http://aplog.sinaapp.com')
        web.header('Content-Type', 'text/xml')
        return render_template('sitemap.xml', pages=pages,
                               posts=posts, terms=terms,
                               archives=archives, domain=domain)
        
