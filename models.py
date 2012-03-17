#!/usr/bin/env python
#-*-coding:utf-8-*-
import web
import hashlib
from datetime import datetime


from sqlalchemy import create_engine, Table, ForeignKey
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy import and_, or_
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base


#engine = create_engine('mysql://root:123456@localhost/aplog2?charset=utf8', echo=True)
engine = create_engine('sqlite:///mydatabase.db', echo=True)
Base = declarative_base()              # every Mapping class should inherit from this


# for the many-to-many relationships between Post and Term
term_relationships = Table('term_relationships', Base.metadata,
                 Column('post_id', Integer, ForeignKey('posts.id')),
                 Column('term_id', Integer, ForeignKey('terms.id'))
        )


class Post(Base):
    """ can be a post or a page """
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(64), nullable=False)
    slug = Column(String(64), unique=True)
    excerpt = Column(Text)
    content = Column(Text, nullable=False)
    content_type = Column(String(10), default='post')            # 'post' or 'page'
    created = Column(DateTime, default=datetime.now)
    modified = Column(DateTime, default=datetime.now)
    status = Column(String(10), default='publish')               # 'publish' or 'draft'
    comment_status = Column(Integer, default=1)                  # allow: 1, not-allow: 0
    comment_count = Column(Integer, default=0)                   # how many comments?
    view_count = Column(Integer, default=0)                      # how many people view this post
    menu_order = Column(Integer, default=0)
    link = Column(String(255), unique=True)

    # many to one: Post <-> User
    author = relationship('User', backref=backref('posts', order_by=created))
    
    # many to many: Post <-> Term
    terms = relationship('Term', secondary=term_relationships, backref=backref('posts', order_by=created))


    def __repr__(self):
        return "<Post (%s)>" % str(self.id)

    # absolute url for post, without domain name
    def get_absolute_url(self):
        if self.slug:
            if self.content_type == 'post': return "/archive/%s" % self.slug
            else: return "/page/%s" % self.slug
        else:
            if self.content_type == 'post': return "/archive/%d" % self.id
            else: return "/page/%d" % self.id
            
    def shortcontent(self, length=300):
        return self.content[:length]

    # get next post
    def get_next(self):
        posts = web.ctx.orm.query(Post).filter(Post.content_type=='post').filter(Post.status=='publish').\
                                       filter("created>:time").params(time=self.created).order_by('created').all()
        if len(posts) > 0: return posts[0]
        else: return None

    # get previous one
    def get_prev(self):
        posts = web.ctx.orm.query(Post).filter(and_(Post.content_type=='post', Post.status=='publish')).\
                                       filter("created<:time").params(time=self.created).order_by('created').all()
        if len(posts) > 0: return posts[-1]
        else: return None


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    email = Column(String(50), nullable=False)
    url = Column(String(50))

    def __repr__(self):
        return "<User ('%s')>" % self.name

    
class Term(Base):
    """ category or tag """
    __tablename__ = 'terms'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    slug = Column(String(64), unique=True, nullable=True)
    description = Column(String(200))
    type = Column(String(10), default='tag')            # 'category' or 'tag'
    count = Column(Integer, default=0)
    order = Column(Integer, default=0)

    def __repr__(self):
        return "<Term ('%s')>" % str(self.id)

    def get_absolute_url(self):
        if self.slug:
            return "/%s/%s" % (self.type, self.slug)
        else:
            return "/%s/%d" % (self.type, self.id)


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    author = Column(String(64), nullable=False)
    email = Column(String(64), nullable=False)
    url = Column(String(255))
    ip = Column(String(40))
    created = Column(DateTime, default=datetime.now)
    content = Column(Text)
    status = Column(String(10), default='approved')         # 'approved' or 'spam' or 'waiting'
    #parent_id = Column(Integer, ForeignKey('comments.id'))

    # many-to-one: Comment <-> Post
    post = relationship('Post', backref=backref('comments', order_by=created))

    # many-to-one: Comment <-> Comment
   # parent = relationship('Comment', backref=backref('children', order_by=created))

    def __repr__(self):
        return "<Comment ('%s')>" % str(self.id)

    # get absolute url for every comment
    def get_absolute_url(self):
        return self.post.get_absolute_url() + ("#comment-%d" % self.id)

        
    
class Option(Base):
    """ options for this blog """
    __tablename__ = 'options'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    value = Column(Text)
    autoload = Column(String(10), default='yes')         # 'yes' or 'not'

    def __repr__(self):
        return "<Option (%s)>" % self.name


class Link(Base):
    """ the blogroll """

    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    url = Column(String(200))
    description = Column(String(200))

    def __repr__(self):
        return "<Link ('%s')>" % str(self.id)

# use to init blog data
def init_data():
    Session = sessionmaker(bind=engine)
    session = Session()
    cate = Term(name='Uncategory', slug='uncategory', type='category')
    session.add(cate)
    pw = hashlib.md5(u'123456').hexdigest()
    user = User(name='admin', password=pw, email='admin@example.com')
    session.add(cate)
    post = Post(title='Hello', content='Hello, world!', author=user)
    post.terms.append(cate)
    session.add(post)
    session.commit()
    session.close()
    
if __name__ == '__main__':
    # create all the tables
    Base.metadata.create_all(engine)
    init_data()
    
    