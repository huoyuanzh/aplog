#!/usr/bin/env python
#-*- coding:utf-8
import web
import hashlib
from datetime import datetime
from markdown import markdown

from config import admin_render, ADMIN_POST_PER_PAGE, ADMIN_COMMENT_PER_PAGE
from models import *
from forms import settings_form
from admin.utils import post_slug_validates, term_slug_validates

# a decorator
def login_required(func):
    def function(*args):
        if web.ctx.session.login == 0:
            raise web.seeother("/login")
        else:
            return func(*args)
    return function


class login(object):
    def GET(self):
        return admin_render.login()

    def POST(self):
        i = web.input(name=None, password=None)
        message = "username or password is nil!"
        if i.name and i.password:                                     
            admin = web.ctx.orm.query(User).filter(User.name==i.name).first() 
            if admin:
                if hashlib.md5(i.password).hexdigest() == admin.password:    # password match ?
                    web.ctx.session.login = 1                                # record login information in session
                    web.ctx.session.uid = admin.id
                    web.ctx.session.username = admin.name                        # set username to session
                    web.ctx.session.email = admin.email                      # set user's email to session
                    raise web.seeother("/")                                  # redirect to '/admin'
                else:
                    message = "Wrong password!"
            else:
                message = "User not exist!"
        return admin_render.login(message=message)
                


class logout(object):
    @login_required
    def GET(self):
        web.ctx.session.kill()          # delete the session
        raise web.seeother("/login")


class index(object):
    @login_required
    def GET(self):
        context = {}
        context['post_count'] = web.ctx.orm.query(Post).filter(Post.content_type=='post').count()
        context['comment_count'] = web.ctx.orm.query(Comment).count()
        context['spam_count'] = web.ctx.orm.query(Comment).filter(Comment.status=='spam').count()
        context['page_count'] = web.ctx.orm.query(Post).filter(Post.content_type=='page').count()
        context['category_count'] = web.ctx.orm.query(Term).filter(Term.type=='category').count()
        context['tag_count'] = web.ctx.orm.query(Term).filter(Term.type=='tag').count()
        context['recent_comments'] = web.ctx.orm.query(Comment).\
                                     order_by('comments.created DESC').all()[:5]  # the recent 10 comments
        return admin_render.index(**context)
        
    
class quickpost(object):
    @login_required
    def POST(self):
        i = web.input()
        title = i.title.strip()
        content = i.content.strip()
        tags = i.tags.strip()
        if not (title and content):
            return "<p style='color: red'>Title and content can not be empty!</p>"
        post = Post(title=title, content=markdown(content))
        for item in tags.split(','):
            tag = web.ctx.orm.query(Term).filter(Term.type=='tag').\
                  filter(Term.name==item.strip()).first()
            # tag not exist yet
            if not tag: 
                tag = Term(name=item.strip(), count=0)
                web.ctx.orm.add(tag)
            tag.count += 1
            post.terms.append(tag)
        if i.get('publish', ''):
            post.status = 'publish'
        else:
            post.status = 'draft'
        web.ctx.orm.add(post)
        web.ctx.orm.commit()
        return "<p>Post has been saved!</p>"

        


# all posts list
class allposts(object):
    def all_count(self):
        return web.ctx.orm.query(Post).filter(Post.content_type=='post').count()

    def pub_count(self):
        return web.ctx.orm.query(Post).filter(Post.content_type=='post').\
               filter(Post.status=='publish').count()

    @login_required
    def GET(self):
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        context = {}
        context['page'] = page
        if i.get('status', ''):
            posts = web.ctx.orm.query(Post).filter(Post.content_type=='post').\
                    filter(Post.status==i.status).order_by("posts.created DESC").all()
            context['status'] = i.status
        else:
            posts = web.ctx.orm.query(Post).filter(Post.content_type=='post').\
                    order_by("posts.created DESC").all()
        post_count = len(posts)
        if post_count != 0 and post_count % ADMIN_POST_PER_PAGE == 0:
            page_count = post_count / ADMIN_POST_PER_PAGE
        else:
            page_count = post_count / ADMIN_POST_PER_PAGE + 1
        if page < 1 or page > page_count: raise web.notfound()
        context['posts'] = posts[(page-1)*ADMIN_POST_PER_PAGE:page*ADMIN_POST_PER_PAGE]
        context['page_count'] = page_count
        context['all_count'] = self.all_count()
        context['publish_count'] = self.pub_count()
        context['draft_count'] = context['all_count'] - context['publish_count']
        context['categories'] = web.ctx.orm.query(Term).filter(Term.type=='category').all()
        return admin_render.posts(**context)


