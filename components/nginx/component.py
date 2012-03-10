# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.utils import Address, Hook


class Nginx(Component):

    snippets = []

    def setup_hooks(self):
        super(Nginx, self).setup_hooks()
        self.hooks['%s:http' % self.name] = Hook()

    def configure(self):
        self.config_attr('server_name')
        self.address = Address(self.server_name+':80')
        self.hooks['%s:http' % self.name].address = self.address

    @step(1)
    def generate_config(self):
        for snippet in self.snippets:
            self.template('config/%s.conf' % snippet,
                          target='/etc/nginx/local/%s.conf' % snippet)

    @step(2)
    def reload(self):
        self.cmd('sudo /etc/init.d/nginx reload')


class PortalFrontend(Nginx):

    snippets = ['euosha']

    def configure(self):
        super(PortalFrontend, self).configure()
        haproxy = self.find_hooks('haproxy:frontend').next()
        self.haproxy = haproxy


class ServicesFrontend(Nginx):

    snippets = ['services']

    def configure(self):
        super(ServicesFrontend, self).configure()
        haproxy = self.find_hooks('haproxy:frontend').next()
        self.upstream_services = haproxy
