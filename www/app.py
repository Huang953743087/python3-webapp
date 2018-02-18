#!/usr/bin/env python3
#-*-coding:utf-8-*-

import logging; logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

def index(request):
    return web.Response(body=b'<h1>Awesome</h1>',headers={'content-type':'text/html'})

@asyncio.coroutine
def init(loop):
    app=web.Application(loop=loop)
    app.router.add_route('GET','/',index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
#创建连接池，连接池由全局变量__pool存储，缺省情况下将编码设置为utf8，自动提交事务
@asyncio.coroutine
def create_pool(loop,**kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = yield  from aiomysql(
        host=kw.get('host','localhost'),
        port=kw.get('port',3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf8'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop

        )
#SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。
@asyncio.coroutine
def select(sql,args,size=None):
    log(sql,args)
    global __pool
    with(yield from __pool) as conn:
        cur=yield from conn.cursor(aiomysql.DictCursor)
        #用于替换？与%
        yield from cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs=yield from curfetchmany(size)
        else:
            rs=yield from cur.fetchall()
        yield from cur.close()
        logging.info('rows returned:%s'%len(rs))
        return rs
'''
要执行INSERT、UPDATE、DELETE语句，可以定义一个通用的execute()函数，
因为这3种SQL的执行都需要相同的参数，以及返回一个整数表示影响的行数：'''
@asyncio.coroutine
def excute(sql,args):
    log(sql)
    with(yield from __pool) as conn:
        try:
            cur=yield from conn.cursor()
            yield from cur.execute(sql.replace('?','%s'),args)
            affected=cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return  affected

loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()