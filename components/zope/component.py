# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.utils import Address, Hook
import batou.utils
import glob
import os
import shutil


class Zope(Buildout):

    """Deploys the zope instance with all dependencies.

    Build requirements for ExactImage:

        * GCC
        * GNU make
        * GNU autotools
        * pkg-config
        * Python C headers
        * libtool

    """

    instance_listen_port = '8080'
    worker_listen_port = '8082'
    run_in_supervisor = 'true'

    # versions of exactimage and agg are hard-coded here since I did not find a
    # better place
    AGG_VERSION = '2.5'
    AGG_TAR = 'agg-%s.tar.gz' % AGG_VERSION
    AGG_URL = 'http://download.gocept.com/packages/%s' % AGG_TAR
    AGG_WORK = 'agg-%s' % AGG_VERSION

    EXACTIMAGE_VERSION = '0.8.7'
    EXACTIMAGE_TAR = 'exact-image-%s.tar.bz2' % EXACTIMAGE_VERSION
    EXACTIMAGE_URL = 'http://download.gocept.com/packages/%s' % (
        EXACTIMAGE_TAR)
    EXACTIMAGE_WORK = 'exact-image-%s' % EXACTIMAGE_VERSION

    features = ('instance', 'worker')

    def setup_hooks(self):
        super(Zope, self).setup_hooks()
        if 'instance' in self.features:
            self.hooks['zope:http'] = Hook()
            self.hooks['zope:supervisor'] = Hook()
        if 'worker' in self.features:
            self.hooks['worker:http'] = Hook()
            self.hooks['worker:supervisor'] = Hook()

    def configure(self):
        super(Zope, self).configure()

        self.zeo = self.find_hooks('zeo:server').next()
        self.solr = self.find_hooks('solr:server').next()
        self.ldap = self.find_hooks('openldap').next()

        self.config_attr('run_in_supervisor', 'bool')
        self.config_attr('instance_listen_port')
        self.instance_address = Address(
            self.host.fqdn, self.instance_listen_port)

        if 'instance' in self.features:
            self.hooks['zope:http'].address = self.instance_address
            if self.run_in_supervisor:
                self.hooks['zope:supervisor'].program = self.expand(
                    '20 instance (startsecs=30) '
                    '${component.compdir}/bin/instance [console] true')
            else:
                del self.hooks['zope:supervisor']

        self.config_attr('worker_listen_port')
        self.worker_address = Address(self.host.fqdn, self.worker_listen_port)
        if 'worker' in self.features:
            self.hooks['worker:http'].address = self.worker_address
            if self.run_in_supervisor:
                self.hooks['worker:supervisor'].program = self.expand(
                    '20 worker (startsecs=30 stopsignal=INT) '
                    '${component.compdir}/bin/worker [console] true')
            else:
                del self.hooks['worker:supervisor']


    # XXX step 1.5 is really a kludge. We need better step numbering.
    @step(1.5)
    def setup_compile_environment(self):
        self.old_env = os.environ.copy()
        batou.utils.prepend_env(
            'PATH', '%s/bin:/usr/lib/ccache/bin:/usr/lib/ccache' %
            self.compdir)
        batou.utils.prepend_env(
            'PKG_CONFIG_PATH', '%s/lib/pkgconfig' % self.compdir)

    def _build_agg(self):
        self.cmd('wget -cq %s' % self.AGG_URL)
        self.cmd('tar xf %s' % self.AGG_TAR)
        with self.chdir(self.AGG_WORK):
            for patch in sorted(glob.glob(
                    '%s/patches/[0-9]*.patch' % self.defdir)):
                self.cmd('patch -p0 < %s' % patch)
            self.cmd('sh autogen.sh --without-x --disable-examples --prefix=%s' %
                     self.compdir)
            self.cmd('make install')
        os.unlink(self.AGG_TAR)
        shutil.rmtree(self.AGG_WORK)

    def _build_exactimage(self):
        self.cmd('wget -cq %s' % self.EXACTIMAGE_URL)
        self.cmd('tar xf %s' % self.EXACTIMAGE_TAR)
        with self.chdir(self.EXACTIMAGE_WORK):
            self.cmd(
                './configure --prefix=%s --with-python --with-swig '
                '--without-libpng --without-libungif --without-php '
                '--without-perl --without-lua' % (self.compdir))
            self.cmd('make install')
        self.cmd('bin/python%s -c "import ExactImage"' % self.py_version)
        os.unlink(self.EXACTIMAGE_TAR)
        shutil.rmtree(self.EXACTIMAGE_WORK)

#    @step(1.6)
    def compile_exactimage(self):
        if not batou.utils.check_shared_object('lib/libagg.so'):
            self._build_agg()
        if not batou.utils.check_shared_object(
                'lib/%s/site-packages/_ExactImage.so' % self.python):
            self._build_exactimage()

    @step(1.7)
    def teardown_compile_environment(self):
        os.environ.clear()
        os.environ.update(self.old_env)

    @step(3.5)
    def ldap_settings(self):
        try:
            os.makedirs('policy/ldap')
        except OSError:
            pass
        self.template('ldapsettings.xml.in', 'policy/ldap/ldapsettings.xml')
