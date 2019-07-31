# -*- coding: utf-8 -*-
import httplib2

class URLHelper(object):
    def check_url(self, url):
        try:
            h = httplib2.Http()
            resp = h.request(url, 'HEAD')
            if int(resp[0]['status']) > 399:
                return False
        except Exception as e:
            print e
            return False
        return True