# add a new post
class addpost(object):

    def get_admin(self):
        username = web.ctx.session.username
        return web.ctx.orm.query(User).filter(User.name==username).first()

    # get all categories
    def get_categories(self):
        return web.ctx.orm.query(Term).filter(Term.type=='category').all() 
        
    @login_required
    def GET(self):
        cates = web.ctx.orm.query(Term).filter(Term.type=='category').all()
        return admin_render.post(cates=cates, action='add', content_type='post')

    @login_required
    def POST(self):
        i = web.input(category=[])
        title = i.title
        content = i.content
        slug = None
        if i.slug.strip(): slug = i.slug.strip().replace(' ', '-')
        excerpt = i.excerpt
        tags = i.tags
        category_ids = i.category                                    # list of category id
        comment_status = 0
        if i.get('comment_status', '') == 'open': comment_status = 1 # allow comment
        status = 'draft'
        if i.get('publish'):
            status = 'publish'                                      # post should be publish

        # create a Post object 
        post = Post(title=title, content=content,
                    slug=slug,  excerpt=excerpt,
                    status=status, comment_status=comment_status)
        
        # create a dict for a category, add a attribute name 'selected'
        def newcategory(cate):
            return {"id": cate.id, "name": cate.name, "slug": cate.slug, "selected": cate.id in category_ids}

        # title and content can't be empty
        if not (title and content):
            msg = "Post not saved! Title and content can not be empty, please fill them."
            return admin_render.post(post=post, cates=map(newcategory, self.get_categories()),
                                     tags=tags, action="add", content_type='post', msg=msg)

        # slug can not be the same with other post slug
        if slug:
            if not post_slug_validates(slug):
                msg = "Post not saved! Slug should be different form other post slug."
                return admin_render.post(post=post, cates=map(newcategory, self.get_categories()),
                                         tags=tags, action="add", content_type="post", msg=msg)
        
        if not post.excerpt: post.excerpt = post.shortcontent()       
        post.author = self.get_admin()
        web.ctx.orm.commit()
        categories = web.ctx.orm.query(Term).filter(Term.type=='category').\
                                           filter(Term.id.in_(category_ids)).all()
        for cate in categories:
            cate.count += 1                
            post.terms.append(cate)
        for item in tags.split(','):
            tag = web.ctx.orm.query(Term).filter(Term.type=='tag').filter(Term.name==item.strip()).first()
            # tag not exist yet
            if not tag: 
                tag = Term(name=item.strip(), count=0)
                web.ctx.orm.add(tag)
            tag.count += 1
            post.terms.append(tag)
        web.ctx.orm.commit()
        if status == 'publish':
            web.ctx.msg = "The post '%s' has been published." % post.title
        else:
            web.ctx.msg = "The post '%s' has been saved." % post.title
        raise web.seeother("/posts")                                # redirect to post list page
        

        
