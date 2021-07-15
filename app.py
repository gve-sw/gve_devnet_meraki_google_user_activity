"""Copyright (c) 2021 Cisco and/or its affiliates.

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

from flask import Flask, render_template, redirect, request, session
import requests
import json
import datetime

app = Flask(__name__)
app.secret_key = 'secret_key_here'


''' Meraki APIs functions '''


def getOrganization(token):
    """Function for gathering all Meraki Organizations
    Parameters:
    token (string): Meraki Dashboard API token

    Returns:
    dict: organization objects
    """

    url = "https://api.meraki.com/api/v1/organizations"
    payload = {}
    headers = {
        'X-Cisco-Meraki-API-Key': token
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status()

    return json.loads(response.text)


def getOrgNetworks(org_id, token):
    """Function for gathering all Meraki Networks of an Organization
    Parameters:
    org_id (string): Id for identifying organization
    token (string): Meraki Dashboard API token

    Returns:
    dict: organization networks
    """

    url = f"https://api.meraki.com/api/v1/organizations/{org_id}/networks"
    payload = {}
    headers = {
        'X-Cisco-Meraki-API-Key': token
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status()

    return json.loads(response.text)


def getLogin(nw_id, token, timeSpanSec):
    """Function for gathering login information from network clients
    Parameters:
    nw_id (string): Id for identifying a network
    token (string): Meraki Dashboard API token
    timeSpanSec (int): Timestamp in days to analyze, value can go from 0 to (3 months)

    Returns:
    dict: logins by clients and parameters
    """
    url = f"https://api.meraki.com/api/v1/networks/{nw_id}/splashLoginAttempts?timespan={timeSpanSec}"

    payload = {}
    headers = {
        'X-Cisco-Meraki-API-Key': token
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status()

    return json.loads(response.text)


def getLoggedClients(logins):
    """Function for cleaning non authorized user in the network, collecting useful info and skipping duplicates
    Parameters:
    logins (list): logins by clients and parameters

    Returns:
    dict: summarized list of authorized clients and parameters
    """
    loggedClients = []
    for login in logins:
        if login["authorization"] == "success":
            login_info = {}
            login_info["clientId"] = login["clientId"]
            login_info["name"] = login["name"]
            login_info["mail"] = login["login"]
            login_info["clientMac"] = login["clientMac"]
            if not login_info in loggedClients:
                loggedClients.append(login_info)
    return loggedClients


def getUserTraffic(nw_id, client_id, token):
    """Function for gathering traffic info of a specific client in a network
    Parameters:
    nw_id (string): Id for identifying a network
    client_id (string): Id for identifying a client
    token (string): Meraki Dashboard API token

    Returns:
    dict: traffic info objects
    """
    url = f"https://api.meraki.com/api/v1/networks/{nw_id}/clients/{client_id}/trafficHistory"
    payload = {}
    headers = {
        'X-Cisco-Meraki-API-Key': token
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status()

    return(json.loads(response.text))


def getUserTrafficByApp(traffic, startDatetime, endDatetime):
    """Function for re-arrenging and aggregating traffic information
    Parameters:
    traffic (list): traffic history of a user
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format

    Returns:
    dict: traffic grouped by app, destination and requests directed there
    """
    user_traffic = {}
    for record in traffic:
        tsDatetime = datetime.datetime.strptime(record["ts"], '%Y-%m-%dT%H:%M:%S.%fZ')
        if tsDatetime >= startDatetime and tsDatetime <= endDatetime:
            if "application" in record:
                if not record["application"] in user_traffic:
                    user_traffic[record["application"]] = {}
                if "destination" in record:
                    if not record["destination"] in user_traffic[record["application"]]:
                        user_traffic[record["application"]
                                    ][record["destination"]] = {}
                        user_traffic[record["application"]
                                    ][record["destination"]]["ts"] = {}
                        user_traffic[record["application"]
                                    ][record["destination"]]["ts"][record["ts"]] = record["activeSeconds"]
                        user_traffic[record["application"]
                                     ][record["destination"]]["occurrences"] = len(user_traffic[record["application"]][record["destination"]]["ts"])
    return user_traffic


def getSingleClient(nw_id, client_id, token):
    """Function for gathering info on a specific Meraki client in a network
    Parameters:
    nw_id (string): Id for identifying a network
    client_id (string): Id for identifying a client
    token (string): Meraki Dashboard API token

    Returns:
    dict: client object with parameters
    """

    url = f"https://api.meraki.com/api/v1/networks/{nw_id}/clients/{client_id}"
    payload = {}
    headers = {
        'X-Cisco-Meraki-API-Key': token
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status()

    return(json.loads(response.text))


def getAllTraffic(token, startDatetime, endDatetime):
    """Function for gathering client traffic information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format

    Returns:
    dict: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}

    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')

    # get specific org
    orgs = getOrganization(token)

    for org in orgs:
        app_traffic[org["name"]] = {}
        # get specific network
        networks = getOrgNetworks(org["id"], token)

        for nw in networks:
            app_traffic[org["name"]][nw["name"]] = {}
            # get login clients info
            logins = getLogin(nw["id"], token, startTimeSpanSec)
            clients_info = (getLoggedClients(logins))

            # inspect traffic history for each log client and add other relevant information
            user_app_traffic = {}
            for info in clients_info:
                if not info["mail"] in app_traffic[org["name"]][nw["name"]]:
                    app_traffic[org["name"]][nw["name"]][info["mail"]] = []

                user_traffic = getUserTraffic(
                    nw["id"], info["clientId"], token)
                user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)
                client = getSingleClient(nw["id"], info["clientId"], token)
                user_history = {}

                user_history["clientId"] = info["clientId"]
                user_history["name"] = info["name"]
                user_history["clientMac"] = info["clientMac"]

                user_history["description"] = client["description"]
                user_history["ip"] = client["ip"]
                user_history["ip6"] = client["ip6"]
                user_history["ssid"] = client["ssid"]
                user_history["lastSeen"] = client["lastSeen"]
                user_history["os"] = client["os"]
                if "usage" in client:
                    user_history["usage"] = client["usage"]
                user_history["status"] = client["status"]

                user_history["traffic"] = user_app_traffic

                app_traffic[org["name"]][nw["name"]
                                         ][info["mail"]].append(user_history)
    return app_traffic



