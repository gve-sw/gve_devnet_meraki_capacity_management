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
from dotenv import load_dotenv
from apscheduler.schedulers.background import BlockingScheduler
import meraki_api
import daily_report
import monthly_report


'''
Method that triggers daily and monthly report creation and storage 
for all organizations related to an associated API key.
'''
def create_port_utilization_summaries():

    organizations = meraki_api.get_organizations()
    
    #Create daily utilization summaries
    daily_reports = daily_report.create_daily_utilization_reports(organizations)
    
    #Create aggregated monthly utilization summaries
    monthly_report.create_summarizing_utilization_reports(organizations, daily_reports)

    print('Data Sync finished')
    print('Next run tomorrow')


'''
Scheduler that executed the reports creation and synchronization once every day at a defined time.
'''
def scheduler():

    SCHEDULER_DAILY_HOUR = int(os.environ['SCHEDULER_DAILY_HOUR'])
    SCHEDULER_DAILY_MIN = int(os.environ['SCHEDULER_DAILY_MIN'])

    print("Job running every day at the same time.")
    print("Running at: " + str(SCHEDULER_DAILY_HOUR) + ":" + str(SCHEDULER_DAILY_MIN))

    scheduler = BlockingScheduler(timezone="Europe/Berlin")
    scheduler.add_job(create_port_utilization_summaries, "cron", day_of_week="mon-sun", hour=str(SCHEDULER_DAILY_HOUR), minute=str(SCHEDULER_DAILY_MIN))
    scheduler.start()
    

if __name__ == "__main__":

    load_dotenv()

    scheduler()

