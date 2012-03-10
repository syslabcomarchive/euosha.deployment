# Copyright (c) 2012 gocept gmbh & co. kg
# See also LICENSE.txt

from batou.components.haproxy import HAProxy


class HAProxy(HAProxy):

    backend_hooks = ['deliverance:http']
