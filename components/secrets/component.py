# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

"""Component to handle secure distribution of secrets"""

from batou.secrets import SecretsFile
from batou.passphrase import PassphraseFile
import contextlib
import ConfigParser
import os
import StringIO


class SecretNoFoundError(KeyError):
    pass


class Secrets(Component):
    """Secrets registry.

    Each environment may define a likewise-named cfg file in the
    component source directory that contains sections and options. The
    secrets files are stored encrypted on disk. At configuration time,
    this component asks for a password (unless provided in a password
    file) and exports the decrypted secrets.

    Create/modify a secret file with the `secretsedit` utility.
    Alternatively, you can create secrets files manually with the
    `aespipe` utility::

        aespipe -P passphrase_file <cleartext.cfg >secret.cfg.aes
    """

    def __init__(self, *args, **kwargs):
        super(Secrets, self).__init__(*args, **kwargs)
        self.encrypted_file = u'%s/%s.cfg.aes' % (
            self.defdir, self.environment.name)
        self.config = None

    def setup_hooks(self):
        # XXX break up the hook from the component.
        self.hooks['secrets'] = self

    @contextlib.contextmanager
    def passphrase_file(self):
        """Runs the associated block with a passphrase file.

        The file name of the file containing the passphrase (terminated with
        newline) is passed as a single argument.
        """
        pf = u'%s/.batou-passphrase' % self.service.base
        if os.path.exists(pf):
            yield pf
            return
        with PassphraseFile('environment "%s"' % self.environment.name) as pf:
            yield pf

    def configure(self):
        if self.config:
            return
        self.config = ConfigParser.SafeConfigParser()
        if os.path.exists(self.encrypted_file):
            with self.passphrase_file() as passphrase:
                with SecretsFile(self.encrypted_file, passphrase) as secrets:
                    self.config.readfp(
                        StringIO.StringIO(secrets.read()), self.encrypted_file)

    def get(self, section, option):
        """Retrieve secrets from decrypted secrets file.

        If the requested secret is not found, we'll reraise the
        exception as SecretNoFoundError to avoid that callers need to
        know anything about ConfigParser.
        """
        try:
            return self.config.get(section, option)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as e:
            raise SecretNoFoundError(
                'cannot locate option [%s] %s in secrets file' %
                (section, option), self.encrypted_file, section, option)
