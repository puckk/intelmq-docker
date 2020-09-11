# -*- coding: utf-8 -*-
"""
Generator Bot

Parameters:
"""

from faker import Faker
import time
import ipaddress
import random

import intelmq.lib.exceptions as exceptions
from intelmq.lib.bot import CollectorBot


class NmapPortsGeneratorCollectorBot(CollectorBot):

    def init(self):
        self.logger.info("Init Generator.")
        # self.base_domains = self.parameters.domains
        self.network = ipaddress.ip_network(self.parameters.network)
        self.chance_open = getattr(self.parameters, 'chance_open', 0.2)
        self.ports = []
        for prange in self.parameters.ports.split(','):
            pr = prange.split('-')
            if len(pr) == 1:
                self.ports.append(pr[0])
            elif len(pr) == 2:
                self.ports.append(range(pr[0], pr[1]))
                
        self.iteration_time = getattr(self.parameters, 'iteration_time', 1)
        self.stop_time = getattr(self.parameters, 'stop_time', 86400)
        self.count = getattr(self.parameters, 'count', 1000)
        self.faker = Faker()
        
    def process(self):
        self.logger.info("Starting Generator Process.")
        proto = 'tcp'
        it = 0
        while True:
            for ip in self.network:
                port_states = []
                for port in self.ports:
                    state = 'open' if random.random() < self.chance_open else 'closed'
                    port_states.append("{}/{}/{}//unknown///".format(port, state, proto))

                ports_str = ', '.join(port_states)
                data = 'Host: {} ()	Ports: {}'.format(ip, ports_str)
                self.logger.info("Sending data: {}".format(data))

                report = self.new_report()
                report.add("raw", data)
                self.send_message(report)
                it += 1
                if (it >=self.count):
                    return
                time.sleep(self.iteration_time)
        
        time.sleep(self.stop_time)


BOT = NmapPortsGeneratorCollectorBot