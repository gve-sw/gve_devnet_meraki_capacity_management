# gve_devnet_meraki_capacity_management

The purpose of this sample code is to show how the Meraki Dashboard APIs can be used to provide switch capacity management. 
The demo offers a custom dashboard with comprehensive monthly reports (for the last 6 months) describing the port utilization for all organizations related to a Meraki API key and its switches. Thereby, the current and maximum utilization information is calculated and displayed for the organization, network, stack and switch level. Detailed current and historical information is available for each port e.g. port usage history, last used within 24h, current status and more.
A separate background script requests the required data once a day from the Meraki Dashboard API, executes further calculation and summarization, and stored the results in a MongoDB. 

## Contacts
* Ramona Renner

## Solution Components
* Meraki Dashboard
* Meraki MS 
* Cloud MongoDB

## Workflow

![/IMAGES/migration_workflow.png](/IMAGES/workflow.png)

## High-Level Architecture

![/IMAGES/migration_workflow.png](/IMAGES/architecture.png)


## Installation

1. Make sure you have [Python 3.8.0](https://www.python.org/downloads/) and [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed

2. Create and activate a virtual environment for the project ([Instructions](https://docs.python.org/3/tutorial/venv.html)).

3. Access the created virtual environment folder
    ```
    cd [add name of virtual environment here] 
    ```

4. Clone this Github repository:  
  ```git clone [add github link here]```
  * For Github link: 
      In Github, click on the **Clone or download** button in the upper part of the page > click the **copy icon**  
      ![/IMAGES/giturl.png](/IMAGES/giturl.png)
  * Or simply download the repository as zip file using 'Download ZIP' button and extract it

5. Access the downloaded folder:  
    ```cd gve_devnet_meraki_capacity_management```

6. Install all dependencies:  
  ```pip install -r requirements.txt```

7. Reuse or set up a cloud **mongoDB account** and create a database and two collections: [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/getting-started/). Generate and note an associated MongoDB Data API key as described under [Read and Write with the Data API](https://www.mongodb.com/docs/atlas/api/data-api/#3.-send-a-data-api-request)

8. Follow the instructions under https://developer.cisco.com/meraki/api/#!authorization/obtaining-your-meraki-api-key to obtain the **Meraki API Token**. Save the token for a later step.

9. Fill in your variables in the **.env** file:      
      
  ```  
    MERAKI_API_TOKEN="[Add Meraki API key (see step 8)]"

    NON_UPLINK_TAG="[Add tag name of uplink ports on non-stack switches]"
    NON_STACK_PORT_TAG="[Add tag name for non-uplink and non-stack-dedicated ports on stack switches]" 

    MONGODB_BASE_URL="https://data.mongodb-api.com/app/data-rrppw/endpoint/data/v1"
    MONGO_DB_API_KEY="[Add MongoDB Data API key (see step 7)]"
    MONGO_DB_CLUSTER="[Add name of cluster]"
    MONGO_DB_NAME="[Add name of database within the cluster]"
    MONGO_DB_COLLECTION_NAME_DAILY="[Add name of the collection within the database for the daily reports]"
    MONGO_DB_COLLECTION_NAME_MONTLY="[Add name of the collection within the database for the monthly reports]"

    SCHEDULER_DAILY_HOUR="[Add hour value for daily report creation time of background script, e.g. 00]" 
    SCHEDULER_DAILY_MIN="[Add minute value for daily report creation time of background script, e.g. 30]"
  ```

  > Note: Mac OS hides the .env file in the finder by default. View the demo folder for example with your preferred IDE to make the file visible.   

  > Note: it takes some time until port traffic information is available via API. The execution of the script will happen at the choose time, but the requested time range will be increased by 30 min to prevent missing usage information - some overlapping information is thereby possible.

10. Start the backend script and wait for the first run to finish.   
  ```python3 report_scheduler.py```

11. Run the flask application 
  ```python3 app.py```

Assuming you kept the default parameters for starting the Flask application, the address to navigate to would be:
https://0.0.0.0:5001


## Screenshots

![/IMAGES/step1.png](/IMAGES/screenshot4.png)
![/IMAGES/step2.png](/IMAGES/screenshot5.png)
![/IMAGES/step3.png](/IMAGES/screenshot6.png)


## More Useful Resources

* Meraki Dashboard API documentation: https://developer.cisco.com/meraki/api-v1/
* MongoDB Data API documentation: https://www.mongodb.com/docs/atlas/api/data-api-resources/#std-label-data-api-resources


# Notice

* This sample code calculates the latest monthly report based on the organizations, networks, switches etc. available at the last script execution time. Thereby, it does not consider/include organization, devices etc. which were removed during the month.
* The "last used" value indicated that the port was used within 24h. The assigned date refers to the time the associated report was created. 
* The max values are referring to the maximum number of ports used within 24h for the associated month. Thereby, the ports were not necessarily used at the same time during a day.


### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.