def getAllTrafficByApp(token, startDatetime, endDatetime):
    """Function for gathering client traffic information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format


    Returns:
    list: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}


    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')
    

    # get specific org
    orgs = getOrganization(token)

    for org in orgs:
        app_traffic[org["name"]] = {}
        # get specific network
        networks = getOrgNetworks(org["id"], token)

        for nw in networks:
            app_traffic[org["name"]][nw["name"]] = {}
            # get login clients info

            logins = getLogin(nw["id"], token, startTimeSpanSec)

            clients_info = (getLoggedClients(logins))

            # inspect traffic history for each log client and add other relevant information
            user_app_traffic = {}
            for info in clients_info:
                user_traffic = getUserTraffic(nw["id"], info["clientId"], token)

                user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)

                for app in user_app_traffic:
                    
                    if not app in app_traffic[org["name"]][nw["name"]]:
                        app_traffic[org["name"]][nw["name"]][app] = {}
                    if not info["mail"] in app_traffic[org["name"]][nw["name"]][app]:
                        app_traffic[org["name"]][nw["name"]][app][info["mail"]] = []

                    
                    client = getSingleClient(nw["id"], info["clientId"], token)
                    user_history = {}

                    user_history["clientId"] = info["clientId"]
                    user_history["name"] = info["name"]
                    user_history["clientMac"] = info["clientMac"]

                    user_history["description"] = client["description"]
                    user_history["ip"] = client["ip"]
                    user_history["ip6"] = client["ip6"]
                    user_history["ssid"] = client["ssid"]
                    user_history["lastSeen"] = client["lastSeen"]
                    user_history["os"] = client["os"]
                    if "usage" in client:
                        user_history["usage"] = client["usage"]
                    user_history["status"] = client["status"]

                    user_history["traffic"] = user_app_traffic[app]

                    app_traffic[org["name"]][nw["name"]][app][info["mail"]].append(user_history)
    return app_traffic




def getOrgTraffic(token, startDatetime, endDatetime, org_id):

    """Function for gathering client traffic within an organization information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format
    org_id (string): organization id to gather client traffic from

    Returns:
    dict: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}

    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')

    # Getting org's name
    orgs = getOrganization(token)
    org_name = None
    for org in orgs:
        if org["id"] == org_id:
            org_name = org["name"]
    if org_name == None:
        raise ValueError("Organization Name not found in Meraki environment")

    app_traffic[org_name] = {}
    # get org networks
    networks = getOrgNetworks(org_id, token)
    for nw in networks:
        app_traffic[org_name][nw["name"]] = {}
        # get login clients info
        logins = getLogin(nw["id"], token, startTimeSpanSec)
        clients_info = (getLoggedClients(logins))

        # inspect traffic history for each log client and add other relevant information
        user_app_traffic = {}
        for info in clients_info:
            if not info["mail"] in app_traffic[org_name][nw["name"]]:
                app_traffic[org_name][nw["name"]][info["mail"]] = []

            user_traffic = getUserTraffic(nw["id"], info["clientId"], token)
            user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)
            client = getSingleClient(nw["id"], info["clientId"], token)
            user_history = {}

            user_history["clientId"] = info["clientId"]
            user_history["name"] = info["name"]
            user_history["clientMac"] = info["clientMac"]

            user_history["description"] = client["description"]
            user_history["ip"] = client["ip"]
            user_history["ip6"] = client["ip6"]
            user_history["ssid"] = client["ssid"]
            user_history["lastSeen"] = client["lastSeen"]
            user_history["os"] = client["os"]
            if "usage" in client:
                user_history["usage"] = client["usage"]
            user_history["status"] = client["status"]

            user_history["traffic"] = user_app_traffic

            app_traffic[org_name][nw["name"]
                                  ][info["mail"]].append(user_history)
    return app_traffic


