# GVE_DevNet_Meraki_Google_User_Activity

## Contacts
* Rami Alfadel (ralfadel@cisco.com)
* Alvaro Escribano (alvescri@cisco.com)

## Solution Components
* Cisco Meraki Dashboard APIs
* Google-oAuth 
* Python
  - Python Module:
    - [Flask](https://flask.palletsprojects.com/)

## Solution Overview

This prototype shows a sample customized report of Meraki users' traffic activities by their email, that was used to sign in to the network using Google oAuth Sign-in.

![/IMAGES/Solution_overview.png](/IMAGES/Solution_overview.png)


## Installation/Configuration

### Requirements

- To use Meraki Dashboard APIs for this prototype, [enable API access](https://documentation.meraki.com/General_Administration/Other_Topics/Cisco_Meraki_Dashboard_API) as follows:
    - Organization > Settings > Dashboard API access
        - Enable Access to the Cisco Meraki Dashboard API
    ![/IMAGES/Enable_API_Access.png](/IMAGES/Enable_API_Access.png)

    - Generate an API key, to log in to the customized dashboard later on, as follows:
        - Go to **my profile** page(from top right corner) and generate a new API key:
        ![/IMAGES/Generate_api_key.png](/IMAGES/Generate_api_key.png)


- For traffic analytics to collect detailed analytics and show destination hostnames, [set "Traffic analysis" to "Detailed"](https://documentation.meraki.com/MS/Monitoring_and_Reporting/Switch_Traffic_Analytics) as follows:
    - Network-wide > General: 
        - Setting "Traffic analysis" to: "Detailed, collect destination hostnames
    ![/IMAGES/Enable_Detailed_Traffic_Analysis.png](/IMAGES/Enable_Detailed_Traffic_Analysis.png)

- This prototype is built to monitor traffic of users who logs in to the network using [Google Sign-in Splash page](https://documentation.meraki.com/MR/MR_Splash_Page/Google_Sign-In), that can be set up for any SSID as follows:
    - Wireless > Access Control:
        - SSID > Splash Page > Sign-on with "3rd party credintials"
            - Accepted Credintials: Google
        ![/IMAGES/SSID_Google_Auth.png](/IMAGES/SSID_Google_Auth.png)


### Getting Started   
 1. Choose a folder, then create a virtual environment:  
   ```python3 -m venv <name of environment>```

 2. Activate the created virtual environment:  
   ```source <name of environment>/bin/activate```

 3. Access the created virtual environment:  
   ```cd <name of environment>```

 4. Clone this Github repository into the virtual environment folder:  
   ```git clone [add github link here]```
   - For Github link: 
        In Github, click on the **Clone or download** button in the upper part of the page > click the **copy icon**  
        ![/IMAGES/giturl.png](/IMAGES/giturl.png)

 5. Access the folder **GVE_DevNet_Meraki_Google_User_Activity**:  
   ```cd GVE_DevNet_Meraki_Google_User_Activity```

 6. Install the solution requirements:  
   ```pip3 install -r requirements.txt```

 7. Initiate the Flask application settings:  
   ```export FLASK_APP=app.py```  
   ```export FLASK_ENV=development```

 8. Start the Flask application:  
   ```flask run```

 9. Open the hosted web page in your browser:  
    (Default: [localhost:9000](localhost:9000))


## Usage
- As you open the main page, you will be asked to login with a Meraki API Key:
    ![/IMAGES/login.png](/IMAGES/login.png)

- Fill in the required inputs to view traffic report of the selected information:
    ![/IMAGES/report_inputs.png](/IMAGES/report_inputs.png)

    - Organization
    - Network
    - Time Frame, which can be one of the following formats:
        - Time span: The number of the past days
        - Time range: Selected range of days
        - Specific day
    - User's email:
        - To get traffic report for a specific user, by entering the email used to login to the network
        - If empty, the report will display results for all the users

- To get traffic data grouped by **user**, click on: "Get Traffic Report **By User**"
    - Sample result:
    ![/IMAGES/sample_by_user.png](/IMAGES/sample_by_user.png)



- To get traffic data grouped by **application**, click on: "Get Traffic Report **By Application**"
    - Sample result:
    ![/IMAGES/sample_by_application.png](/IMAGES/sample_by_application.png)


## Notes

- The list of Meraki Dashboard APIs used in this prototype:
    - [Get Organizations](https://developer.cisco.com/meraki/api-v1/#!get-organizations)
    - [Get Organization Networks](https://developer.cisco.com/meraki/api-v1/#!get-organizations)
    - [Get Network Clients](https://developer.cisco.com/meraki/api-v1/#!get-network-clients)
    - [Get Network Splash Login Attempts](https://developer.cisco.com/meraki/api-v1/#!get-network-splash-login-attempts)
    - [Get Network Client Traffic History](https://developer.cisco.com/meraki/api-v1/#!get-network-client-traffic-history)

- Disclaimer: The timestamps results for the API call: [Get Network Client Traffic History](https://developer.cisco.com/meraki/api-v1/#!get-network-client-traffic-history) is showing timestamps hours and minutes as 00:00 for all records in the environment that was used for developing this use-case.



### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.