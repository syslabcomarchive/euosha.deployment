# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.utils import Address, Hook


class Varnish(Component):

    listen_port = '8090'

    VARNISH_VERSION = '3.0.2'
    VARNISH_TAR = 'varnish-%s.tar.gz' % VARNISH_VERSION
    VARNISH_URL = 'http://repo.varnish-cache.org/source/%s' % VARNISH_TAR
    VARNISH_WORK = 'varnish-%s' % VARNISH_VERSION

    def setup_hooks(self):
        super(Varnish, self).setup_hooks()
        self.hooks['varnish:http'] = Hook()
        self.hooks['varnish:supervisor'] = Hook()

    def configure(self):
        super(Varnish, self).configure()

        self.config_attr('listen_port')
        self.address = Address(self.host.fqdn, self.listen_port)
        self.hooks['varnish:http'].address = self.address

        self.hooks['varnish:supervisor'].program = self.expand(
            '20 varnish ${component.compdir}/sbin/varnishd [-F -f etc/varnish/webwork.vcl '
            '-a ${component.address.listen} -p thread_pool_min=10 '
            '-p thread_pool_max=50 -s malloc,250M] ${component.compdir} true')

        self.haproxy = self.find_hooks('haproxy:frontend').next()
        self.frontend = self.find_hooks('portalfrontend:http').next()


    @step(1)
    def build_varnish(self):
        if os.path.exists('sbin/varnishd'):
            return
        self.cmd('wget -cq %s' % self.VARNISH_URL)
        self.cmd('tar xf %s' % self.VARNISH_TAR)
        with self.chdir(self.VARNISH_WORK):
            self.cmd('./configure --prefix=%s' % self.compdir)
            self.cmd('make install')
        os.unlink(self.VARNISH_TAR)
        shutil.rmtree(self.VARNISH_WORK)

    @step(2)
    def varnish_config(self):
        self.template('webwork.vcl.in', 'etc/varnish/webwork.vcl')
