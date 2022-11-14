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
import mongoDB_api
import helper


'''
Method that triggers the creation of a monthly report for each organization related to an API key.
The data of each organization is stored in a MongoDB.
'''
def create_summarizing_utilization_reports(organizations, latest_daily_reports):

    desc_month_string_list = helper.get_last_x_month_year_strings(2)

    for orga in organizations:

        orga_id = orga['id']
        orga_api_enabled = orga['api']['enabled']
        
        if orga_api_enabled:
            for latest_daily_orga_report in latest_daily_reports:
                if orga['id'] == latest_daily_orga_report['organization_id']:
                    
                    #Request the latest report from this or last month. Older reports are not taken into consideration
                    latest_orga_month_report = get_orga_month_report(orga_id, desc_month_string_list)['documents']

                    #Creates utilization data for new networks, device, stacks and if no montly report available yet 
                    monthly_orga_utilization_report = enrich_past_month_report_with_new_day_report(latest_daily_orga_report, latest_daily_orga_report)

                    if latest_orga_month_report != []:
                        #Adds utilization data in comparison to the old monthly report
                        monthly_orga_utilization_report = enrich_past_month_report_with_new_day_report(latest_orga_month_report[0], monthly_orga_utilization_report)

                    update_current_orga_month_report(orga_id, desc_month_string_list[0], monthly_orga_utilization_report)


'''
Retrieves and returns an organization report from the MongoDB with the measurement_start_date value within a requested range.
'''
def get_orga_month_report(orga_id, desc_month_string_list):

    MONGO_DB_COLLECTION_NAME_MONTLY= os.environ['MONGO_DB_COLLECTION_NAME_MONTLY']

    filter_rule = {
                    "organization_id": orga_id,
                    "measurement_start_date": {
                        "$gte": helper.get_first_day_of_selected_month(desc_month_string_list[1]),
                        "$lt": helper.get_last_day_of_selected_month(desc_month_string_list[0])
                    }}

    sort_rule = { "measurement_end_date": -1 } #sort descending based on date

    last_month_report = mongoDB_api.find_many(filter_rule, sort_rule, MONGO_DB_COLLECTION_NAME_MONTLY)

    return last_month_report


'''
Updates the organization report in the MongoDB for the current month or creates a new report in case it is not yet present.
'''
def update_current_orga_month_report(orga_id, date_string, monthly_orga_utilization_report):
    
    MONGO_DB_COLLECTION_NAME_MONTLY= os.environ['MONGO_DB_COLLECTION_NAME_MONTLY']

    filter_rule = {
                    "organization_id": orga_id,
                    "measurement_start_date": {
                        "$gte": helper.get_first_day_of_selected_month(date_string),
                        "$lt": helper.get_last_day_of_selected_month(date_string)
                    }}

    mongoDB_api.update_one(monthly_orga_utilization_report, MONGO_DB_COLLECTION_NAME_MONTLY, filter_rule)


'''
Enriches the report data by comparing two reports to create the monthly report.
'''
def enrich_past_month_report_with_new_day_report(last_month_report, latest_day_report):

    new_month_report = latest_day_report.copy() 
    
    last_monthly_report_end_date= last_month_report['measurement_end_date']
    latest_daily_report_end_date= latest_day_report['measurement_end_date']

    add_higher_level_utilization(new_month_report, latest_day_report, last_month_report, 'organization_id', last_monthly_report_end_date)

    for latest_day_network_index,latest_day_network_report in enumerate(latest_day_report['networks']):
        for last_month_network_report in last_month_report['networks']:
            if last_month_network_report['network_id'] == latest_day_network_report['network_id']:
            
                add_network_utilization_level(new_month_report, latest_day_network_report, last_month_network_report, latest_day_network_index, last_monthly_report_end_date) 
                add_non_stack_switch_utilization_level(new_month_report, last_monthly_report_end_date, latest_daily_report_end_date, latest_day_network_report, last_month_network_report, latest_day_network_index)
                
                for latest_stack_index,latest_stack_report in enumerate(latest_day_network_report['stacks']):
                    for past_stack_report in last_month_network_report['stacks']:
                        if latest_stack_report['id'] == past_stack_report['id']:
                            add_stack_and_switch_utilization_level(new_month_report, last_monthly_report_end_date, latest_daily_report_end_date, latest_stack_report, past_stack_report, latest_day_network_index, latest_stack_index)                
            
    return new_month_report

'''
Adds the network utilization level data to the monthly report.
'''
def add_network_utilization_level(new_month_report, latest_day_network_report, last_month_network_report, latest_day_network_index, last_monthly_report_end_date):
    target = new_month_report['networks'][latest_day_network_index]
    add_higher_level_utilization(target, latest_day_network_report, last_month_network_report, 'network_id', last_monthly_report_end_date)

'''
Adds the non-stack switch utilization level data to the monthly report.
'''
def add_non_stack_switch_utilization_level(new_month_report, last_monthly_report_end_date, latest_daily_report_end_date, latest_day_network_report, last_month_network_report, latest_day_network_index):
    target = new_month_report['networks'][latest_day_network_index]['non_stack_switches']
    latest_non_stack_switches = latest_day_network_report['non_stack_switches']
    last_non_stack_switches = last_month_network_report['non_stack_switches']
    add_latest_port_utilization(target, last_monthly_report_end_date, latest_daily_report_end_date, latest_non_stack_switches, last_non_stack_switches)                

