#!/usr/bin/env python
# -*- encodig: utf-8 -*-
"""Blackbird plugin for monitoring slapd runtime information."""

import json

from blackbird.plugins import base
from blackbird.utils.helpers import global_import


class ConcreteJob(base.JobBase):
    """
    """

    def __init__(self, options, queue=None, logger=None):
        super(ConcreteJob, self).__init__(options, queue, logger)

        self.entries_generic = (
            ('cn=Monitor', 'monitoredInfo'),
            ('cn=Max File Descriptors,cn=Connections,cn=Monitor',
                'monitorCounter'),
            ('cn=Total,cn=Connections,cn=Monitor', 'monitorCounter'),
            ('cn=Current,cn=Connections,cn=Monitor', 'monitorCounter'),
            ('cn=Bind,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Unbind,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Search,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Compare,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Modify,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Modrdn,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Add,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Delete,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Abandon,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Extended,cn=Operations,cn=Monitor', 'monitorOpInitiated'),
            ('cn=Bind,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Unbind,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Search,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Compare,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Modify,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Modrdn,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Add,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Delete,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Abandon,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Extended,cn=Operations,cn=Monitor', 'monitorOpCompleted'),
            ('cn=Bytes,cn=Statistics,cn=Monitor', 'monitorCounter'),
            ('cn=PDU,cn=Statistics,cn=Monitor', 'monitorCounter'),
            ('cn=Entries,cn=Statistics,cn=Monitor', 'monitorCounter'),
            ('cn=Referrals,cn=Statistics,cn=Monitor', 'monitorCounter'),
            ('cn=Max,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=Max Pending,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=Open,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=Starting,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=Active,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=Pending,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=Backload,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=State,cn=Threads,cn=Monitor', 'monitoredInfo'),
            ('cn=Start,cn=Time,cn=Monitor', 'monitorTimestamp'),
            ('cn=Current,cn=Time,cn=Monitor', 'monitorTimestamp'),
            ('cn=Uptime,cn=Time,cn=Monitor', 'monitoredInfo'),
            ('cn=Read,cn=Waiters,cn=Monitor', 'monitorCounter'),
            ('cn=Write,cn=Waiters,cn=Monitor', 'monitorCounter'),
        )

        self.attributes_bdb = [
            'namingContexts',
            'olmBDBDNCache',
            'olmBDBEntryCache',
            'olmBDBIDLCache',
        ]

        self.ldap = global_import('ldap')
        self.connection = None

    def build_items(self):
        """
        main loop
        """
        uri = (
            'ldap://{host}:{port}'
            ''.format(host=self.options['host'], port=self.options['port'])
        )
        self.connection = self.ldap.initialize(uri)
        self.connection.set_option(self.ldap.OPT_NETWORK_TIMEOUT,
                                   self.options['timeout'])

        self.enqueue_generic_metrics()
        self.enqueue_database_metrics()

        del self.connection

    def enqueue_generic_metrics(self):
        results = self.connection.search_s(
            base='cn=Monitor',
            scope=self.ldap.SCOPE_SUBTREE,
            filterstr='(!(monitorConnectionNumber=*))',
            attrlist=['*', '+']
        )
        results = dict(results)

        for (distinguished_name, attribute_name) in self.entries_generic:
            key = format_key((distinguished_name, attribute_name))
            value = results[distinguished_name][attribute_name][0]
            self.enqueue(key, value)

    def enqueue_database_metrics(self):
        lld_data_value = []

        results = self.connection.search_s(
            base='cn=Databases,cn=Monitor',
            scope=self.ldap.SCOPE_SUBTREE,
            filterstr='(|(monitoredInfo=bdb)(monitoredInfo=hdb))',
            attrlist=['*', '+']
        )
        results = dict(results)

        for distinguished_name in results:
            db_name = results[distinguished_name]['cn'][0]
            lld_data_value.append({'{#DBNAME}': db_name})

            for attribute_name in self.attributes_bdb:
                key = ('openldap.Monitor.Databases.Item[{db},{attr}]'
                       ''.format(db=db_name, attr=attribute_name))
                value = results[distinguished_name][attribute_name][0]
                self.enqueue(key, value)

        lld_data = {'data': lld_data_value}
        self.enqueue(
            'openldap.Monitor.Databases.LLD',
            json.dumps(lld_data),
        )

    def enqueue(self, key, value):
        item = LdapItem(
            key=key,
            value=value,
            host=self.options['hostname']
        )
        self.queue.put(item, block=False)

        self.logger.debug(
            ('Enqueued: "{key}"="{value}"'
             ''.format(key=key, value=value)
             )
        )


class LdapItem(base.ItemBase):
    """
    Enqueued item.
    """

    def __init__(self, key, value, host):
        super(LdapItem, self).__init__(key, value, host)

        self._data = self._generate()

    @property
    def data(self):

        return self._data

    def _generate(self):

        data = {}
        data['key'] = self.key
        data['value'] = self.value
        data['host'] = self.host
        data['clock'] = self.clock

        return data


class Validator(base.ValidatorBase):

    def __init__(self):
        self.__spec = None

    @property
    def spec(self):
        self.__spec = (
            "[{0}]".format(__name__),
            "host = string(default='localhost')",
            "port = integer(0, 65535, default=389)",
            "timeout = integer(default=10)",
            "hostname = string(default={0})".format(self.detect_hostname()),
        )
        return self.__spec


def format_key(entry):
    """
    Format key.
    "entry" as argument is tuple type object or list type object.
    e.x:
    ('cn=Current,cn=Connections,cn=Monitor', 'monitorCounter')
    ->
    openldap.Monitor.Connections.Current[monitorCounter]
    """

    if not (type(entry) == list or type(entry) == tuple):
        raise ValueError('Ldap\'s key entry must be tuple or list!!!')

    key_name = entry[0]
    parameter = entry[1]

    key_name = key_name.split(',')
    key_name = [elem.replace('cn=', '', 1) for elem in key_name]
    key_name = [elem.replace(' ', '_') for elem in key_name]
    key_name = key_name[::-1]
    key_name = '.'.join(key_name)

    formated_key = 'openldap.{key_name}[{parameter}]'.format(
        key_name=key_name,
        parameter=parameter
    )

    return formated_key
