# Copyright 2015 Michael Rice <michael@michaelrice.org>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Use this script to connect to a vCenter and find all HostSystems
that have the default Dell BIOS UUID. 44454C4C-0000-1020-8020-80C04F202020

This is caused when you don't set the Asset tag/Service tag before you
install ESX/i on the HostSystem. This can cause strange problems if you
rely on this UUID to track your HostSystems, or you use it to locate
your HostSystem in a vCenter. There have also been reports of 3rd
party software that uses the UUID even though it shouldn't because there
is no way to ensure UUID will be unique:
http://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=1006250
"""
from __future__ import print_function

from tools import cli
from tools import pchelper

from pyVim import connect
from pyVmomi import vim
# Disable the warning message about the self signed certs
# http://www.errr-online.com/index.php/2014/10/15/ignore-ssl-warnings-in-pyvmomi-caused-by-requests/
import requests
requests.packages.urllib3.disable_warnings()


def setup_args():
    """
    Adds additional ARG to allow the uuid to be set.
    """
    parser = cli.build_arg_parser()
    # using j here because -u is used for user
    parser.add_argument('-j', '--uuid',
                        help='UUID of the HostSystem you want to find'
                             ' duplicate of if not looking for the default'
                             ' Dell UUID: 44454C4C-0000-1020-8020-80C04F202020')

    my_args = parser.parse_args()

    return cli.prompt_for_password(my_args)


def get_si(**kwargs):
    """
    Function to fetch a ServiceInstance from the vCenter
    """
    user = kwargs.get("user")
    passwd = kwargs.get("passwd")
    host = kwargs.get("host")
    port = kwargs.get("port")
    return connect.SmartConnect(host=host,
                                user=user,
                                pwd=passwd,
                                port=int(port))


def fetch_hosts(**kwargs):
    """
    Function to fetch HostSystems from vCenter using a property collector
    """
    service_instance = kwargs.get('service_instance')
    host_properties = ["name", "hardware.systemInfo.uuid"]
    host_view = pchelper.get_container_view(service_instance, [vim.HostSystem])
    host_data = pchelper.collect_properties(service_instance, host_view, vim.HostSystem,
                                            host_properties)
    return host_data

if __name__ == "__main__":
    args = setup_args()
    # This is the default dell uuid when a service tag/asset tag fails to get set
    # before you install esx/i
    default_uuid = '44454C4C-0000-1020-8020-80C04F202020'
    if args.uuid:
        default_uuid = args.uuid
    service_instance = get_si(user=args.user,
                              passwd=args.password, host=args.host, port=args.port)
    hosts = fetch_hosts(service_instance=service_instance)
    print("Found {} total HostSystems on {}.".format(len(hosts), args.host))
    found_hosts = 0
    for host in hosts:
        if host['hardware.systemInfo.uuid'] == default_uuid:
            found_hosts += 1
            print("Name: {} -- {}".format(host['name'], host['hardware.systemInfo.uuid']))
    print("Found {} HostSystems with a UUID of: {}".format(
        found_hosts, default_uuid
    ))
    connect.Disconnect(service_instance)