def getOrgTrafficByApp(token, startDatetime, endDatetime, org_id):
    """Function for gathering client traffic within an organization information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format
    org_id (string): organization id to gather client traffic from


    Returns:
    list: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}
    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')

    # Getting org's name
    orgs = getOrganization(token)
    org_name = None
    for org in orgs:
        if org["id"] == org_id:
            org_name = org["name"]
    if org_name == None:
        raise ValueError("Organization Name not found in Meraki environment")

    app_traffic[org_name] = {}
    # get org networks
    networks = getOrgNetworks(org_id, token)
    for nw in networks:
        app_traffic[org_name][nw["name"]] = {}
        # get login clients info
        logins = getLogin(nw["id"], token, startTimeSpanSec)
        clients_info = (getLoggedClients(logins))

        # inspect traffic history for each log client and add other relevant information
        user_app_traffic = {}
        for info in clients_info:
            user_traffic = getUserTraffic(nw["id"], info["clientId"], token)
            user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)
            for app in user_app_traffic:
                
                if not app in app_traffic[org_name][nw["name"]]:
                    app_traffic[org_name][nw["name"]][app] = {}
                if not info["mail"] in app_traffic[org_name][nw["name"]][app]:
                    app_traffic[org_name][nw["name"]][app][info["mail"]] = []

                
                client = getSingleClient(nw["id"], info["clientId"], token)
                user_history = {}

                user_history["clientId"] = info["clientId"]
                user_history["name"] = info["name"]
                user_history["clientMac"] = info["clientMac"]

                user_history["description"] = client["description"]
                user_history["ip"] = client["ip"]
                user_history["ip6"] = client["ip6"]
                user_history["ssid"] = client["ssid"]
                user_history["lastSeen"] = client["lastSeen"]
                user_history["os"] = client["os"]
                if "usage" in client:
                    user_history["usage"] = client["usage"]
                user_history["status"] = client["status"]

                user_history["traffic"] = user_app_traffic[app]

                app_traffic[org_name][nw["name"]][app][info["mail"]].append(user_history)
    return app_traffic



def getNwTraffic(token, startDatetime, endDatetime, org_id, nw_id):
    """Function for gathering client traffic within an organization information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format
    org_id (string): organization id to gather client traffic from
    nw_id (string): network id to gather client traffic from

    Returns:
    dict: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}
    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')

    # Getting org name
    orgs = getOrganization(token)
    org_name = None
    for org in orgs:
        if org["id"] == org_id:
            org_name = org["name"]
    if org_name == None:
        raise ValueError("Organization ID not found in Meraki environment")

    app_traffic[org_name] = {}

    # Getting network name
    networks = getOrgNetworks(org_id, token)
    nw_name = None
    for nw in networks:
        if nw["id"] == nw_id:
            nw_name = nw["name"]
    if nw_name == None:
        raise ValueError("Network ID not found in Meraki environment")

    app_traffic[org_name][nw_name] = {}
    # get login clients info
    logins = getLogin(nw_id, token, startTimeSpanSec)
    clients_info = (getLoggedClients(logins))

    # inspect traffic history for each log client and add other relevant information
    user_app_traffic = {}
    for info in clients_info:
        if not info["mail"] in app_traffic[org_name][nw_name]:
            app_traffic[org_name][nw_name][info["mail"]] = []

        user_traffic = getUserTraffic(nw_id, info["clientId"], token)
        user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)
        client = getSingleClient(nw_id, info["clientId"], token)
        user_history = {}

        user_history["clientId"] = info["clientId"]
        user_history["name"] = info["name"]
        user_history["clientMac"] = info["clientMac"]

        user_history["description"] = client["description"]
        user_history["ip"] = client["ip"]
        user_history["ip6"] = client["ip6"]
        user_history["ssid"] = client["ssid"]
        user_history["lastSeen"] = client["lastSeen"]
        user_history["os"] = client["os"]
        if "usage" in client:
            user_history["usage"] = client["usage"]
        user_history["status"] = client["status"]

        user_history["traffic"] = user_app_traffic

        app_traffic[org_name][nw_name][info["mail"]].append(user_history)
    return app_traffic


