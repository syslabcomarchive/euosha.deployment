# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

"""SSH key management"""

import batou.utils
import os.path
import os


class SSH(Component):
    """Install SSH user and host keys.

    User keys are read from the secrets file and written to
    ~/.ssh/id_dsa{,.pub}.
    """

    id_dsa = None
    id_dsa_pub = None
    sshdir = os.path.expanduser(u'~/.ssh')
    scan_hosts = None

    def configure(self):
        secrets = self.find_hooks('secrets').next()
        try:
            self.id_dsa = secrets.get('ssh', 'id_dsa')
            self.id_dsa_pub = secrets.get('ssh', 'id_dsa.pub')
        except KeyError:
            pass
        self.scan_hosts = batou.utils.string_list(
            self.config_attr('scan-hosts'))

    def install_key(self, key, keyfile, mode=None):
        if os.path.exists(keyfile):
            with open(keyfile) as kf:
                if key == kf.read().strip():
                    return
        with open(keyfile, 'w') as kf:
            if mode:
                os.chmod(keyfile, mode)
            kf.write(key.strip() + '\n')

    @step(0)
    def disable_ssh_agent(self):
        try:
            del os.environ['SSH_AUTH_SOCK']
        except KeyError:
            pass

    @step(1)
    def ensure_ssh_dir(self):
        if not os.path.exists(self.sshdir):
            os.mkdir(self.sshdir, 0o711)

    @step(2)
    def install_private_key(self):
        if not self.id_dsa:
            return
        self.install_key(self.id_dsa, u'%s/id_dsa' % self.sshdir, 0o600)

    @step(3)
    def install_public_key(self):
        if not self.id_dsa_pub:
            return
        self.install_key(self.id_dsa_pub, u'%s/id_dsa.pub' % self.sshdir)

    @step(4)
    def known_hosts(self):
        for host in self.scan_hosts:
            self.cmd('grep -q %(host)s ~/.ssh/known_hosts || '
                     'ssh-keyscan %(host)s >> ~/.ssh/known_hosts' % {
                         'host': host})
