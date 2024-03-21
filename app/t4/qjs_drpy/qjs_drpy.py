#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File  : qjs_drpy.py
# Author: DaShenHan&道长-----先苦后甜，任凭晚风拂柳颜------
# Date  : 2024/3/20

import os
import threading

import quickjs
import ujson
from quickjs import Context
from utils.quickjs_ctx import initContext
from utils.tools import get_md5
from t4.test.ad_remove import fixAdM3u8
from concurrent.futures import ThreadPoolExecutor, wait


class Drpy:
    def __init__(self, api='drpy', t4_js_api='', debug=0):
        """
        初始化一个drpy类
        @param api: 可以传api如996影视.js
        @param t4_js_api: 本地代理url
        @param debug: 开启调试模式|默认关闭，开启后可以显示源里打印的日志
        """
        base_path = os.path.dirname(__file__)
        key = '_' + get_md5(api)

        def _(p):
            return os.path.join(base_path, p)

        with open(_('qjs_module_muban.js'), encoding='utf-8') as f:
            self._qjs_module_muban = f.read()
        with open(_('qjs_module_cheerio.js'), encoding='utf-8') as f:
            self._qjs_module_cheerio = f.read()
        with open(_('qjs_module_gbk.js'), encoding='utf-8') as f:
            self._qjs_module_gbk = f.read()
        with open(_('qjs_module_crypto.js'), encoding='utf-8') as f:
            self._qjs_module_crypto = f.read()
        with open(_('qjs_module_drpy2.js'), encoding='utf-8') as f:
            self._qjs_module_drpy2 = f.read() + f'\nglobalThis.{key} = ' + '{ init, home, homeVod, category, detail, ' \
                                                                           'play, search, proxy, sniffer, isVideo};'

        self.executor = ThreadPoolExecutor(max_workers=1)
        self._lock = threading.Lock()

        future = self.executor.submit(self.initCtx, debug)
        wait([future])
        self.ctx = future.result()

        self._api = api
        self.key = key
        self.t4_js_api = t4_js_api

    def initCtx(self, debug) -> Context:
        ctx = Context()
        initContext(ctx, url='', prefix_code='true', env={'debug': debug}, getParams=lambda: {},
                    getCryptoJS=lambda: 'true')
        ctx.module(self._qjs_module_muban)
        ctx.module(self._qjs_module_cheerio)
        ctx.module(self._qjs_module_gbk)
        ctx.module(self._qjs_module_crypto)
        ctx.module(self._qjs_module_drpy2)
        return ctx

    def setDebug(self, debug):
        with self._lock:
            future = self.executor.submit(self.ctx.set, '_debug', debug)
            wait([future])
            return future.result()

    def getName(self):
        return self._api.split('/')[-1]

    def toJsObJect(self, any):
        if isinstance(any, dict) or isinstance(any, list):
            with self._lock:
                future = self.executor.submit(self.ctx.parse_json, ujson.dumps(any, ensure_ascii=False))
                wait([future])
                return future.result()
        return any

    @staticmethod
    def toDict(_object):
        return ujson.loads(_object.json())

    @staticmethod
    def setDict(_str):
        return ujson.loads(_str)

    def call(self, func: str, *args):
        with self._lock:
            future = self.executor.submit(self._call, func, *args)
            wait([future])
            return future.result()

    def _call(self, func: str, *args):
        return self.ctx.eval(f'globalThis.{self.key}.{func}')(*args)

    def init(self, extend=""):
        extend = self.toJsObJect(extend)
        self.call('init', extend)

    def homeContent(self, filter=None):
        filter = self.toJsObJect(filter)
        return self.setDict(self.call('home', filter))

    def homeVideoContent(self):
        return self.setDict(self.call('homeVod'))

    def categoryContent(self, tid, pg, filter, extend):
        filter = self.toJsObJect(filter)
        extend = self.toJsObJect(extend)
        return self.setDict(self.call('category', tid, pg, filter, extend))

    def detailContent(self, ids):
        if isinstance(ids, list):
            ids = ids[0]
        ids = self.toJsObJect(ids)
        return self.setDict(self.call('detail', ids))

    def searchContent(self, key, quick, pg=1):
        return self.setDict(self.call('search', key, quick, pg))

    def playerContent(self, flag, id, vipFlags=None):
        if vipFlags is None:
            vipFlags = []
        vipFlags = self.toJsObJect(vipFlags)
        return self.setDict(self.call('play', flag, id, vipFlags))

    def isVideo(self):
        """
        返回是否为视频的匹配字符串
        @return: None空 reg:正则表达式  js:input js代码
        """
        # return 'js:input.includes(".m3u8)?true:false'

    @staticmethod
    def adRemove():
        """
        m3u8广告移除函数。将自动执行返回的字符串的本地代理功能
        @return: None空 reg:正则表达式  js:input js代码
        """
        # return 'reg:/video/adjump.*?ts'

    def getProxyUrl(self):
        """
        获取本地代理地址
        @return:
        """
        return self.t4_js_api

    @staticmethod
    def fixAdM3u8(*args):
        return fixAdM3u8(*args)

    def localProxy(self, params):
        params = self.toJsObJect(params)
        return self.toDict(self.call('proxy', params))


if __name__ == '__main__':
    drpy = Drpy(debug=1)
    drpy.init('https://ghproxy.liuzhicong.com/https://github.com/hjdhnx/dr_py/raw/main/js/555影视[飞].js')
    # drpy.init('https://ghproxy.liuzhicong.com/https://github.com/hjdhnx/dr_py/raw/main/js/农民影视.js')
    # drpy.init('https://ghproxy.liuzhicong.com/https://github.com/hjdhnx/dr_py/raw/main/js/奇珍异兽.js')
    drpy.setDebug(0)
    print(drpy.homeContent())
    f = quickjs.Function(
        "adder", """
                function adder(x, y) {
                    return x + y;
                }
                """)

    # print(drpy.categoryContent(3, 1, False, {}))
    # print(drpy.detailContent("3$/detail/790.html"))
    # print(drpy.playerContent("索尼", "https://www.cs1369.com/play/790-1-1.html", []))
    # print(drpy.searchContent("斗罗大陆", False, 1))