class editpost(object):
    # get all categories
    def get_categories(self):
        return web.ctx.orm.query(Term).filter(Term.type=='category').all()

    @login_required
    def GET(self, id):
        post = web.ctx.orm.query(Post).filter(Post.id==int(id)).first()
        category_ids = []
        for term in post.terms:
            if term.type == 'category':
                category_ids.append(term.id)
        cates = self.get_categories()
        tags = [term.name for term in post.terms if term.type == 'tag']
        tags = ",".join(tags)
        
        # create a dict for a category, add a attribute name 'selected'
        def newcategory(cate):
            return {"id": cate.id, "name": cate.name, "slug": cate.slug, "selected": cate.id in category_ids}
       
        return admin_render.post(post=post, cates=map(newcategory, self.get_categories()),
                            tags=tags, content_type='post', action='edit')
    @login_required
    def POST(self, id):
        i = web.input(category=[])
        title = i.title
        content = i.content
        slug = None
        if i.slug.strip(): slug = i.slug.strip().replace(' ', '-')
        excerpt = i.excerpt
        tags = i.tags
        category_ids = i.category                                  # list of category id
        comment_status = 0
        status = i.status
        if i.get('unpublish'): status = 'draft'                    # if cancel publish button been press
        if i.get('publish'): status = 'publish'
        if i.get('comment_status', '') == 'open': comment_status = 1        # allow comment
        post = web.ctx.orm.query(Post).filter(Post.id==int(id)).first()
        if not (title and content):
            msg = "Post modification not saved! Title and content can not be empty."
            return admin_render.post(post=post, cates=map(newcategory, self.get_categories()),
                                     tags=tags, action="add", content_type='post', msg=msg)
        # validates post slug
        if slug:
            if not post_slug_validates(slug, int(id)):
                msg = "Post modification not saved! Slug is the same as another post's, please change it."
                return admin_render.post(post=post, cates=map(newcategory, self.get_categories()),
                                         tags=tags, action="edit", content_type="post", msg=msg)

        if not excerpt: excerpt = post.shortcontent()

        # everything is ok, update the post now
        post.title = title
        post.content = content
        post.slug = slug
        post.excerpt = excerpt
        post.status = status
        post.comment_status = comment_status
        post.modified = datetime.now()
        
        # update the original terms' count of posts
        for term in post.terms:
            term.count -= 1
        post.terms = []                             # reset it
        categories = web.ctx.orm.query(Term).filter(Term.type=='category').\
                                           filter(Term.id.in_(category_ids)).all()
        for cate in categories:
            cate.count += 1
            post.terms.append(cate)
        for item in tags.split(','):
            tag = web.ctx.orm.query(Term).filter(Term.type=='tag').filter(Term.name==item.strip()).first()
            # tag not exist yet
            if not tag: 
                tag = Term(name=item.strip(), count=0)
                web.ctx.orm.add(tag)
            tag.count += 1
            post.terms.append(tag)
        web.ctx.orm.commit()
        web.ctx.msg = "The post '%s' has been modified!" % post.title
        raise web.seeother('/posts')

# delete a single post
class delpost(object):
    @login_required
    def GET(self):
        i = web.input()
        try:
            id = int(i.id)
        except:
            raise web.notfound()
        post = web.ctx.orm.query(Post).filter(Post.id==id).first()
        # category and tags' post count decrease one
        for term in post.terms:
            term.count -= 1
        # delete the comments
        for comment in post.comments:
            web.ctx.orm.delete(comment)
        web.ctx.orm.delete(post)
        web.ctx.orm.commit()
        referer = web.ctx.env.get('HTTP_REFERER', '/posts')        # where he deletes ?
        raise web.seeother(referer)                                      # come back


# bulk delete articles
class delposts(object):
    @login_required
    def POST(self):
        i = web.input(checks=[])
        for id in i.checks:
            post = web.ctx.orm.query(Post).filter(Post.id==int(id)).first()
            for term in post.terms:
                term.count -= 1
            for comment in post.comments:
                web.ctx.orm.delete(comment)
            web.ctx.orm.delete(post)
            web.ctx.orm.commit()
        referer = web.ctx.env.get('HTTP_REFERER', '/posts')
        raise web.seeother(referer)

# show posts in specific category
class posts_by_category(object):
    @login_required
    def GET(self, arg):
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        try:
            arg = int(arg)
            cate = web.ctx.orm.query(Term).filter(Term.id==arg).first()
        except:
            cate = web.ctx.orm.query(Term).filter(Term.type=='category').\
                                           filter(Term.slug==arg).first()
        if cate:
            posts = cate.posts
            return  admin_render.category_posts(posts=posts, page=page)
        else:
            raise web.notfound()

# show all categories
class categories(object):
    @login_required
    def GET(self):
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        categories = web.ctx.orm.query(Term).filter(Term.type=='category').all()
        msg = web.ctx.get('msg', '')
        return admin_render.categories(categories=categories, page=page, msg=msg)


