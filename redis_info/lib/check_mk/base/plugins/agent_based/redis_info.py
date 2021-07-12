#!/usr/bin/env python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Check_MK Redis Info Plugin
#
# Copyright 2016, Clemens Steinkogler <c.steinkogler[at]cashpoint.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# check_mk --debug -nv --checks=redis_info some.redis-server.dom

# example output
# <<<redis_info>>>
# +++ 127.0.0.1:6380 +++
# Failed to connect to host
# --- 127.0.0.1:6380 ---
# +++ 127.0.0.1:6379 +++
# $1858
# # Server
# redis_version:2.8.19

import time

# factory_settings ... is part of version/share/check_mk/modules/check_mk.py
factory_settings["redis_info_default_values"] = {
    'config': ((None, None), False),
}


# the inventory function
def inventory_redis_info(info):
    if len(info) > 0:
        hostinfo = ''
        for line in info:
            redis_info_item = ''
            line = " ".join(line)
            line = str(line)
            # print("line: '" + line + "'")
            if line.startswith('+++'):
                hostinfo = line.strip('+++').strip()
                # print('hostinfo: ' + hostinfo)
                continue  # just go to next line
            elif line.startswith('---'):
                continue  # end of host-section reached
            elif line.startswith('$') or line.startswith('#'):
                continue
            # endif

            errors = ['Failed', 'Error']
            if any(error in line for error in errors):
                redis_info_item = hostinfo + ": error"
                yield (redis_info_item, "redis_info_default_values")
            elif ":" in line:
                line_as_list = line.split(':')
                # we have to reformat for example ["slave0", "ip=10.12.47.107,port=6380,state=online,offset=89946822,lag=1"]
                # to get a nice useable format
                #print(str(line_as_list))
                if "=" in line_as_list[1]:
                    dissected_line_as_list = line_as_list[1].split(",")
                    # will create a new list
                    # ["ip=10.12.47.107", "port=6380", "state=online", "offset=89946822", "lag=1"]
                    for dissected_line_as_list_element in dissected_line_as_list:
                        hostinfo_part, hostinfo_value = dissected_line_as_list_element.split("=")
                        # we now split for example "ip=10.12.47.107" to hostinfo_part = "ip" and to
                        # hostinfo_value = "10.12.47.107"
                        redis_info_item = hostinfo + ": " + str(line_as_list[0]) + "_" + str(hostinfo_part)
                        # we now yield a new item - e.g.: slave0_ip: 10.12.47.107
                        # print(str(redis_info_item))
                        yield (redis_info_item, "redis_info_default_values")
                    # endfor
                else:
                    redis_info_item = hostinfo + ": " + str(line_as_list[0])
                    # print(str(redis_info_item))
                    yield (redis_info_item, "redis_info_default_values")
                # endif
            # endif
        # endfor
    # endif
# enddef


# create the perfdata stuff and save new values in counter-file        
def create_redis_total_commands_perfdata(current_total_commands, last_total_commands, last_total_commands_diff):
    total_commands_diff = None
    # parameter_name = "total_commands_processed"
    if current_total_commands > last_total_commands:  # redis was not restarted
        current_diff = current_total_commands - last_total_commands
        total_commands_diff = last_total_commands_diff + current_diff
        set_item_state('daily_redis_total_commands_diff', total_commands_diff)  # save new daily total commands difference
    # endif

    if current_total_commands < last_total_commands:  # redis must have been restarted
        total_commands_diff = last_total_commands_diff + current_total_commands  # we add the amount of new commands to the already known ones
        set_item_state('daily_redis_total_commands_diff', total_commands_diff)  # save new daily total commands difference
    # endif

    # return parameter_name, saveint(total_commands_diff)  # return the needed perfdata
    return saveint(total_commands_diff)  # return the needed perfdata-value
# enddef


def float_int_or_string(value):
    if isinstance(value, int):
        return saveint(value)
    # endif

    if isinstance(value, float):
        return savefloat(value)
    # endif

    if isinstance(value, basestring):
        value_int = saveint(value)
        value_float = savefloat(value)

        # ### DEBUGGING
        # print("value: " + str(value))
        # print("value_int: " + str(value_int))
        # print("value_float: " + str("{0:.2f}".format(round(value_float,2))))
        # some examples and their return value
        #
        # # value is initially really a string - e.g.: master
        # saveint will return    0
        # savefloat will return  0.0
        # the 'integer string' 0 is not equal to the string master - the elif will be taken into account
        # the 'float string' 0.0 is not equal to the string master - the else will be taken into account
        # so the initial given string will be returned
        #
        # # value is initially an integer given as string - e.g.: 17
        # saveint will return    17
        # savefloat will return  17.0
        # the 'integer string' 17 is equal to the string 17 the value will be returned as integer
        #
        # # value is initially a float given as string - e.g.: 17.4
        # saveint will return    17
        # savefloat will return  17.4
        # the 'integer string' 17 is not equal to the string 17.4 the elif will be taken into account
        # the 'float string' 17.4 is equal to the string 17.4 so it will be returned as float
        if str(value_int) == str(value):
            return value_int
        # as we possibly receive a value of for example 1.10, savefloat will return 1.1 - for comparison
        # we need a float with two decimal points
        elif str("{0:.2f}".format(round(value_float, 2))) == str(value):
            return value_float
        else:
            return value
        # endif
    # endif
