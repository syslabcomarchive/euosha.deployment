# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

"""Configure mail server settings as far as this is possible."""

from __future__ import print_function, unicode_literals
from batou.utils import Address, Hook
import subprocess


class Mail(Component):
    """Configure mail server.

    We expect a gocept.net managed mailserver to be present on the
    machine. Currently, this components exports the host name and sets
    SASL credentials for mail submission.

    Required secrets::
        [mailout]
        username = SMTP_AUTH_USERNAME
        password = SMTP_AUTH_PASSWORD

    Configuration variables::
        [mail]
        myhostname = FQDN
            The externally visible host name for outgoing SMTP
            connections
        port = PORTNUMBER
            The port number for outgoing SMTP connections
        sasl_set_password = BOOLEAN
            Whether we should try to set the sasl user (requires `sudo
            saslpasswd`)

    Hooks:

    * mailout
      - address - hostname:port for outgoing SMTP
      - username - SMTP AUTH
      - password - SMTP AUTH
    """

    myhostname = ''
    port = 587
    sasl_set_password = True

    def setup_hooks(self):
        super(Mail, self).setup_hooks()
        self.hooks['mailout'] = Hook()
        self.hooks['mailin'] = Hook()

    def configure(self):
        super(Mail, self).configure()
        secrets = self.find_hooks('secrets').next()
        self.username = secrets.get('mailout', 'username')
        self.password = secrets.get('mailout', 'password')
        self.config_attr('sasl_set_password', 'bool')
        self.config_attr('port')
        self.config_attr('myhostname')
        if not self.myhostname:
            print('trying to read myhostname')
            with open('/etc/postfix/myhostname') as f:
                self.myhostname = f.read().strip()
        self.address = Address(self.myhostname, self.port).connect

    @step(1)
    def update_sasl(self):
        if not self.sasl_set_password:
            return
        saslpasswd = subprocess.Popen([
            'sudo', 'saslpasswd', '-u%s' % self.myhostname,
            self.username], stdin=subprocess.PIPE)
        saslpasswd.communicate(self.password)
        if saslpasswd.returncode != 0:
            raise RuntimeError('failed saslpasswd execution',
                               saslpasswd)
