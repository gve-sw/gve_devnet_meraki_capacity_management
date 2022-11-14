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

import os
from pprint import pprint
from dotenv import load_dotenv
import meraki_api
import mongoDB_api
import helper


'''
Method triggers creation of an daily utilization report for each organization connected to an API key.
The data of all organizations is returned as a list and stored in a MongoDB.
'''
def create_daily_utilization_reports(organizations):

    MONGO_DB_COLLECTION_NAME_DAILY= os.environ['MONGO_DB_COLLECTION_NAME_DAILY']
    daily_orga_utilization_reports = []

    for orga in organizations:
        
        orga_id = orga['id']
        orga_name = orga['name']
        orga_api_enabled = orga['api']['enabled']
        
        if orga_api_enabled:

            daily_orga_utilization_report = create_daily_orga_report(orga_name, orga_id)
            daily_orga_utilization_reports.append(daily_orga_utilization_report)
        
        else: 
            print(str(orga['name']) + ": API is not enabled for this organization. Thereby, no report created for the mentioned organization.")

    mongoDB_api.insert_many(daily_orga_utilization_reports, MONGO_DB_COLLECTION_NAME_DAILY)

    return daily_orga_utilization_reports


'''
Method that requests current organization, network, stack, switch and port data for a specific organization,
caluclates the utilization values and creates a summarizing utilization report.
The data of one organization is returned as a dict.
'''
def create_daily_orga_report(orga_name, orga_id):

    daily_orga_utilization_report = initialize_daily_orga_report(orga_name, orga_id)

    orga_switches_and_their_ports = meraki_api.get_organization_switch_ports_by_switch(orga_id)  
    orga_inventory = meraki_api.get_organization_inventory_devices(orga_id)
    orga_devices = meraki_api.get_organization_devices(orga_id)
    
    networks = create_networks_list(orga_switches_and_their_ports)
    
    add_networks_level_data(daily_orga_utilization_report, networks)

    for network_index, network in enumerate(networks):
        
        stacks, network_stack_switches_list = create_stack_list(network)
        
        add_stack_level_base_structure(daily_orga_utilization_report, stacks, network_stack_switches_list, network_index)

        for switch in orga_switches_and_their_ports:
            
            if switch['network']['id'] == network['network_id']:

                add_switch_and_stack_level_data_and_utilization(daily_orga_utilization_report, switch, stacks, network_stack_switches_list, network_index, orga_inventory, orga_devices)

        add_daily_stack_utilization_data(daily_orga_utilization_report, network_index)
        
        add_daily_network_utilization_data(daily_orga_utilization_report, network_index)

    add_daily_orga_utilization_report(daily_orga_utilization_report)
    
    return daily_orga_utilization_report


'''
Initializes the orga utilization report dict with report identifiers.
'''
def initialize_daily_orga_report(orga_name, orga_id):
    
    daily_orga_utilization_report = {
                    "measurement_start_date": helper.get_today_minus_x_day(1), 
                    "measurement_end_date": helper.get_today(),
                    "organization_name": orga_name,
                    "organization_id": orga_id
                    }
    return daily_orga_utilization_report


#NETWORK LEVEL
'''
Creates and returns a list of all networks of an organization based of the response of 
the "Get Organization Switch Ports By Switch" Call (https://developer.cisco.com/meraki/api-v1/#!get-organization-switch-ports-by-switch).
'''
def create_networks_list(orga_switches_and_their_ports):
    
    networks = []

    for switch in orga_switches_and_their_ports:
        
        network_name = switch['network']['name']
        network_id = switch['network']['id']

        network = {
                    "network_name": network_name,
                    "network_id": network_id
                    } 
        
        if network not in networks:
            networks.append(network)

    return networks


'''
Adds the network layer and associated network information to a orga report.
'''
def add_networks_level_data(daily_orga_utilization_report, networks):

    daily_orga_utilization_report['networks'] = networks 


#STACK LEVEL
'''
Creates and returns:
* a list of all serials of stack switches of a network 
* a list of the base stack switch level dicts (id, name, switches (serial)) -> will be further populated at later step
based of the response of the "Get Network Switch Stacks" Call (https://developer.cisco.com/meraki/api-v1/#!get-network-switch-stacks).
'''
def create_stack_list(network):

    network = network['network_id']
    
    stacks = meraki_api.get_network_switch_stacks(network)

    formated_stacks_list = []
    network_stack_switches_list = []

    for stack in stacks:
        switches = []
        
        for serial in stack['serials']:
            switches.append({"serial": serial})
            network_stack_switches_list.append(serial)
    
        formated_stacks_list.append({
                "id": stack['id'],
                "name": stack['name'],
                "switches": switches
            })

    return formated_stacks_list, network_stack_switches_list


