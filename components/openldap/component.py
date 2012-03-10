# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

"""Configure OpenLDAP server."""

from __future__ import print_function, unicode_literals


class OpenLDAP(Component):

    etcdir = '/etc/openldap'
    restart = 'true'

    # note that the port number is currently not reflected in the generated
    # configuration file snippets
    port = 389

    def configure(self):
        super(OpenLDAP, self).configure()
        self.config_attr('etcdir')
        self.config_attr('restart', 'bool')
        self.config_attr('port', 'int')

        secrets = self.find_hooks('secrets').next()
        self.uri = 'ldap://%s:%s/' % (self.host.fqdn, self.port)
        self.binddn = secrets.get('LDAP', 'binddn')
        self.bindpw = secrets.get('LDAP', 'bindpw')

    def setup_hooks(self):
        super(OpenLDAP, self).setup_hooks()
        self.hooks['openldap'] = self

    @step(1)
    def copy_config(self):
        for fn in ():
            self.install(fn, '%s/%s' % (self.etcdir, fn))

    @step(2)
    def restart_daemon(self):
        if self.restart and self.changed_files:
            self.cmd('sudo /etc/init.d/slapd restart')
