#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) 2017 Heinlein Support GmbH
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

from .agent_based_api.v1.type_defs import (
    CheckResult,
    DiscoveryResult,
)

from .agent_based_api.v1 import (
    get_rate,
    get_value_store,
    register,
    render,
    Metric,
    Result,
    State,
    Service,
    )

# factory_settings['ox_filestore_default_levels'] = {
#     'reserved': (80.0, 90.0),
#     'used': (80.0, 90.0),
#     'ent': (80.0, 90.0),
# }

def parse_ox_filestore(string_table):
    section = {}
    return section

# register.agent_section(
#     name="ox_filestore",
#     parse_function=parse_ox_filestore,
# )

def inventory_ox_filestore(info):
    for line in info:
        if line[1] != 'path':
            yield line[1], None

def check_ox_filestore(item, params, info):
    for line in info:
        if line[1] == item:
            size = saveint(line[2])
            reserved = saveint(line[3])
            used = saveint(line[4])
            maxent = saveint(line[5])
            curent = saveint(line[6])

            if size > 0:
                percreserved = reserved * 100.0 / size
                percused = used * 100.0 / size
            else:
                percreserved = 0
                percused = 0
            if maxent > 0:
                percent = curent * 100.0 / maxent
            else:
                percent = 0

            perfdata = [ ( 'reserved', reserved, size * params['reserved'][0] / 100.0, size * params['reserved'][1] / 100.0, 0, size ),
                         ( 'used', percused, params['used'][0], params['used'][1], 0, 100 ),
                         ( 'entities', curent, maxent * params['ent'][0] / 100.0, maxent * params['ent'][1] / 100.0, 0, maxent ) ]
            msg = ''
            state = 0

            msg += "Filestore reserved is %.2f%%" % percreserved
            if percreserved > params['reserved'][1]:
                state = 2
            elif percreserved > params['reserved'][0]:
                state = 1
            msg += state_markers[state]

            msg += ", used is %.2f%%" % percused
            if percused > params['used'][1]:
                state = 2
                msg += state_markers[2]
            elif percused > params['used'][0]:
                if state == 0:
                    state = 1
                msg += state_markers[1]

            msg += ", entities at %.2f%%" % percent
            if percent > params['ent'][1]:
                state = 2
                msg += state_markers[2]
            elif percent > params['ent'][0]:
                if state == 0:
                    state = 1
                msg += state_markers[1]

            return (state, msg, perfdata)

# check_info["ox_filestore"] = {
#     'check_function':          check_ox_filestore,
#     'inventory_function':      inventory_ox_filestore,
#     'service_description':     'OX Filestore %s',
#     'has_perfdata':            True,
#     'group':                   'ox_filestore',
#     'default_levels_variable': 'ox_filestore_default_levels',
# }