'''
Adds the base stack level and associated stack information to a report.
'''
def add_stack_level_base_structure(daily_orga_utilization_report, stacks, network_stack_switches_list, network_index):
    
    network_target = daily_orga_utilization_report['networks'][network_index]
    
    #Add stacks
    network_target.update({'stacks': stacks})                

    #Add placeholder list for non stack switches
    network_target['non_stack_switches'] = [] 

    return stacks, network_stack_switches_list


#SWITCH LEVEL
'''
Adds the switch level (stack and non-stack) and associated switch information to report.
'''
def add_switch_and_stack_level_data_and_utilization(daily_orga_utilization_report, switch, stacks, network_stack_switches_list, network_index, orga_inventory, orga_devices):
    
    switch_serial = switch['serial']
    port_statuses_24h = meraki_api.get_device_switch_port_stauses_for_24h(switch_serial)
    orga_switch_port_info = switch['ports']

    if switch_serial not in network_stack_switches_list: 
        switch_and_port_data_and_utilization = get_switch_data_and_port_and_utilization(False, port_statuses_24h, orga_switch_port_info, switch, orga_inventory, orga_devices)
        add_non_stack_switch_level(daily_orga_utilization_report, network_index, switch_and_port_data_and_utilization)
    else: 
        switch_and_port_data_and_utilization = get_switch_data_and_port_and_utilization(True, port_statuses_24h, orga_switch_port_info, switch, orga_inventory, orga_devices)
        add_stack_switch_level(daily_orga_utilization_report, network_index, switch_serial, stacks, switch_and_port_data_and_utilization)


'''
Adds the non-stack switch level and associated non-stack switch information to a report.
'''
def add_non_stack_switch_level(daily_orga_utilization_report, network_index, switch_and_port_data_and_utilization):
    
    non_stack_switch_target = daily_orga_utilization_report['networks'][network_index]['non_stack_switches']
    non_stack_switch_target.append(switch_and_port_data_and_utilization)


'''
Adds the stack switch level and associated stack switch information to a report.
'''
def add_stack_switch_level(daily_orga_utilization_report, network_index, switch_serial, stacks, switch_and_port_data_and_utilization):
    
    for stack_index, stack in enumerate(stacks):
        for stack_switch_index, stack_switch in enumerate(stack['switches']):
            if switch_serial == stack_switch['serial']:
                
                stack_switch_target = daily_orga_utilization_report['networks'][network_index]['stacks'][stack_index]['switches'][stack_switch_index]
                stack_switch_target.update(switch_and_port_data_and_utilization)


#SWITCH AND PORT LEVEL
'''
Method to request switch and port information and calculate utilization values.
'''
def get_switch_data_and_port_and_utilization(is_stack_port, port_statuses, orga_switch_port_info, switch, orga_inventory, orga_devices):
    
    switch_serial = switch['serial']
    claimed_at_date = get_associated_claimed_at_date_or_None(switch_serial, orga_inventory)
    switch_notes = get_associated_switch_notes(switch_serial, orga_devices)
    port_statuses_available = len(port_statuses) > 0

    if port_statuses_available:
        if is_stack_port:
            non_uplink_or_stack_ports = get_non_stack_or_uplink_port_ids(switch)
        else:
            non_uplink_or_stack_ports = get_non_uplink_port_ids(switch)
        non_uplink_port_count = len(non_uplink_or_stack_ports)
        overall_port_count = len(port_statuses)
        current_used_non_uplink_or_stack_port_count = get_currently_used_non_uplink_or_stack_ports_count(port_statuses, non_uplink_or_stack_ports)
        port_statuses = get_enhanced_port_level_data(port_statuses, orga_switch_port_info,  non_uplink_or_stack_ports)
        daily_max_used_non_uplink_port_count = get_daily_max_used_non_uplink_port_count(port_statuses, non_uplink_or_stack_ports)

        try: 
            utilization_percent = current_used_non_uplink_or_stack_port_count / non_uplink_port_count * 100 
            daily_max_utilization_percent = daily_max_used_non_uplink_port_count / non_uplink_port_count * 100 
        except ZeroDivisionError:
            utilization_percent = 0
            daily_max_utilization_percent = 0

        switch_and_port_data_and_utilization = { 
            "serial": switch_serial,
            "name": switch['name'],
            "model": switch['model'],
            "claimedAt": claimed_at_date,
            "switch_notes": switch_notes,
            "non_uplink_port_count": non_uplink_port_count,
            "overall_port_count": overall_port_count,
            "current_used_non_uplink_or_stack_port_count": current_used_non_uplink_or_stack_port_count,
            "utilization_percent": utilization_percent,
            "daily_max_used_non_uplink_port_count":daily_max_used_non_uplink_port_count,
            "daily_max_utilization_percent": daily_max_utilization_percent,
            "ports": port_statuses
        }    
    else:
        switch_and_port_data_and_utilization = { 
            "serial": switch_serial,
            "name": switch['name'],
            "model": switch['model'],
            "claimedAt": claimed_at_date,
            "switch_notes": switch_notes,
            "non_uplink_port_count": 0,
            "overall_port_count": 0,
            "current_used_non_uplink_or_stack_port_count": 0,
            "daily_max_used_non_uplink_port_count":0,
            "utilization_percent": 0,
            "daily_max_utilization_percent":0,
            "ports": []
        }

    return switch_and_port_data_and_utilization


