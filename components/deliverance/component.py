# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.utils import Address, Hook
import os.path
import shutil


class Deliverance(Buildout):
    """Configure deliverance.

    Deliverance sits in front of the Zope servers.

    Required secrets::
        [deliverance]
        dev_user = USERNAME
        dev_password = PASSWORD

    Configuration variables::
        [component:deliverance]
        address = HOST:PORT
            Where to open the listening socket

    Exported hooks:
        * deliverance:supervisor - register daemon for automatic startup
        * deliverance:http - where to point downstream components (like haproxy)

    Imported hooks:
        * zope:http - address of upstream Zope
    """

    address = '${host.fqdn}:7000'
    dev_user = 'admin'
    dev_password = 'admin'

    def setup_hooks(self):
        super(Deliverance, self).setup_hooks()
        self.hooks['deliverance:supervisor'] = Hook()
        self.hooks['deliverance:http'] = Hook()

    def configure(self):
        super(Deliverance, self).configure()
        self.config_attr('address')

        secrets = self.find_hooks('secrets').next()
        self.dev_user = secrets.get('deliverance', 'dev_user')
        self.dev_password = secrets.get('deliverance', 'dev_password')

        self.address = Address(self.address)
        self.hooks['deliverance:http'].address = self.address
        self.hooks['deliverance:http'].backend = 'deliverance'
        self.hooks['deliverance:http'].name = self.host.name

        self.hooks['deliverance:supervisor'].program = self.expand(
                '30 deliverance (startsecs=10) '
                '${component.compdir}/bin/deliverance-proxy '
                '[${component.compdir}/rules-hw2012.xml] true')

        self.upstream = self.find_hooks('zope:http', self.host).next()

    @step(9)
    def pull_deliverance_rules(self):
        if not os.path.exists('themes'):
            shutil.mkdir('themes')
            self.cmd('svn co https://svn.syslab.com/svn/OSHA/Campaign-maintenance/Prototype/ themes/hw2010')
            self.cmd('svn co https://svn.syslab.com/svn/OSHA/Campaign-prevention/Prototype/ themes/hw2012')
        with self.chdir('themes'):
            self.cmd('svn up hw2010')
            self.cmd('svn up hw2012')

    @step(10)
    def generate_deliverance_rules(self):
        self.template('rules-hw2010.xml.in', 'rules-hw2010.xml')
        self.template('rules-hw2012.xml.in', 'rules-hw2012.xml')
