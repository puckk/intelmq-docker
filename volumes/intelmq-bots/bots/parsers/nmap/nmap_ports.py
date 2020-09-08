# -*- coding: utf-8 -*-
import re

from intelmq.lib import utils
from intelmq.lib.bot import ParserBot

class NmapPortsParserBot(ParserBot):

    def parse_line(self, val, report):
        l = val.split("Ports:")
        if len(l) > 1:
            host = l[0].split()[1]
            ports = l[1].split(', ')
            for p in ports:
                p_data = p.split('/')
                port = p_data[0].strip()
                state = p_data[1].strip()
                protocol = p_data[2].strip()
                self.logger.info("{} {} {} {}".format(host, protocol, port, state))

                event = self.new_event(report)

                event.add('extra.ip', host)
                event.add('extra.protocol_transport', protocol)
                event.add('extra.port', port)
                event.add('extra.state', state)

                event.add('raw', self.recover_line(val))

                yield event

BOT = NmapPortsParserBot