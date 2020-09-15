# -*- coding: utf-8 -*-
"""
Generator Bot

Parameters:
"""

from faker import Faker
import time

import intelmq.lib.exceptions as exceptions
from intelmq.lib.bot import CollectorBot


class DomainGeneratorCollectorBot(CollectorBot):

    def init(self):
        self.logger.info("Init Generator.")
        # self.base_domains = self.parameters.domains
        self.iteration_time = getattr(self.parameters, 'iteration_time', 1)
        self.stop_time = getattr(self.parameters, 'stop_time', 86400)
        self.count = getattr(self.parameters, 'count', 1000)
        self.faker = Faker()
        
    def process(self):
        self.logger.info("Starting Generator Process.")
        
        for _ in range(self.count):
            data = self.faker.domain_name()
            self.logger.info("Sending data: {}".format(data))

            report = self.new_report()
            report.add("extra.fqdn", data)
            report.add("raw", data)
            self.send_message(report)
            time.sleep(self.iteration_time)
        
        time.sleep(self.stop_time)


BOT = DomainGeneratorCollectorBot