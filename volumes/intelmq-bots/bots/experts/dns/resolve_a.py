# -*- coding: utf-8 -*-

from datetime import datetime

# import dns.exception
# import dns.resolver
# import dns.reversename
import dns.resolver

from intelmq.lib.bot import Bot
from intelmq.lib.cache import Cache
from intelmq.lib.harmonization import IPAddress

MINIMUM_BGP_PREFIX_IPV4 = 24
MINIMUM_BGP_PREFIX_IPV6 = 128
DNS_EXCEPTION_VALUE = "__dns-exception"


class InvalidPTRResult(ValueError):
    pass


class DnsResolveAExpertBot(Bot):

    def init(self):
        self.overwrite = getattr(self.parameters, 'overwrite', True)

    def process(self):
        original_event = self.receive_message()

        keys = ["extra.%s"]

        for key in keys:
            domain_key = key % "fqdn"

            if domain_key not in original_event:
                self.logger.info('event without key')
                continue

            domain = original_event.get(domain_key)
            
            try:
                self.logger.info('Quering: {}'.format(domain))
                res = dns.resolver.resolve(domain, 'A', raise_on_no_answer=False)
                self.logger.info('Res: {}'.format(res))

                for answer in res.response.answer:
                    query = answer.name.to_text()
                    for real_answer in answer.items.keys():
                        typ = real_answer.rdtype.name
                        res = real_answer.to_text()
                    
                        event = self.new_event(original_event.to_dict())
                        event.add('extra.dns_type', str(typ), overwrite=True)
                        event.add('extra.dns_domain', str(query), overwrite=True)
                        event.add('extra.dns_res', str(res), overwrite=True)

                        self.send_message(event)

            except dns.resolver.NXDOMAIN as e:
                self.logger.warning(
                    'cannot find {} Exception: {}'.format(domain, e))
            except Exception as e:
                self.logger.error(
                    'cannot process domain {} Exception: {}'.format(domain, e))
        
        self.acknowledge_message()



BOT = DnsResolveAExpertBot