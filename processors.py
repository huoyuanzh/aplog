#!/usr/bin/env python
#-*- coding:utf-8

import web
from sqlalchemy.orm import scoped_session, sessionmaker
from models import engine

# a load hook to use sqlalchemy
def load_sqla(handler):
    web.ctx.orm = scoped_session(sessionmaker(bind=engine))       # create the Session object of sqlalchemy
    try:
        return handler()
    except web.HTTPError:
        web.ctx.orm.commit()
        raise
    except:
        web.ctx.orm.rollback()
        raise
    finally:
        web.ctx.orm.commit()
        # if the above alone doesn't work, uncomment the following line:
        # web.ctx.orm.expunge_all()
        web.ctx.orm.close()
        