def getNwTrafficByApp(token, startDatetime, endDatetime, org_id, nw_id):
    """Function for gathering client traffic within an organization information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format
    org_id (string): organization id to gather client traffic from
    nw_id (string): network id to gather client traffic from

    Returns:
    list: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}

    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')


    # Getting org name
    orgs = getOrganization(token)
    org_name = None
    for org in orgs:
        if org["id"] == org_id:
            org_name = org["name"]
    if org_name == None:
        raise ValueError("Organization ID not found in Meraki environment")

    app_traffic[org_name] = {}

    # Getting network name
    networks = getOrgNetworks(org_id, token)
    nw_name = None
    for nw in networks:
        if nw["id"] == nw_id:
            nw_name = nw["name"]
    if nw_name == None:
        raise ValueError("Network ID not found in Meraki environment")

    app_traffic[org_name][nw_name] = {}
    # get login clients info
    logins = getLogin(nw_id, token, startTimeSpanSec)
    clients_info = (getLoggedClients(logins))

    # inspect traffic history for each log client and add other relevant information
    user_app_traffic = {}
    for info in clients_info:
        user_traffic = getUserTraffic(nw_id, info["clientId"], token)
        user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)
        for app in user_app_traffic:
            
            if not app in app_traffic[org_name][nw_name]:
                app_traffic[org_name][nw_name][app] = {}
            if not info["mail"] in app_traffic[org_name][nw_name][app]:
                app_traffic[org_name][nw_name][app][info["mail"]] = []

            
            client = getSingleClient(nw_id, info["clientId"], token)
            user_history = {}

            user_history["clientId"] = info["clientId"]
            user_history["name"] = info["name"]
            user_history["clientMac"] = info["clientMac"]

            user_history["description"] = client["description"]
            user_history["ip"] = client["ip"]
            user_history["ip6"] = client["ip6"]
            user_history["ssid"] = client["ssid"]
            user_history["lastSeen"] = client["lastSeen"]
            user_history["os"] = client["os"]
            if "usage" in client:
                user_history["usage"] = client["usage"]
            user_history["status"] = client["status"]

            user_history["traffic"] = user_app_traffic[app]

            app_traffic[org_name][nw_name][app][info["mail"]].append(user_history)
    return app_traffic

def getSingleGoogleUserTraffic(token, startDatetime, endDatetime, mail):
    """Function for gathering client traffic information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format

    Returns:
    dict: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}

    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')

    # get specific org
    orgs = getOrganization(token)

    for org in orgs:
        app_traffic[org["name"]] = {}
        # get specific network
        networks = getOrgNetworks(org["id"], token)

        for nw in networks:
            app_traffic[org["name"]][nw["name"]] = {}
            # get login clients info
            logins = getLogin(nw["id"], token, startTimeSpanSec)
            clients_info = (getLoggedClients(logins))

            # inspect traffic history for each log client and add other relevant information
            user_app_traffic = {}
            
            for info in clients_info:
                if info["mail"] == mail:
                    if not info["mail"] in app_traffic[org["name"]][nw["name"]]:
                        app_traffic[org["name"]][nw["name"]][info["mail"]] = []

                    user_traffic = getUserTraffic(
                        nw["id"], info["clientId"], token)
                    user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)
                    client = getSingleClient(nw["id"], info["clientId"], token)
                    user_history = {}

                    user_history["clientId"] = info["clientId"]
                    user_history["name"] = info["name"]
                    user_history["clientMac"] = info["clientMac"]

                    user_history["description"] = client["description"]
                    user_history["ip"] = client["ip"]
                    user_history["ip6"] = client["ip6"]
                    user_history["ssid"] = client["ssid"]
                    user_history["lastSeen"] = client["lastSeen"]
                    user_history["os"] = client["os"]
                    if "usage" in client:
                        user_history["usage"] = client["usage"]
                    user_history["status"] = client["status"]

                    user_history["traffic"] = user_app_traffic

                    app_traffic[org["name"]][nw["name"]
                                            ][info["mail"]].append(user_history)
    return app_traffic