# add a category
class addcategory(object):
    @login_required
    def POST(self):
        i = web.input()
        name = i.name.strip()
        slug = None
        if i.slug.strip():
            slug = i.slug.strip().replace(' ', '-')
        desc = i.desc.strip()
        # name should not be empty
        if not name:
            web.ctx.msg = "Category name can not be empty."
            raise web.seeother('/categories')
        count = web.ctx.orm.query(Term).filter(Term.type=='category').filter(Term.name==name).count()
        if count > 0:
            web.ctx.msg = "Category '%s' already exist!" % name
            raise web.seeother('/categories')
        # validates slug
        if slug:
            if not term_slug_validates(slug):
                web.ctx.msg = "Category not saved! slug is the same as another category."
                raise web.seeother('/categories')

        # add a new category 
        term = Term(name=name, slug=slug, description=desc, type='category')
        web.ctx.orm.add(term)
        web.ctx.msg = "Category '%s' has been saved!" % name
        web.ctx.orm.commit()
        raise web.seeother('/categories')
        
# edit a category
class editcategory(object):
    @login_required
    def GET(self, id):
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        try:
            id = int(id)
            cate = web.ctx.orm.query(Term).filter(Term.id==id).first()
        except:
            pass
        categories = web.ctx.orm.query(Term).filter(Term.type=='category').all()
        return admin_render.category(cate=cate, categories=categories, page=page)

    @login_required
    def POST(self, id):
        i = web.input()
        name = i.name.strip()                                    
        slug = None
        if i.slug.strip():                                              # should validate slug
            slug = i.slug.strip().replace(' ', '-')
        desc = i.desc.strip()
        if not name:                                            # name can't be empty
            web.ctx.msg = "Category name can not be empty"
            raise web.seeother("/category/edit/%s" % id)
        cate = web.ctx.orm.query(Term).filter(Term.type=='category').filter(Term.id==int(id)).first()
        # if the category get a new name
        if cate.name != name:
            count = web.ctx.orm.query(Term).filter(Term.type=='category').filter(Term.name==name).count()
            if count > 0:
                web.ctx.msg = "Category '%s' already exist, change a name!" % name
                raise web.seeother("/category/edit/%s" % id)
        # validates slug
        if slug:
            if not term_slug_validates(slug, int(id)):
                web.ctx.msg = "Category not modified! slug is the same as another category."
                raise web.seeother('/categories')
            
        cate.name = name
        cate.slug = slug
        cate.description = desc
        web.ctx.orm.commit()                           # update it
       # web.ctx.msg = "Category '%s' has been modified!" % name
        raise web.seeother('/categories')


# delete a category
class delcategory(object):
    @login_required
    def POST(self):
        i = web.input(checks=[])         # tells web.input that checks is a list, it stores the post id to delete
        if i.action == 'delete':
            for id in i.checks:  
                category = web.ctx.orm.query(Term).filter(Term.id==int(id)).first()
                web.ctx.orm.delete(category)
                web.ctx.orm.commit()
        raise web.seeother("/categories")
            


# list of all pages
class allpages(object):

    @login_required
    def GET(self):
        i = web.input()
        if i.get('status', ''):
            pages = web.ctx.orm.query(Post).filter(Post.content_type=='page').\
                    filter(Post.status==i.status).order_by("posts.created DESC")
        else:
            pages = web.ctx.orm.query(Post).filter(Post.content_type=='page').order_by("posts.created DESC")
        all_count = web.ctx.orm.query(Post).filter(Post.content_type=='page').count()
        publish_count = web.ctx.orm.query(Post).filter(Post.content_type=='page').\
                        filter(Post.status=='publish').count()
        return admin_render.pages(pages=pages, all_count=all_count, publish_count=publish_count)