# enddef


# the check function
def check_redis_info(item, params, info):
    perfdata = []
    state = 0

    # ### DEBUGGING
    # print(str(params))
    item_as_list = item.split(": ")
    host_in_item, hostinfo_in_item = item_as_list
    info_as_dict = {}
    create_perfdata = False
    errors = ['Failed', 'Error']
    warn, crit = params['config'][0]
    create_perfdata = params['config'][1]
    warn_crit_append_string = ""
    message = ""
    perfdata_value = None
    perfdata_value_str = None
    check_string_crit = False
    # ### DEBUGGING
    # just tried something - some interesting variables
    # print(str(get_info_for_check(g_hostname, lookup_ip_address(g_hostname), 'redis_info')))
    # print(str(extra_service_conf))
    # debug warn and crit
    # print(str(warn))
    # print(str(crit))

    for line in info:
        line = " ".join(line)
        line = str(line)
        if line.startswith('+++'):
            hostinfo = line.strip('+++').strip()
            info_as_dict[hostinfo] = {}
            continue  # just go to next line
        elif line.startswith('---'):
            continue  # end of host-section reached
        else:
            if any(error in line for error in errors):
                info_as_dict[hostinfo].update({hostinfo_in_item: str(line)})
            elif ":" in line:
                # e.g.:  line = "slave0: ip=10.12.47.107,port=6380,state=online,offset=89946822,lag=1"
                line_as_list = line.split(':')
                # e.g.: line_as_list = ["slave0", "ip=10.12.47.107,port=6380,state=online,offset=89946822,lag=1"]
                if "=" in line_as_list[1]:
                    dissected_line_as_list = line_as_list[1].split(",")
                    # will create a new list
                    # ["ip=10.12.47.107", "port=6380", "state=online", "offset=89946822", "lag=1"]
                    for dissected_line_as_list_element in dissected_line_as_list:
                        hostinfo_part, hostinfo_value = dissected_line_as_list_element.split("=")
                        info_as_dict[hostinfo].update({str(line_as_list[0]) + '_' + str(hostinfo_part): str(hostinfo_value)})
                        # e.g. info_as_dict["127.0.0.1:6379"].update({"slave0_ip": "10.12.47.107"})
                    # endfor
                else:
                    info_as_dict[hostinfo].update({line_as_list[0]: line_as_list[1]})
                # endif
            # endif
        # endif
    # endfor

    # from pprint import pprint
    # pprint(info_as_dict)

    # Catch if automatic detection is used. The plugin will not be able to connect to an previously automatically
    # detected redis-instance so here the it will be tried to read the supplied value. But if it's not available
    # a 'KeyError' would occure
    try:
        hostinfo_in_item_value = str(info_as_dict[host_in_item][hostinfo_in_item])
        # print(str(info_as_dict))
    except KeyError:
        hostinfo_in_item_value = "Error - Redis-Instance or Check not available"
    # endtry

    # if initial first connection to host fails (e.g. if first inventory is run)
    if "error" in item:
        state = 2
    # else if connection to host was lost or if REDIS is currently not running
    elif any(error in hostinfo_in_item_value for error in errors):
        state = 2
    else:
        warn = float_int_or_string(warn)
        crit = float_int_or_string(crit)
        # print("host_in_item: " + str(host_in_item))
        # print("hostinfo_in_item: " + str(hostinfo_in_item))
        # print("hostinfo_in_item value: " + str(info_as_dict[host_in_item][hostinfo_in_item]))
        perfdata_value = float_int_or_string(info_as_dict[host_in_item][hostinfo_in_item])
        # print("perfdata_value after float_int_or_string: " + str(perfdata_value))
        if isinstance(perfdata_value, basestring):
            if (warn is None) and (crit is None):
                warn_crit_append_string = " "
            else:
                warn_crit_append_string = " (crit if string changes) "
                check_string_crit = True
            # endif
        else:
            if (warn is None) and (crit is None):
                warn_crit_append_string = " "
            else:
                warn_crit_append_string = " (warn/crit at " + str(warn) + "/" + str(crit) + ")"
            # endif
        # endif

        bytes_to_mb_for = ['used_memory', 'used_memory_peak', 'used_memory_rss']
        if hostinfo_in_item in bytes_to_mb_for:
            perfdata_value = round(float(perfdata_value) / 1024 / 1024, 2)
            perfdata_value_str = str(perfdata_value) + "MB"
        else:
            perfdata_value_str = str(perfdata_value)
        # endif
    # endif

    if create_perfdata:
        # catch total_commands_processed
        if hostinfo_in_item == "total_commands_processed":
            # print("hostinfo_in_item: " + str(hostinfo_in_item))
            date = time.strftime("%Y%m%d")
            current_redis_total_commands = saveint(perfdata_value)  # current total_commands_processed value
            daily_redis_total_commands_diff = get_item_state('daily_redis_total_commands_diff')  # we try to get the daily processed total commands
            # print("daily_redis_total_commands_diff: " + str(daily_redis_total_commands_diff))

            if daily_redis_total_commands_diff is None:  # there was no value found - so this is running the first time
                # we set the few differnent counters that we need later
                daily_redis_total_commands_diff = 0
                set_item_state('daily_redis_total_commands_diff', daily_redis_total_commands_diff)
                daily_redis_total_commands_date = date
                set_item_state('daily_redis_total_commands_date', daily_redis_total_commands_date)
                last_redis_total_commands = current_redis_total_commands
                set_item_state('last_redis_total_commands', last_redis_total_commands)
                perfdata_value = saveint(daily_redis_total_commands_diff)
                # text = "%s: %d" % (parameter, saveint(daily_redis_total_commands_diff))
            else:  # we found an old value
                daily_redis_total_commands_date = get_item_state('daily_redis_total_commands_date')  # we get the set date
                last_redis_total_commands = get_item_state('last_redis_total_commands')  # we get the last total commands processed value
                # print("daily_redis_total_commands_date: " + str(daily_redis_total_commands_date))

                if daily_redis_total_commands_date == date:  # do we still have the same day?
                    # print("date: " + str(date) + " daily_redis_total_commands_date: " + str(daily_redis_total_commands_date))
                    daily_redis_total_commands_diff = get_item_state('daily_redis_total_commands_diff')

                    # we have a function for creating the perfdata stuff, it will also set the new daily_redis_total_commands_diff value
                    perfdata_value = create_redis_total_commands_perfdata(current_redis_total_commands, last_redis_total_commands, daily_redis_total_commands_diff)

                    # we set the current total commands processed as the last known - so we can calculate the values for the next check run
                    set_item_state('last_redis_total_commands', current_redis_total_commands)
                else:  # we have a new day - we must reset the already daily counted total commands processed to 0
                    daily_redis_total_commands_diff = 0
                    daily_redis_total_commands_date = date  # we set the new date
                    set_item_state('daily_redis_total_commands_date', daily_redis_total_commands_date)

                    # we have a function for creating the perfdata stuff, it will also set the new daily_redis_total_commands_diff value
                    perfdata_value = create_redis_total_commands_perfdata(current_redis_total_commands, last_redis_total_commands, daily_redis_total_commands_diff)

                    # we set the current total commands processed as the last known
                    set_item_state('last_redis_total_commands', current_redis_total_commands)
                # endif
                perfdata_value_str = str(perfdata_value)
            # endif
        # endif

        # perfdata = [(label, value*, warn, crit, min, max)]
        # * can have a unit of measurement:
        #   + no unit specified - assume a number (int or float) of things (eg, users, processes, load averages)
        #   + s - seconds (also us, ms)
        #   + % - percentage
        #   + B - bytes (also KB, MB, TB, GB?)
        #   + c - a continous counter (such as bytes transmitted on an interface)
        if (warn is None) or (crit is None):
            perfdata = [(hostinfo_in_item, perfdata_value_str)]
        else:
            perfdata = [(hostinfo_in_item, perfdata_value_str, warn, crit, 0)]
        # endif
    # endif

    if state != 2:
        message = str(hostinfo_in_item) + ": " + str(perfdata_value_str) + str(warn_crit_append_string)
    else:
        try:
            message = "(!!) An error occured: " + hostinfo_in_item_value
        except KeyError:
            state = 2
            message = "(!!) - Item not found, maybe do a Tabula Rasa :o) "
        # endtry
    # endif

    # we check if warn/crit is set and if we have to change the state
    if (warn is not None) or (crit is not None) and (state != 2):
        if check_string_crit:
            if str(crit) != perfdata_value_str:
                state = 2
                message += "difference between set string '" + str(crit) + "' detected(!!)"
            # endif
        else:
            if float_int_or_string(perfdata_value) >= crit:  # critical part
                state = 2
                message += " (!!)"
            elif float_int_or_string(perfdata_value) >= warn:  # warning part
                state = 1
                message += " (!)"
            # endif
        # endif
    # endif

    return state, message, perfdata
# enddef

# declare the check to Check_MK
check_info["redis_info"] = {
    'default_levels_variable': "redis_info_default_values",
    'inventory_function': inventory_redis_info,
    'check_function': check_redis_info,
    'service_description': 'Redis info',
    'has_perfdata': True,
    'group': "redis_info",
}