def getSingleGoogleUserTrafficByApp(token, startDatetime, endDatetime, mail):
    """Function for gathering client traffic information and ordering it into a dictionary
    Parameters:
    token (list): Meraki API token
    startDatetime (datetime): start of the timespan in datetime format
    endDatetime (datetime): start of the timespan in datetime format
    mail (string): google user email

    Returns:
    list: extensive dictionary with traffic information grouped by organization > network > user_mail
    """
    app_traffic = {}

    startTimeSpanSec = int((datetime.datetime.now() - startDatetime).total_seconds())
    if startTimeSpanSec >= 2592000 or startTimeSpanSec < 0 or endDatetime > datetime.datetime.now():
        raise ValueError(
            'TimeSpan cannot be larger than 1 month or lower than 0')
    
    # get specific org
    orgs = getOrganization(token)

    for org in orgs:
        app_traffic[org["name"]] = {}
        # get specific network
        networks = getOrgNetworks(org["id"], token)

        for nw in networks:
            app_traffic[org["name"]][nw["name"]] = {}
            # get login clients info
            logins = getLogin(nw["id"], token, startTimeSpanSec)
            clients_info = (getLoggedClients(logins))

            # inspect traffic history for each log client and add other relevant information
            user_app_traffic = {}
            for info in clients_info:
                if info["mail"] == mail:
                    user_traffic = getUserTraffic(nw["id"], info["clientId"], token)
                    user_app_traffic = getUserTrafficByApp(user_traffic, startDatetime, endDatetime)
                    for app in user_app_traffic:
                        
                        if not app in app_traffic[org["name"]][nw["name"]]:
                            app_traffic[org["name"]][nw["name"]][app] = {}
                        if not info["mail"] in app_traffic[org["name"]][nw["name"]][app]:
                            app_traffic[org["name"]][nw["name"]][app][info["mail"]] = []

                        
                        client = getSingleClient(nw["id"], info["clientId"], token)
                        user_history = {}

                        user_history["clientId"] = info["clientId"]
                        user_history["name"] = info["name"]
                        user_history["clientMac"] = info["clientMac"]

                        user_history["description"] = client["description"]
                        user_history["ip"] = client["ip"]
                        user_history["ip6"] = client["ip6"]
                        user_history["ssid"] = client["ssid"]
                        user_history["lastSeen"] = client["lastSeen"]
                        user_history["os"] = client["os"]
                        if "usage" in client:
                            user_history["usage"] = client["usage"]
                        user_history["status"] = client["status"]

                        user_history["traffic"] = user_app_traffic[app]

                        app_traffic[org["name"]][nw["name"]][app][info["mail"]].append(user_history)
    return app_traffic


''' Flask application routes '''

@app.route('/')
# Default route
def default():
    return redirect('/login')


@app.route('/login')
# Login route
def login():
    return render_template('login.html')


@app.route('/verify_login', methods=['POST'])
# Verify login route
def verify_login():
    api_key = request.form.get('api_key')
    session['api_key'] = api_key
    print('New login - api_key:' + str(session['api_key']))
    return redirect('/context')


@app.route('/context')
# Context route
def context():
    # Only showng last 4 characters of the API key
    hidden_api_key = '(...' + session['api_key'][-4:] + ')'

    # Getting the list of organizations
    orgs = getOrganization(session['api_key'])

    if(orgs):
        all_option = {'id': 'All', 'name': 'All'}
        orgs.insert(0, all_option)

    return render_template('context.html', hidden_api_key=hidden_api_key, orgs=orgs)


@app.route('/logout')
def logout():
    print('Logout - api_key:' + str(session['api_key']))
    session.pop('api_key')
    return redirect('/login')


