#!/usr/bin/env python
#-*- coding:utf-8

import web
from controllers import *

urls = (
    "", "index",
    
    # login in, login out
    "/login", "login",
    "/logout", "logout",

    # post
    "/quickpost", "quickpost",
    "/posts", "allposts",                                  # all posts list
    "/category-posts/([-\w]+)", "posts_by_category",
    "/post/add", "addpost",
    "/post/edit/(\d+)", "editpost",
    "/post/delete", "delpost",
    "/post/filter", "filterpost",
    "/pages", "allpages",
    "/page/add", "addpage",
    "/page/delete", "delpages",
    "/page/edit/(\d+)", "editpage",
    
    # comment
    "/comments", "allcomments",
    "/spam-comments", "spamcomments",
    "/comment/delete/(\d+)", "delcomment",
    "/comment/bulk-delete", "delcomments",
    "/comment/edit/(\d+)", "editcomment",
    "/comment/reply", "replycomment",
    "/comment/mark/(\d+)", "markcomment",
    

    # category
    "/categories", "categories",
    "/category/add", "addcategory",
    "/category/delete", "delcategory",
    "/category/edit/(\d+)", "editcategory",
    
    # links
    "/links", "links",
    "/link/add", "addlink",
    "/link/edit/(\d+)", "editlink",
    "/link/delete", "dellinks",

    # settings
    "/settings", "settings",
    "/comment-setting", "comment_setting",

    "/users", "allusers",
    "/profile", "profile",
    
    # media
    "/media", "media"
)


app_admin = web.application(urls, globals(), autoreload=True)