'''
Adds the stack and stack switch utilization level data to the monthly report.
'''
def add_stack_and_switch_utilization_level(new_month_report, last_monthly_report_end_date, latest_daily_report_end_date, latest_stack_report, past_stack_report, latest_day_network_index, latest_stack_index):
    
    stack_target = new_month_report['networks'][latest_day_network_index]['stacks'][latest_stack_index]
    switches_target =  stack_target['switches']
    latest_stack_switches = latest_stack_report['switches']
    past_stack_switches = past_stack_report['switches']
    
    add_latest_port_utilization(switches_target, last_monthly_report_end_date, latest_daily_report_end_date, latest_stack_switches, past_stack_switches)                
    add_higher_level_utilization(stack_target, latest_stack_report, past_stack_report, 'id', last_monthly_report_end_date)

'''
Calculates and adds the higher level (no port) utilization data to the monthly report. e.g. max values
Values of the previous month are not transfered.
'''
def add_higher_level_utilization(target, latest_element, past_element, key, last_monthly_report_end_date):
    
    if key in past_element and key in latest_element:
        if past_element[key] == latest_element[key]:
            
            if helper.date_is_current_month(last_monthly_report_end_date):
                extended_data = {
                        "max_utilization_percent": max(latest_element['daily_max_utilization_percent'],past_element['daily_max_utilization_percent']),
                        "max_non_uplink_port_count": max(latest_element['non_uplink_port_count'],past_element['non_uplink_port_count']),
                        "max_overall_port_count": max(latest_element['overall_port_count'],past_element['overall_port_count']),
                        "max_used_non_uplink_port_count": max(latest_element['daily_max_used_non_uplink_port_count'],past_element['daily_max_used_non_uplink_port_count']),
                    } 
            else:
                extended_data = {
                        "max_utilization_percent": latest_element['daily_max_utilization_percent'],
                        "max_non_uplink_port_count": latest_element['non_uplink_port_count'],
                        "max_overall_port_count": latest_element['overall_port_count'],
                        "max_used_non_uplink_port_count": latest_element['daily_max_used_non_uplink_port_count'],
                    } 

            target.update(extended_data)

'''
Adds the port and device level utilization data to the monthly report.
'''
def add_latest_port_utilization(target, last_monthly_report_end_date, latest_orga_end_date, latest_day_network_report, last_month_network_report):
    for latest_device_index,latest_device_report in enumerate(latest_day_network_report):
        for past_device_report in last_month_network_report:
            if past_device_report['serial'] == latest_device_report['serial']:
                device_target = target[latest_device_index]
                add_higher_level_utilization(device_target, latest_device_report, past_device_report, 'serial', last_monthly_report_end_date)
                
                #port level data
                for latest_port_index,latest_port_report in enumerate(latest_device_report['ports']):
                    for past_port_report in past_device_report['ports']:
                        if past_port_report['portId'] == latest_port_report['portId']:

                            port_target = device_target['ports'][latest_port_index]
                            add_extended_values_port_level(port_target, last_monthly_report_end_date, latest_orga_end_date, latest_port_report, past_port_report)


'''
Adds the port level utilization data to the monthly report. e.g. port history and used date
'''
def add_extended_values_port_level(target, last_monthly_report_end_date, latest_orga_end_date, latest_data, past_data):
    add_last_used_date(target, last_monthly_report_end_date, latest_orga_end_date, latest_data, past_data)
    add_unique_element_to_port_usage_history(target, latest_orga_end_date, last_monthly_report_end_date, latest_data, past_data)


'''
Calculates and adds the used date value for a port.  Value of last month is used if not used in the current month.
'''
def add_last_used_date(target, last_monthly_report_end_date, latest_orga_end_date, latest_data, past_data):

    if 'last_used_date' not in latest_data:
        target.update({'last_used_date':'None'})
    
    last_used_date = past_data['last_used_date']
    last_monthly_report_end_date = helper.string_to_date(last_monthly_report_end_date)
    
    if latest_data['used_within_1_day']: 
        last_used_date = latest_orga_end_date
    elif str(last_used_date) == 'None' and past_data['used_within_1_day']:
        last_used_date = helper.date_to_string(last_monthly_report_end_date)
    elif str(last_used_date) != 'None' and past_data['used_within_1_day'] and helper.string_to_date(last_used_date) < last_monthly_report_end_date:
        last_used_date = helper.date_to_string(last_monthly_report_end_date)

    target['last_used_date'] = last_used_date


'''
Calculates and adds the port history for a port. Port history of the previous month is not transfered.
'''
def add_unique_element_to_port_usage_history(target, latest_orga_end_date, last_monthly_report_end_date, latest_data, past_data):

    if 'usage_history' not in past_data:
        target.update({'usage_history':{latest_orga_end_date: latest_data['used_within_1_day']}})
    
    if latest_orga_end_date not in past_data['usage_history'] and helper.date_is_current_month(last_monthly_report_end_date):
        port_history = past_data['usage_history']
        port_history.update({latest_orga_end_date: latest_data['used_within_1_day']})
        target['usage_history'].update(port_history)