# add a new page
class addpage(object):

    def get_admin(self):
        username = web.ctx.session.username
        return web.ctx.orm.query(User).filter(User.name==username).first()

    @login_required
    def GET(self):
        return admin_render.post(action='add', content_type='page')

    @login_required
    def POST(self):
        i = web.input()
        title = i.title
        content = i.content
        slug = None
        if i.slug.strip(): slug = i.slug.strip().replace(' ', '-')
        excerpt = i.excerpt
        try:
            menu_order = int(i.order)
        except:
            menu_order = 0
        comment_status = 0
        if i.get('comment_status', '') == 'open': comment_status = 1   # allow comment
        status = 'draft'
        if i.get('publish'):
            status = 'publish'                                          # post be  publish
        post = Post(title=title, content=content, slug=slug,
                    content_type='page', status=status,
                    excerpt=excerpt, menu_order=menu_order,
                    comment_status=comment_status)
        
        if not (title and content):
            msg = "Title and page content can not be empty."
            post.status = None                                          # post did not publish, so change this
            return admin_render.post(post=post, action='add',
                                     content_type='page', msg=msg)
        # validates post slug
        if slug:
            if not post_slug_validates(slug):
                msg = "Page not saved! Slug is the same as another post's, please change it."
                post.status = None                                                                  
                return admin_render.post(post=post, action="add",
                                         content_type="page", msg=msg)
        post.author = self.get_admin()
        web.ctx.orm.commit()
        if status == 'publish':
            web.ctx.msg = "The page '%s' has been published." % post.title
        else:
            web.ctx.msg = "The page '%s' has been saved." % post.title
        raise web.seeother('/pages')                                # redirect to post list page


class editpage(object):

    @login_required
    def GET(self, id):
        try:
            id = int(id)
        except:
            raise web.notfound()
        page = web.ctx.orm.query(Post).filter(Post.id==id).first()
        return admin_render.post(post=page, content_type='page', action='edit')

    @login_required
    def POST(self, id):
        i = web.input()
        title = i.title
        content = i.content
        slug = None
        if i.slug.strip(): slug = i.slug.strip().replace(' ', '-')
        excerpt = i.excerpt
        try:
            menu_order = int(i.order)
        except:
            menu_order = 0
        comment_status = 0
        if i.get('comment_status', '') == 'open': comment_status = 1   # allow comment
        status = i.status                                        
        if i.get('unpublish'): status = 'draft'                         # if cancel publish button been press
        if i.get('publish'): status = 'publish'
        post = web.ctx.orm.query(Post).filter(Post.id==int(id)).first()          # the old page object
        if not (title and content):
            msg = "Title and content can not be empty!"
            return admin_render.post(post=post, action='edit', content_type='page', msg=msg)
        # validates post slug
        if slug:
            if not post_slug_validates(slug, int(id)):
                msg = "Page modification not saved! Slug is the same as another post's, please change it."
                return admin_render.post(post=post, action="edit", content_type="page", msg=msg)
        post.title = title
        post.content = content
        post.slug = slug
        post.excerpt = excerpt
        post.menu_order = menu_order
        post.comment_status = comment_status
        post.status = status
        post.modified = datetime.now()
        web.ctx.orm.commit()
        raise web.seeother("/pages")


# delete blog page
class delpages(object):
    @login_required
    def POST(self):
        i = web.input(checks=[])
        checks = i.checks
        for id in checks:
            id = int(id)
            page = web.ctx.orm.query(Post).filter(Post.id==id).first()
            web.ctx.orm.delete(page)
            web.ctx.orm.commit()
        referer = web.ctx.env.get('HTTP_REFERER', '/pages')
        raise web.seeother(referer)


# all comments with status: 'waiting' or 'approved'
class allcomments(object):
    @login_required
    def GET(self):
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        comments = web.ctx.orm.query(Comment).filter(Comment.status != 'spam').\
                   order_by("comments.created DESC").all()
        comment_count = len(comments)
        if comment_count % ADMIN_COMMENT_PER_PAGE == 0:
            page_count = comment_count / ADMIN_COMMENT_PER_PAGE
        else:
            page_count = comment_count / ADMIN_COMMENT_PER_PAGE + 1
        spam_count = web.ctx.orm.query(Comment).filter(Comment.status=='spam').count()
        return admin_render.comments(comments=comments[(page-1)*ADMIN_COMMENT_PER_PAGE:page*ADMIN_COMMENT_PER_PAGE],
                                     comment_count=comment_count, spam_count=spam_count,
                                     page=page, page_count=page_count)

