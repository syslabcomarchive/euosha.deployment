# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.utils import Address, Hook


class ZEO(Buildout):

    listen_port = '9000'

    def setup_hooks(self):
        super(ZEO, self).setup_hooks()
        self.hooks['zeo:server'] = Hook()
        self.hooks['zeo:supervisor'] = Hook()

    def configure(self):
        super(ZEO, self).configure()
        self.config_attr('listen_port')
        self.address = Address(self.host.fqdn, self.listen_port)
        self.hooks['zeo:server'].address = self.address
        self.hooks['zeo:supervisor'].program = self.expand(
            '10 zeo (startsecs=10) ${component.compdir}/bin/runzeo '
            '[-C ${component.compdir}/parts/zeo/zeo.conf] true')
