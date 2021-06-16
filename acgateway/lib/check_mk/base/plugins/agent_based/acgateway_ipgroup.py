#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) 2019 Heinlein Support GmbH
#          Robert Sander <r.sander@heinlein-support.de>

#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

def _item_acgateway_ipgroup(line):
    return "%s %s" % (line[0], line[4])

def parse_acgateway_ipgroup(info):
    rowStatus = {
        u'1': u'active',
        u'2': u'notInService',
        u'3': u'notReady',
    }
    ipGroupType = {
        u'0': u'server',
        u'1': u'user',
        u'2': u'gateway',
    }
    parsed = {}
    for line in info:
        item = _item_acgateway_ipgroup(line)
        parsed[item] = {u'ipgroupstatus': rowStatus.get(line[1], u'unknown'),
                        u'ipgrouptype': ipGroupType.get(line[2], u'unknown'),
                        u'description': line[3],
                        u'name': line[4]}
    return parsed

def inventory_acgateway_ipgroup(parsed):
    for item, data in parsed.iteritems():
        yield (item, {'ipgroupstatus': data.get('ipgroupstatus')})

def check_acgateway_ipgroup(item, params, parsed):
    if item in parsed:
        data = parsed[item]
        yield 0, 'ip group type: %s' % data[u'ipgrouptype']
        if data[u'description']:
            yield 0, data[u'description']
        for param, value in params.iteritems():
            if value != data.get(param):
                yield 2, '%s is %s(!!)' % (param, data.get(param))

# check_info['acgateway_ipgroup'] = {
#     'parse_function'        : parse_acgateway_ipgroup,
#     'inventory_function'    : inventory_acgateway_ipgroup,
#     'check_function'        : check_acgateway_ipgroup,
#     'service_description'   : 'IP Group %s',
#     'has_perfdata'          : False,
#     'snmp_info'             : ( '.1.3.6.1.4.1.5003.9.10.3.1.1.23.21.1', [ '1',  # 0  AcGateway::ipGroupIndex
#                                                                           '2',  # 1  AcGateway::ipGroupRowStatus
#                                                                           '5',  # 2  AcGateway::ipGroupType
#                                                                           '6',  # 3  AcGateway::ipGroupDescription
#                                                                           '31', # 4  AcGateway::ipGroupName
#                                                                         ] ),
#     'snmp_scan_function'    : lambda oid: oid('.1.3.6.1.2.1.1.2.0').startswith('.1.3.6.1.4.1.5003.8.1.1'),
# }