# all apam comments
class spamcomments(object):
    @login_required
    def GET(self):
        i = web.input(page=1)
        try:
            page = int(i.page)
        except:
            page = 1
        spam_comments = web.ctx.orm.query(Comment).filter(Comment.status=='spam').\
                        order_by("comments.created DESC").all()
        spam_count = len(spam_comments)
        if spam_count != 0 and spam_count % ADMIN_COMMENT_PER_PAGE == 0:
            page_count = spam_count / ADMIN_COMMENT_PER_PAGE
        else:
            page_count = spam_count / ADMIN_COMMENT_PER_PAGE + 1
        comment_count = web.ctx.orm.query(Comment).filter(Comment.status!='spam').count()
        return admin_render.comments(comments=spam_comments[(page-1)*ADMIN_COMMENT_PER_PAGE:page*ADMIN_COMMENT_PER_PAGE],
                                     comment_count=comment_count, spam_count=spam_count,
                                     page=page, page_count=page_count)
    

# mark a comment as 'spam' or 'approved'
class markcomment(object):
    @login_required
    def GET(self, id):
        i = web.input()
        try:
            id = int(id)
        except:
            raise web.notfound()
        comment = web.ctx.orm.query(Comment).filter(Comment.id==id).first()
        if not comment:
            raise web.notfound()
        comment.status = i.status
        web.ctx.orm.commit()
        raise web.seeother(web.ctx.env.get('HTTP_REFERER', '/comments'))


    
# delete a single comment
class delcomment(object):
    @login_required
    def GET(self, id):
        try:
            id = int(id)
        except:
            raise web.notfound()
        comment = web.ctx.orm.query(Comment).filter(Comment.id==id).first()
        if comment:
            comment.post.comment_count -= 1                     # comment count minus 1
            web.ctx.orm.delete(comment)
            web.ctx.orm.commit()
        referer = web.ctx.env.get('HTTP_REFERER', '/comments')
        
        # if comment is deleted on comment-edit page, should not stay on the edit page
        if "/admin/comment/edit/" in referer:               
            referer = '/comments'
        raise web.seeother(referer)

# bulk delete comment
class delcomments(object):
    @login_required
    def POST(self):
        i = web.input(checks=[])              # tells web.input that checks is a list
        for id in i.checks:
            comment = web.ctx.orm.query(Comment).filter(Comment.id==int(id)).first()
            if comment:
                comment.post.comment_count -= 1
                web.ctx.orm.delete(comment)
                web.ctx.orm.commit()
        referer = web.ctx.env.get('HTTP_REFERER', '/comments')
        raise web.seeother(referer)
        

# edit a comment
class editcomment(object):

    @login_required
    def GET(self, id):
        try:
            id = int(id)
        except:
            raise web.notfound()
        comment = web.ctx.orm.query(Comment).filter(Comment.id==id).first()
        return admin_render.comment_edit(comment=comment)

    @login_required
    def POST(self, id):
        i = web.input()
        referer = web.ctx.env.get('HTTP_REFERER', '/comments')
        comment = web.ctx.orm.query(Comment).filter(Comment.id==int(id)).first()
        # update the comment data and commit it
        if not (i.author and i.email and i.content):
            msg = "Author, email, content field can not be empty!"
            return admin_render.comment_edit(comment=comment, msg=msg)
        comment.author = i.author
        comment.email = i.email
        comment.url = i.url
        comment.content = i.content
        if i.comment_status == "approved": comment.status = i.comment_status
        elif i.comment_status == "spam": comment.status = i.comment_status
        else: comment.status = i.comment_status
        web.ctx.orm.commit()
        msg = "Comment has been updated successfully!"
        return admin_render.comment_edit(comment=comment, msg=msg)
            
        

# reply a comment
class replycomment(object):

    @login_required
    def POST(self):
        i = web.input()
        post_id = int(i.post_id)
        parent_id = int(i.parent_id)     # not implement yet
        comment = Comment(
            post_id=post_id,
            author=web.ctx.session.username,
            email=web.ctx.session.email,
            content=i.comment,
            status='approved'
        )
        web.ctx.orm.add(comment)
        web.ctx.orm.commit()
        comment.post.comment_count += 1
        web.ctx.orm.commit()
        referer = web.ctx.env.get('HTTP_REFERER', '/comments')
        raise web.seeother(referer)


class links(object):
    @login_required
    def GET(self):
        i = web.input(page=1)
        page = i.page
        links = web.ctx.orm.query(Link).all()
        return admin_render.links(links=links, page=page)

