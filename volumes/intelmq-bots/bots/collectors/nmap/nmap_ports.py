# -*- coding: utf-8 -*-
"""
Nmap Collector Bot

TODO: INSTALL NMAP!!

Parameters:
    network: string

    ports: string

    nmap_params: string
"""

import subprocess
import ipaddress

import intelmq.lib.exceptions as exceptions
from intelmq.lib.bot import CollectorBot


class NmapPortsCollectorBot(CollectorBot):

    def init(self):
        self.logger.info("Init Nmap Process.")
        self.network = ipaddress.ip_network(self.parameters.network).with_prefixlen
        self.ports = self.parameters.ports
        self.fast_first = getattr(self.parameters, 'fast_first', True)
        self.nmap_params = getattr(self.parameters, 'nmap_params', '-n -T4 -Pn --max-rtt-timeout 200ms --initial-rtt-timeout 100ms --min-hostgroup 512 -oG -')
        
    def scan(self, network, ports, nmap_params):
        self.logger.info("Starting Nmap Process.")
        
        nmap_command = ["nmap", network]
        if ports:
            nmap_command.extend(["-p", ports])

        nmap_command.extend(nmap_params.split(' '))
        self.logger.info(' '.join(nmap_command))

        with subprocess.Popen(nmap_command,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE) as p:
            try:
                for line in p.stdout:
                    report = self.new_report()
                    report.add("raw", line)
                    self.send_message(report)
            finally:
                p.kill()
                p.wait()

    def process(self):
        if self.fast_first:
            self.logger.info("Starting Fast scan.")
            self.scan(self.network, None, self.nmap_params)
            self.logger.info("Finished Fast scan.")
        
        self.logger.info("Starting user defined scan.")
        self.scan(self.network, self.ports, self.nmap_params)
        self.logger.info("Starting all scans.")



BOT = NmapPortsCollectorBot