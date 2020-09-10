# -*- coding: utf-8 -*-
import re

from intelmq.lib import utils
from intelmq.lib.bot import ParserBot
import requests
from intelmq.lib.exceptions import MissingDependencyError
from bs4 import BeautifulSoup
import magic
from urllib import parse

class HttpFetcherBot(ParserBot):
    def init(self):
        if requests is None:
            raise MissingDependencyError("requests")
        self.set_request_parameters()
        self.magic = magic.Magic(mime=True)

    def set_request_parameters(self):
        self.http_header = getattr(self.parameters, 'http_header', {})
        self.http_verify_cert = getattr(self.parameters, 'http_verify_cert', True)
        self.ssl_client_cert = getattr(self.parameters, 'ssl_client_certificate', None)
        self.kwargs = {}
        if (hasattr(self.parameters, 'http_username') and
                hasattr(self.parameters, 'http_password') and
                self.parameters.http_username):
            self.auth = (self.parameters.http_username,
                         self.parameters.http_password)
            self.kwargs["auth"] = self.auth
        else:
            self.auth = None

        if self.parameters.http_proxy and self.parameters.https_proxy:
            self.proxy = {'http': self.parameters.http_proxy,
                          'https': self.parameters.https_proxy}
            self.kwargs["proxies"] = self.proxy
        elif self.parameters.http_proxy or self.parameters.https_proxy:
            self.logger.warning('Only %s_proxy seems to be set.'
                                'Both http and https proxies must be set.',
                                'http' if self.parameters.http_proxy else 'https')
            self.proxy = {}
        else:
            self.proxy = {}

        self.http_timeout_sec = getattr(self.parameters, 'http_timeout_sec', None)
        self.kwargs["timeout"] = self.http_timeout_sec
        self.http_timeout_max_tries = getattr(self.parameters, 'http_timeout_max_tries', 1)
        # Be sure this is always at least 1
        self.http_timeout_max_tries = self.http_timeout_max_tries if self.http_timeout_max_tries >= 1 else 1

        self.http_header['User-agent'] = self.parameters.http_user_agent


    def parse_line(self, val, report):
        self.logger.info("{}".format(str(val)))
        event = self.new_event(report)
        url = val

        r = requests.get(url, headers=self.http_header, **self.kwargs)
        bs = BeautifulSoup(r.text, "html.parser")
        try:
            title = bs.find("title").text
        except:
            title = ""

        if not r.headers["Content-Type"]:
            content_type = self.magic.from_buffer(r.content)
        else:
            content_type = r.headers["Content-Type"]

        original_links = [tag_a["href"] for tag_a in bs.find_all("a", href=True)]
        # Sacar almohadillas
        links = [link for link in original_links if not link.startswith("#")]
        #Parse url absolute/relative
        links = [parse.urljoin(r.url, l) for l in links]
        links = list(set(links))
        links = [ parse.urlparse(link) for link in links ]

        links_fragments = [link for link in original_links if not link.startswith("#")]

        event.add('extra.response_code', r.status_code)
        event.add('extra.cookies', r.cookies.get_dict())
        event.add('extra.headers', dict(r.headers))
        event.add('extra.encoding', r.encoding)
        event.add('extra.content', r.content.decode("ISO-8859-1"))
        event.add('extra.url', r.url)
        event.add('extra.response_time', r.elapsed.microseconds)
        event.add("extra.title", title)
        event.add("extra.content_type", content_type)
        event.add("extra.links", links)



        yield event

BOT = HttpFetcherBot