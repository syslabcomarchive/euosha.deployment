# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.utils import Address
import os


class Supervisor(Buildout):

    user_init = u'/var/spool/init.d/${environment.service_user}/supervisor'
    listen_port = '9001'

    def configure(self):
        self.config_attr('listen_port')
        self.config_attr('user_init')

        self.address = Address('127.0.0.1', self.listen_port)
        self.programs = []
        for hook in self.find_hooks('.*:supervisor', self.host):
            self.programs.append(hook.program)

    @step(6)
    def restart_supervisor(self):
        try:
            self.cmd('bin/supervisorctl reload')
        except:
            self.cmd('bin/supervisord')

    @step(7)
    def setup_userinit(self):
        if not self.user_init:
            self.log('ignored userinit')
            return
        if not os.path.exists(os.path.dirname(self.user_init)):
            os.makedirs(os.path.dirname(self.user_init))
        self.template('init.sh', target=self.user_init)
        os.chmod(self.user_init, 0o755)
