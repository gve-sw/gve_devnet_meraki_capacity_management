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

from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv

import os
import meraki_api
import mongoDB_api
import helper

app = Flask(__name__)

'''
Route for orga view including information about network utilization.
'''
app.route('/?orga_id=<orga>&month=<month>')
@app.route('/', methods=['GET', 'POST'])
def dashboard():
    
    global extended_orga_report

    MONGO_DB_COLLECTION_NAME_MONTLY= os.environ['MONGO_DB_COLLECTION_NAME_MONTLY']
    orga_dropdown_content, month_dropdown_content = create_dropdown_content()
    orga_id = request.args.get('orga_id')
    month = request.args.get('month')

    extended_orga_report = []
    
    try:
        if request.method == 'POST':
            orga_id = request.form.get("organizations_select")
            month = request.form.get("month_select")
            return redirect("/?orga_id="+str(orga_id)+"&month="+str(month))

        if orga_id != 'None' and month != 'None':

            filter_rule = {
                    "organization_id": orga_id,
                    "measurement_start_date": {
                        "$gte": helper.get_first_day_of_selected_month(month),
                        "$lt": helper.get_last_day_of_selected_month(month)
                    }}

            sort_rule = { "measurement_end_date": -1 } #sort descending based on date

            orga_summaries = mongoDB_api.find_many(filter_rule, sort_rule, MONGO_DB_COLLECTION_NAME_MONTLY)

            extended_orga_reports = orga_summaries['documents']
           
            if extended_orga_reports != []:
                extended_orga_report = extended_orga_reports[0] #is latest report because of decending sorting

        return render_template('dashboard.html', orga_data=extended_orga_report, hiddenLinks=True, orga_dropdown_content=orga_dropdown_content, selected_orga_id=orga_id, month_dropdown_content=month_dropdown_content, selected_month=month)

    except Exception as e: 
        print(f'EXCEPTION!! {e}')
        return render_template('dashboard.html', orga_data=extended_orga_report, error=True, hiddenLinks=True, orga_dropdown_content=orga_dropdown_content, selected_orga_id=orga_id, selected_month=month)


'''
Route for network view including information about network utilization and switch and stack details.
'''
app.route('/network_details?orga_id=<orga_id>&month=<month>&network_id=<network_id>')
@app.route('/network_details', methods=["GET"])
def network_details():
    try:
        
        global extended_orga_report

        orga_id = request.args.get('orga_id')
        network_id = request.args.get('network_id')
        month = request.args.get('month')
        network_data = []
        measurement_end_date = []

        if orga_id != None and network_id != None:

            extended_network_summary = extended_orga_report['networks']

            #Extract the data for a specific network
            for network in extended_network_summary:
                if network['network_id'] == network_id:
                    network_data = network
            
            measurement_end_date=extended_orga_report['measurement_end_date'] 

        return render_template('network_details.html', network_data=network_data, orga_id=orga_id, month=month, network_id=network_id, measurement_end_date=measurement_end_date, hiddenLinks=False)
    
    except Exception as e: 
        print(f'EXCEPTION!! {e}')
        return render_template('network_details.html', error=True, hiddenLinks=False)


'''
Route for switch view including information about switch utilization and port details.
'''
app.route('/switch_details?orga_id=<orga_id>&month=<month>&network_id=<network_id>&serial=<serial>')
@app.route('/switch_details', methods=["GET"])
def switch_details():
    try:
        global extended_orga_report

        orga_id = request.args.get('orga_id')
        network_id = request.args.get('network_id')
        month = request.args.get('month')
        serial = request.args.get('serial')

        switch_data = []
        measurement_end_date = []

        if orga_id != None and network_id != None:

            extended_network_summary = extended_orga_report['networks']

            #Extract the data for a specific switch
            for network in extended_network_summary:
                if network['network_id'] == network_id:
                    for switch in network['non_stack_switches']:
                        if switch['serial'] == serial:
                            switch_data = switch
                    for stack in network['stacks']:  
                        for switch in stack['switches']:  
                            if switch['serial'] == serial:
                                switch_data = switch

            measurement_end_date=extended_orga_report['measurement_end_date'] 

        return render_template('switch_details.html', switch_data=switch_data, orga_id=orga_id, network_id=network_id, month=month, serial=serial, measurement_end_date=measurement_end_date ,hiddenLinks=False)
    
    except Exception as e: 
        print(f'EXCEPTION!! {e}')
        return render_template('switch_details.html', error=True, hiddenLinks=False)


'''
Returns drop down field content:
* list of yyyy-mm strings for the last 6 months
* list of organizations and their names
'''
def create_dropdown_content():

    month_dropdown_content = []
    orga_dropdown_content = []

    orga_dropdown_content = meraki_api.get_organizations()
    month_dropdown_content = helper.get_last_x_month_year_strings(6)

    return orga_dropdown_content, month_dropdown_content


if __name__ == "__main__":
    
    load_dotenv()

    extended_orga_report = [] # List holding the latest requested data

    app.run(host='0.0.0.0', port=5001, debug=True)