'''Returns the claimed at date of an organization switch based on the organization inventory list. 
If no switch with the wanted serial number is in the inventory list, None is returned.'''
def get_associated_claimed_at_date_or_None(switch_serial, orga_inventory):
    
    claimed_at = get_listelem_key_value_or_None(switch_serial, 'serial', orga_inventory, 'claimedAt')
    return claimed_at


'''Returns the notes value of an organization switch based on the organization device list. 
If no switch with the wanted serial number is in the device list, None is returned.'''
def get_associated_switch_notes(switch_serial, orga_devices): 
    notes = get_listelem_key_value_or_None(switch_serial, 'serial', orga_devices, 'notes')
    return notes


'''
Returns the value of a specific key within a list element that has a specific matching 
key value pair e.g. serial number
'''
def get_listelem_key_value_or_None(element_identifier_value, element_idenifier_key, list, value_key):
    
    for element in list:
        if element[element_idenifier_key] == element_identifier_value:
            return element[value_key]
    
    return None


#PORT LEVEL
'''
Returns portId list of non uplink ports on non stack switches. Non uplink ports are identified through the absence of a specific tag e.g. managed.
'''
def get_non_uplink_port_ids(device):

    NON_UPLINK_TAG = os.environ['NON_UPLINK_TAG']
    
    non_uplink_ports = []
    
    for port in device['ports']:
        if NON_UPLINK_TAG not in port['tags']:
            non_uplink_ports.append(port['portId'])

    return non_uplink_ports


'''
Returns list of non stack dedicated or uplink ports of a stack switch. Non stack or uplink ports are identified through a specific tag e.g. customer_editable.
'''
def get_non_stack_or_uplink_port_ids(device):
    
    NON_STACK_PORT_TAG = os.environ['NON_STACK_PORT_TAG']

    non_stack_or_uplink_ports = []
    
    for port in device['ports']:
        if NON_STACK_PORT_TAG in port['tags']:
            non_stack_or_uplink_ports.append(port['portId'])

    return non_stack_or_uplink_ports


'''
Returns number of currently used non uplink or stack ports, based on the connected status or a port
'''
def get_currently_used_non_uplink_or_stack_ports_count(port_statuses, non_uplink_or_stack_ports):
    
    current_used_non_uplink_or_stack_port_count = 0

    for port in port_statuses:
        if port['status'] == 'Connected' and port['portId'] in non_uplink_or_stack_ports: 
            current_used_non_uplink_or_stack_port_count += 1
    
    return current_used_non_uplink_or_stack_port_count


'''
Returns number of max used ports throughout the last 24h.  
Ports were not necessarily used at the same time. 
A port is considered used as soon as it has been used once within 24 hours.
'''
def get_daily_max_used_non_uplink_port_count(port_statuses, non_uplink_or_stack_ports):
    
    daily_max_used_non_uplink_port_count = 0

    for port in port_statuses:
        if port['used_within_1_day'] == True and port['portId'] in non_uplink_or_stack_ports:
            daily_max_used_non_uplink_port_count += 1
    
    return daily_max_used_non_uplink_port_count


