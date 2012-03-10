# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.utils import Address, Hook


class Solr(Buildout):

    listen_port = '11983'

    def setup_hooks(self):
        super(Solr, self).setup_hooks()
        self.hooks['solr:server'] = Hook()
        self.hooks['solr:supervisor'] = Hook()

    def configure(self):
        super(Solr, self).configure()
        self.config_attr('listen_port')
        self.address = Address(self.host.fqdn, self.listen_port)
        self.hooks['solr:server'].address = self.address
        self.hooks['solr:supervisor'].program = self.expand(
            '10 solr (startsecs=10) java [-jar start.jar] ${component.compdir}/parts/instance true')