@app.route('/assign_org', methods=['POST'])
# Assign org route
def assign_org():
    session['selected_org'] = request.form.get('selected_org')

    print('Getting networks for org: ' + session['selected_org'])
    networks = []

    if(session['selected_org'] != 'All'):
        networks = getOrgNetworks(session['selected_org'], session['api_key'])

    all_option = {'id': 'All', 'name': 'All'}
    networks.insert(0, all_option)

    return json.dumps(networks)


@app.route('/assign_network', methods=['POST'])
# Assign network route
def assign_network():
    session['selected_network'] = request.form.get('selected_network')

    print('Getting traffic for network: ' + session['selected_network'])

    return ''


@app.route('/assign_time', methods=['POST'])
# Assign time route
def assign_time():
    session['start_date'] = request.form.get('start_date')
    session['end_date'] = request.form.get('end_date')
    print('Getting traffic for selected_time_span, from: ' +
          session['start_date'] + ' to: ' + session['end_date'])

    return ''


@app.route('/assign_user', methods=['POST'])
# Assign user route
def assign_user():
    session['selected_user'] = request.form.get('selected_user')
    print('Getting traffic for selected_user: ' +
          session['selected_user'])

    return ''


@app.route('/traffic_by_user')
# Traffic results by user route
def traffic_by_user():
    # Only showng last 4 characters of the API key
    hidden_api_key = '(...' + session['api_key'][-4:] + ')'

    # Changing times to datetime variables
    startDatetime = datetime.datetime.strptime(session['start_date'], '%Y-%m-%d')
    endDatetime = datetime.datetime.strptime(session['end_date'], '%Y-%m-%d')


    #  If a user was selected
    if(session['selected_user'] != ''):
        traffic = getSingleGoogleUserTraffic(session['api_key'],
                                             startDatetime,
                                             endDatetime,
                                             session['selected_user']
                                             )
    else:
        # If "All" orgs was selected
        if(session['selected_org'] == 'All'):
            # Checking if user was selected or getting all users
            traffic = getAllTraffic(session['api_key'],
                                    startDatetime,
                                    endDatetime
                                    )
        # Else if a specific org was selected
        else:
            if(session['selected_network'] == 'All'):
                traffic = getOrgTraffic(session['api_key'],
                                        startDatetime,
                                        endDatetime,
                                        session['selected_org']
                                        )
            else:
                traffic = getNwTraffic(session['api_key'],
                                    startDatetime,
                                    endDatetime,
                                    session['selected_org'],
                                    session['selected_network']
                                    )

    # Saving results to the file: result.json
    with open("result.json", "w") as f:
        json.dump(traffic, f, indent=3)

    # Dumping python dictionary as JSON for the front end
    traffic = json.dumps(traffic)

    return render_template('traffic_by_user.html', hidden_api_key=hidden_api_key, traffic=traffic)

@app.route('/traffic_by_app')
# Traffic results by app route
def traffic_by_app():
    # Only showng last 4 characters of the API key
    hidden_api_key = '(...' + session['api_key'][-4:] + ')'

    # Changing times to datetime variables
    startDatetime = datetime.datetime.strptime(
        session['start_date'], '%Y-%m-%d')
    endDatetime = datetime.datetime.strptime(session['end_date'], '%Y-%m-%d')

    #  If a user was selected
    if(session['selected_user'] != ''):
        traffic = getSingleGoogleUserTrafficByApp(session['api_key'],
                                             startDatetime,
                                             endDatetime,
                                             session['selected_user']
                                             )
    else:
        # If "All" orgs was selected
        if(session['selected_org'] == 'All'):
            # Checking if user was selected or getting all users
            traffic = getAllTrafficByApp(session['api_key'],
                                    startDatetime,
                                    endDatetime
                                    )
        # Else if a specific org was selected
        else:
            if(session['selected_network'] == 'All'):
                traffic = getOrgTrafficByApp(session['api_key'],
                                        startDatetime,
                                        endDatetime,
                                        session['selected_org']
                                        )
            else:
                traffic = getNwTrafficByApp(session['api_key'],
                                       startDatetime,
                                       endDatetime,
                                       session['selected_org'],
                                       session['selected_network']
                                       )

    # Saving results to the file: result.json
    with open("result_by_app.json", "w") as f:
        json.dump(traffic, f, indent=3)

    # Dumping python dictionary as JSON for the front end
    traffic = json.dumps(traffic)

    return render_template('traffic_by_app.html', hidden_api_key=hidden_api_key, traffic=traffic)

# ''' Starting Flask web application '''
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9000, debug=False, threaded=True)
