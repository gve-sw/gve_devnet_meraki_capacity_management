""" Copyright (c) 2022 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

import meraki
import os
from dotenv import load_dotenv

load_dotenv()

DASHBOARD = meraki.DashboardAPI(
        api_key=os.environ['MERAKI_API_TOKEN'],
        base_url='https://api.meraki.com/api/v1/',
        output_log=False,
        print_console=False
        )

def get_organizations():
    response = DASHBOARD.organizations.getOrganizations()
    return response

def get_networks(orga_id):
    response = DASHBOARD.organizations.getOrganizationNetworks(orga_id)
    return response

def get_organization_inventory_devices(orga_id):
    response = DASHBOARD.organizations.getOrganizationInventoryDevices(orga_id)
    return response

def get_organization_devices(orga_id):
    response = DASHBOARD.organizations.getOrganizationDevices(orga_id)
    return response

def get_organization_switch_ports_by_switch(orga_id):
    response = DASHBOARD.switch.getOrganizationSwitchPortsBySwitch(orga_id)
    return response

def get_network_switch_stacks(network_id):
    response = DASHBOARD.switch.getNetworkSwitchStacks(network_id)
    return response

def get_device_switch_port_stauses_packets(serial):
    response = DASHBOARD.switch.getDeviceSwitchPortsStatusesPackets(serial)
    return response

'''
Note: It takes some time until the latest traffic value is available via API. 
A change is thereby not immediately detectable via API. Thereby, we add an extra of 30 min to make 
sure no utilization is undetected. Overlapping is happening instead.
'''
def get_device_switch_port_stauses_for_24h(serial):
    one_day_in_seconds = 86400
    overlapping_for_API_delay = 1800
    timespan = one_day_in_seconds + overlapping_for_API_delay
    response = DASHBOARD.switch.getDeviceSwitchPortsStatuses(serial, timespan=timespan)
    return response

        