class addlink(object):
    @login_required
    def POST(self):
        i = web.input()
        name = i.name.strip()
        href = i.href.strip()
        desc = i.desc.strip()
        # if name or href empty, don't add it
        if not (name and href):
            raise web.seeother(web.ctx.env.get('HTTP_REFERER', '/links'))
        if not href.startswith('http://'):
            href = "http://%s" % href
        link = Link(name=name, url=href, description=desc)
        web.ctx.orm.add(link)
        web.ctx.orm.commit()
        raise web.seeother("/links")
        
class editlink(object):
    @login_required
    def GET(self, id):
        try:
            id = int(id)
        except:
            raise web.notfound()
        links = web.ctx.orm.query(Link).all()
        link = web.ctx.orm.query(Link).get(id)
        return admin_render.link(link=link, links=links)

    @login_required
    def POST(self, id):
        i = web.input()
        id = int(id)
        name = i.name.strip()
        href = i.href.strip()
        desc = i.desc.strip()
        if not (name and href):
            raise web.seeother("/links")
        if not href.startswith('http://'):
            href = "http://%s" % href
        web.ctx.orm.query(Link).filter(Link.id==id).\
                                update({'name': name, 'url': href, 'description': desc})
        raise web.seeother("/links")

# delete a link or more                            
class dellinks(object):
    @login_required
    def POST(self):
        i = web.input(checks=[])
        checks = i.checks
        action = i.get('action', '')
        if checks and action == 'delete':
            for id in checks:
                link = web.ctx.orm.query(Link).get(int(id))
                web.ctx.orm.delete(link)
                web.ctx.orm.commit()
        raise web.seeother(web.ctx.env.get('HTTP_REFERER', '/links'))
    

# general settings
class settings(object):
    # get blog's general settings
    def get_settings(self):
        option_title = web.ctx.orm.query(Option).filter(Option.name=='blog_title').first()
        if not option_title:
            option_title = Option(name='blog_title')
            web.ctx.orm.add(option_title)
        option_subtitle = web.ctx.orm.query(Option).filter(Option.name=='blog_subtitle').first()
        if not option_subtitle:
            option_subtitle = Option(name='blog_subtitle')
            web.ctx.orm.add(option_subtitle)
        option_notice = web.ctx.orm.query(Option).filter(Option.name=='blog_notice').first()
        if not option_notice:
            option_notice = Option(name='blog_notice')
            web.ctx.orm.add(option_notice)
        option_keywords = web.ctx.orm.query(Option).filter(Option.name=='blog_keywords').first()
        if not option_keywords:
            option_keywords = Option(name='blog_keywords')
            web.ctx.orm.add(option_keywords)
        option_desc = web.ctx.orm.query(Option).filter(Option.name=='blog_description').first()
        if not option_desc:
            option_desc = Option(name='blog_description')
            web.ctx.orm.add(option_desc)
        option_email = web.ctx.orm.query(Option).filter(Option.name=='blog_admin_email').first()
        if not option_email:
            option_email = Option(name='blog_admin_email')
            web.ctx.orm.add(option_email)
        option_domain = web.ctx.orm.query(Option).filter(Option.name=='blog_domain').first()
        if not option_domain:
            option_domain = Option(name='blog_domain')
            web.ctx.orm.add(option_domain)
        web.ctx.orm.commit()
        return {'title': option_title, 'subtitle': option_subtitle, 'notice': option_notice,
                'keywords': option_keywords, 'description': option_desc,
                'email': option_email, 'domain': option_domain}
        
    @login_required
    def GET(self):
        f = settings_form()
        settings = self.get_settings()
        f.title.value = settings['title'].value
        f.subtitle.value = settings['subtitle'].value
        f.notice.value = settings['notice'].value
        f.keywords.value = settings['keywords'].value
        f.description.value = settings['description'].value
        f.email.value = settings['email'].value
        f.domain.value = settings['domain'].value
        return admin_render.settings(form=f)

    @login_required
    def POST(self):
        f = settings_form()
        if not f.validates():
            msg = "settings not saved!"
            return admin_render.settings(form=f, msg=msg)
        else:
            web.ctx.orm.query(Option).filter(Option.name=='blog_title').update({'value': f.title.value})
            web.ctx.orm.query(Option).filter(Option.name=='blog_subtitle').update({'value': f.subtitle.value})
            web.ctx.orm.query(Option).filter(Option.name=='blog_notice').update({'value': f.notice.value})
            web.ctx.orm.query(Option).filter(Option.name=='blog_keywords').update({'value': f.keywords.value})
            web.ctx.orm.query(Option).filter(Option.name=='blog_description').update({'value': f.description.value})
            web.ctx.orm.query(Option).filter(Option.name=='blog_admin_email').update({'value': f.email.value})
            web.ctx.orm.query(Option).filter(Option.name=='blog_domain').update({'value': f.domain.value})
            msg = "settings has been saved!"
            return admin_render.settings(form=f, msg=msg)
         