'''
Returns the enhanced port level data. It adds additional vlan, isUplink or usedWithin24h data.
'''
def get_enhanced_port_level_data(port_statuses, orga_switch_port_info, non_uplink_or_stack_ports):

    for port_index, status_port in enumerate(port_statuses):

        for orga_switch_port in orga_switch_port_info:
            if orga_switch_port['portId'] == status_port['portId']:

                port_statuses[port_index].update(
                    {   
                        "vlan": orga_switch_port['vlan'],
                        "voiceVlan": orga_switch_port['voiceVlan'],
                        "allowedVlans" : orga_switch_port['allowedVlans'],
                        "type": orga_switch_port['type'],
                        "taggedUplink": status_port['portId'] not in non_uplink_or_stack_ports,
                        "used_within_1_day": port_used_within_24_h(status_port)
                    })
        
    return port_statuses


'''
Checks if a port was used within the last 24h (based on traffic) or is currently in use.
Note: It takes some time until the latest traffic value is available via API. 
A change is thereby not immediately detectable via API. 
'''
def port_used_within_24_h(port_status):
    
    return port_status['usageInKb']['total'] > 0 or port_status['status'] == 'port_status'


'''
Enhances the report with further organization utilization data based on the calculated lower level data
'''
def add_daily_orga_utilization_report(daily_orga_utilization_report):
    
    networks = daily_orga_utilization_report['networks']
    utilization_level_data = get_level_utilzation_data(networks)
    daily_orga_utilization_report.update(utilization_level_data)


'''
Enhances the report with further network utilization data based on the calculated lower level data
'''
def add_daily_network_utilization_data(daily_orga_utilization_report, network_index):
    
    network = daily_orga_utilization_report['networks'][network_index]
    utilization_level_data = get_network_utilzation_data(network)
    network.update(utilization_level_data)


'''
Enhances the report with further stack utilization data based on the calculated lower level data
'''
def add_daily_stack_utilization_data(daily_orga_utilization_report, network_index):

    stacks = daily_orga_utilization_report['networks'][network_index]['stacks']

    for stack_index, stack in enumerate(stacks):
        
        stack_switches = stacks[stack_index]['switches']
        
        utilization_level = get_level_utilzation_data(stack_switches)
        stacks[stack_index].update(utilization_level)
        

'''
Caluclates and returns network level utilization data based on the data of stack and non-stack switches
'''
def get_network_utilzation_data(network):
    
    utilization_data_list = []
    non_stack_switches = network['non_stack_switches']
    stack_switches = network['stacks']

    utilization_data_list.append(get_level_utilzation_data(non_stack_switches))
    utilization_data_list.append(get_level_utilzation_data(stack_switches))
    utilization_level_data = get_level_utilzation_data(utilization_data_list)
    
    return utilization_level_data


'''
Caluclates and returns utilization data for different levels by aggreating lower level utilization data.
'''
def get_level_utilzation_data(data_list):
    
    non_uplink_port_count = 0
    overall_port_count = 0
    current_used_non_uplink_or_stack_port_count = 0
    daily_max_used_non_uplink_port_count = 0
    daily_max_utilization_percent = 0

    for list_elem in data_list:
        non_uplink_port_count += int(list_elem['non_uplink_port_count'])      
        overall_port_count += int(list_elem['overall_port_count'])
        current_used_non_uplink_or_stack_port_count += int(list_elem['current_used_non_uplink_or_stack_port_count'])
        daily_max_used_non_uplink_port_count += int(list_elem['daily_max_used_non_uplink_port_count'])
    try: 
        utilization_percent = current_used_non_uplink_or_stack_port_count / non_uplink_port_count * 100 
        daily_max_utilization_percent = daily_max_used_non_uplink_port_count / non_uplink_port_count * 100 
    except ZeroDivisionError:
        utilization_percent = 0
        daily_max_utilization_percent = 0

    utilization_level = {
        "non_uplink_port_count": non_uplink_port_count,
        "overall_port_count": overall_port_count,
        "current_used_non_uplink_or_stack_port_count": current_used_non_uplink_or_stack_port_count,
        "utilization_percent": utilization_percent,
        "daily_max_used_non_uplink_port_count":daily_max_used_non_uplink_port_count,
        "daily_max_utilization_percent": daily_max_utilization_percent
    }

    return utilization_level

