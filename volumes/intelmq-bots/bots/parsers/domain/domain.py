# -*- coding: utf-8 -*-
import re

from intelmq.lib import utils
from intelmq.lib.bot import ParserBot

class DomainParserBot(ParserBot):

    def parse_line(self, val, report):
        event = self.new_event(report)
        event.add('extra.domain', val.strip())
        yield event

BOT = DomainParserBot