class comment_setting(object):
    """ comment setting stuff """
    def get_comment_setting(self):
        avatar = web.ctx.orm.query(Option).filter(Option.name=='comment_avatar').first()
        if not avatar:
            avatar = Option(name='comment_avatar')
            web.ctx.orm.add(avatar)
        akismet_enable = web.ctx.orm.query(Option).filter(Option.name=='comment_akismet_enable').first()
        if not akismet_enable:
            akismet_enable = Option(name='comment_akismet_enable')
            web.ctx.orm.add(akismet_enable)
        akismet_key = web.ctx.orm.query(Option).filter(Option.name=='comment_akismet_key').first()
        if not akismet_key:
            akismet_key = Option(name='comment_akismet_key')
            web.ctx.orm.add(akismet_key)
        return {'avatar': avatar, 'akismet_enable': akismet_enable, 'akismet_key': akismet_key}
        
    @login_required
    def GET(self):
        # something should be add here later
        setting = self.get_comment_setting()
        return admin_render.comment_setting(avatar=setting['avatar'].value,
                                            akismet_enable=setting['akismet_enable'].value,
                                            akismet_key=setting['akismet_key'].value)

    @login_required
    def POST(self):
        i = web.input()
        akismet_enable = i.get('akismet_enable', '')
        akismet_key = i.get('akismet_key', '')
        avatar = i.get('avatar', '')
        if akismet_enable:
            if not akismet_key:
                msg = "Changes not saved! If you enable akismet, you should input a key!"
                return admin_render.comment_setting(avatar=avatar, akismet_enable=akismet_enable,
                                                    akismet_key=akismet_key, msg=msg)
                
        web.ctx.orm.query(Option).filter(Option.name=='comment_akismet_enable').\
                                  update({'value': akismet_enable})
        web.ctx.orm.query(Option).filter(Option.name=='comment_akismet_key').\
                                  update({'value': akismet_key})
        web.ctx.orm.query(Option).filter(Option.name=='comment_avatar').\
                                  update({'value': avatar})
        msg = "Changes has been saved!"
        return admin_render.comment_setting(avatar=avatar, akismet_enable=akismet_enable,
                                            akismet_key=akismet_key, msg=msg)

# user list
class allusers(object):
    @login_required
    def GET(self):
        users = web.ctx.orm.query(User).all()
        post = web.ctx.orm.query(Post).first()
        return admin_render.users(users=users, post=post)

# config user information
class profile(object):
    @login_required
    def GET(self):
        i = web.input()
        uid = i.get('uid', '')
        if uid:
            user = web.ctx.orm.query(User).get(int(uid))
        else:
            user = web.ctx.orm.query(User).filter(User.id==web.ctx.session.uid).first()
        if not user: raise web.notfound()
        return admin_render.profile(user=user)

    @login_required
    def POST(self):
        i = web.input()
        uid = int(i.uid)
        user = web.ctx.orm.query(User).get(uid)
        email = i.email.strip()
        url = i.url.strip()
        pw1 = i.get('pw1', '')
        pw2 = i.get('pw2', '')
        if not email:
            msg = "Email is required!"
            return admin_render.profile(user=user, msg=msg)
        if pw1:
            if pw2:
                if pw1 != pw2:
                    msg = "Password is not the same."
                    return admin_render.profile(user=user, msg=msg)
                else:
                    user.password = hashlib.md5(pw1).hexdigest()
            else:
                msg = "You must confirm your password!"
                return admin_render.profile(user=user, msg=msg)
        user.email = email
        user.url = url
        web.ctx.orm.commit()
        msg = "Changes has been saved!"
        return admin_render.profile(user=user, msg=msg)


    
