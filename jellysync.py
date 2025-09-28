# #############################################################################
# Origional Author: CobayeGunther
# Creation Date: 26/04/2020
# Updated 25/02/2025 by Ozymandyaz, renamed JellySync
#
# Description: 	python script to recreate users from emby to jellyfin 
#				and migrate their watched content 
#
# Origional Github Source: https://github.com/CobayeGunther/Emby2Jelly
#
# #############################################################################


import json
import requests
import urllib.parse
from configobj import ConfigObj
import os
import time
import sys, getopt
import getpass
import argparse

destinationUserDb = {}
destinationUserPw = {}


def getConfig(path, section, option, type):
    config = ConfigObj(path)
    if type == "str":
        return config[section][option]
    elif type == "int":
        return config[section].as_int(option)
    elif type == "bool":
        print("bool : ", section, option, config[section].as_bool(option))
        result = config[section].as_bool(option)
        if result:
            return 1
        else:
            return 0


def exist(path):
    return os.path.exists(path)


def createConfig(path):
    """
    Create a config file
    """
    config = ConfigObj(path)
    SourceSection = {
        "SOURCE_APIKEY": "aaaabbbbbbbcccccccccccccdddddddd",
        "SOURCE_URLBASE": "http://127.0.0.1:8096/source/",
        "IGNORE_USERS":   "User1"
    }
    config["Source"] = SourceSection

    DestinationSection = {
        "DEST_APIKEY": "eeeeeeeeeeeeeeeffffffffffffffffggggggggg",
        "DEST_URLBASE": "http://127.0.0.1:8096/destinationfin/",
    }
    config["Destination"] = DestinationSection

    config.write()


def getTokenForUser(server_url, username, password):
    auth_data = {"username": username, "Pw": password}
    headers = {}
    authorization = 'MediaBrowser Client="other", Device="my-script", DeviceId="some-unique-id", Version="0.0.0"'
    headers["Authorization"] = authorization
    r = requests.post(
        server_url + "/Users/AuthenticateByName", headers=headers, json=auth_data
    )
    token = r.json().get("AccessToken")
    user_id = r.json().get("User").get("Id")
    headers["Authorization"] = f'{authorization}, Token="{token}"'
    return token


def source(selectedUsers):
    # global MigrationData
    global SOURCE_APIKEY
    global SOURCE_URLBASE
    if SOURCE_APIKEY == None or SOURCE_URLBASE == None:
        if not exist(path):
            createConfig(path)
            print(
                "No config:\nif you are in docker, update your env. variables\nif not please see the README and complete the jellysync.ini\n thank you"
            )
            sys.exit()
        SOURCE_APIKEY = getConfig(path, "Source", "SOURCE_APIKEY", "str")
        SOURCE_URLBASE = getConfig(path, "Source", "SOURCE_URLBASE", "str")
    else:
        print("using env variables for source : {0}".format(SOURCE_URLBASE))
    SOURCE_HEADERS = {"accept": "application/json", "api_key": "{0}".format(SOURCE_APIKEY)}
    users = dict()

    def emby_get_users_list(SOURCE_APIKEY, SOURCE_URLBASE, SOURCE_HEADERS):

        api_url = "{0}Users?api_key={1}".format(SOURCE_URLBASE, SOURCE_APIKEY)

        response = requests.get(api_url, headers=SOURCE_HEADERS)

        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))
        else:
            return "error : " + json.loads(response.content.decode("utf-8"))

    def get_watched_status():
        # global MigrationData
        # lister les utilsateurs et leur ID respectives
        i = 0
        userCount = 0
        print("\033[92mSource has {0} Users\033[00m".format(userTotal))
        UserPlaylist = {}
        for user in users:
            userCount += 1
            if (user["Name"] in selectedUsers) and (user["Name"] is not None):
                MigrationData[user["Name"]] = []
                PlayedItem = 0
                # print("{0} ({2} / {3}) : {1}".format(user['Name'],user['Id'],userCount,userTotal))
                print(f"{user['Name']} ({userCount} / {userTotal}) : {user['Id']}")

                api_urls = {
                    f"{SOURCE_URLBASE}Users/{user['Id']}/Items?Filters=IsPlayed&IncludeItemTypes=Movie,Episode&Recursive=True&api_key={SOURCE_APIKEY}",
                    f"{SOURCE_URLBASE}Users/{user['Id']}/Items?Filters=IsResumable&IncludeItemTypes=Movie,Episode&Recursive=True&api_key={SOURCE_APIKEY}",
                }
                for api_url in api_urls:
                    SOURCE_HEADERS_Auth = {
                        "accept": "application/json",
                        "api_key": f"{SOURCE_APIKEY}",
                    }
                    response = requests.get(api_url, headers=SOURCE_HEADERS_Auth)
                    if response.status_code == 200:
                        UserPlaylist = json.loads(response.content.decode("utf-8"))
                        for item in UserPlaylist["Items"]:
                            MigrationMedia = {
                                "Type": "",
                                "SourceId": "",
                                "DestinationId": "",
                                "Name": "",
                                "ProviderIds": {},
                                "UserData": {},
                            }
                            PlayedItem += 1
                            api_url = "{0}Users/{1}/Items/{3}?api_key={2}".format(
                                SOURCE_URLBASE, user["Id"], SOURCE_APIKEY, item["Id"]
                            )
                            SOURCE_HEADERS_Auth = {
                                "accept": "application/json",
                                "api_key": "{0}".format(SOURCE_APIKEY),
                            }
                            response = requests.get(api_url, headers=SOURCE_HEADERS_Auth)

                            if response.status_code == 200:
                                itemDto = json.loads(response.content.decode("utf-8"))
                                MigrationMedia["Type"] = item["Type"]
                                MigrationMedia["SourceId"] = item["Id"]
                                MigrationMedia["DestinationId"] = ""
                                MigrationMedia["Name"] = item["Name"]
                                itemDto["ProviderIds"].pop("sonarr", None)
                                MigrationMedia["ProviderIds"] = itemDto["ProviderIds"]
                                MigrationData[user["Name"]].append(MigrationMedia)
                                DEST_HEADERS_movie = {
                                    "Content-Type": "application/json",
                                    "Authorization": 'MediaBrowser Token="{0}"'.format(
                                        SOURCE_APIKEY
                                    ),
                                }
                                api_url2 = (
                                    "{0}UserItems/{2}/UserData?userId={1}".format(
                                        SOURCE_URLBASE, user["Id"], item["Id"]
                                    )
                                )
                                response2 = requests.get(
                                    api_url2, headers=DEST_HEADERS_movie
                                )
                                if response.status_code == 200:
                                    itemDto = json.loads(
                                        response2.content.decode("utf-8")
                                    )
                                    MigrationMedia["UserData"] = itemDto
                    else:
                        print(
                            "\033[91merror : {0}  =  {1}\033[00m".format(
                                response.status_code, response.content.decode("utf-8")
                            )
                        )
        print("\n\n\033[92m##### SourceSync Done #####\033[00m\n\n")

    users = emby_get_users_list(SOURCE_APIKEY, SOURCE_URLBASE, SOURCE_HEADERS)
    if selectedUsers == []:
        ignoreUsers = getConfig(path, "Source", "IGNORE_USERS", "str")
        if ignoreUsers != None:
            ignoreUsers = ignoreUsers.split(",")
        for user in users:
            # if user['Name'] != 'admin' and user['Name'] != 'Mark2':
            if user["Name"] not in ignoreUsers:
                selectedUsers.append(user["Name"])

    userTotal = len(users)
    get_watched_status()


def destination(newUser_pw):
    reportStr = ""
    report = {}
    global DEST_APIKEY
    global DEST_URLBASE
    if DEST_APIKEY == None or DEST_URLBASE == None:
        if not exist(path):
            createConfig(path)
            print(
                "No config:\nif you are in docker, update your env. variables\nif not please see the README and complete the jellysync.ini\n thank you"
            )
            sys.exit()
        DEST_APIKEY = getConfig(path, "Destination", "DEST_APIKEY", "str")
        DEST_URLBASE = getConfig(path, "Destination", "DEST_URLBASE", "str")
    else:
        print("using env variables for Destination : {0}".format(DEST_URLBASE))
    DEST_HEADERS = {
        "accept": "application/json",
        "api_key": "{0}".format(DEST_APIKEY),
    }

    def destination_get_users_list():
        api_url = "{0}Users?api_key={1}".format(DEST_URLBASE, DEST_APIKEY)

        response = requests.get(api_url, headers=DEST_HEADERS)
        if response.status_code == 200:
            # print(json.loads(response.content.decode('utf-8')))
            return json.loads(response.content.decode("utf-8"))
        else:
            return "error : " + json.loads(response.content.decode("utf-8"))

    def compare_users():

        print("\033[96mDestination has {0} Users\033[00m".format(userTotal))

        nonlocal DestinationUsersIdDict
        nonlocal report

        report["users"] = ""
        DestinationUsersIdDict["Name"] = 0
        embyList = []
        destinationList = []
        for eUser in MigrationData:
            embyList.append(eUser)
        for jUser in destinationUsers:
            DestinationUsersIdDict[jUser["Name"]] = jUser["Id"]
            ## Destination does not accept char space in userNames
        for eUser in MigrationData:
            if eUser.replace(" ", "_") in DestinationUsersIdDict.keys():
                print(
                    "Destination already knows {0} (Id {1})".format(
                        eUser.replace(" ", "_"),
                        DestinationUsersIdDict[eUser.replace(" ", "_")],
                    )
                )
                report["users"] += "{0} (Source) is  {1} (Destination)\n".format(
                    eUser, eUser.replace(" ", "_")
                )
                destinationUserPw[eUser.replace(" ", "_")] = set_pw(eUser.replace(" ", "_"), None)
            else:
                print("{0} ..  Creating".format(eUser))
                ##creating user account
                DEST_HEADERS_usercreate = {
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "api_key": "{0}".format(DEST_APIKEY),
                }

                api_url = "{0}Users/New?&api_key={1}".format(
                    DEST_URLBASE, DEST_APIKEY
                )
                userData = {
                        "name": eUser.replace(" ", "_"),
                        "Password": set_pw(eUser.replace(" ", "_"), newUser_pw),
                    }

                response = requests.post(
                    api_url,
                    headers=DEST_HEADERS_usercreate,
                    data=json.dumps(userData),
                )
                if response.status_code == 200:
                    print("{0}  Created".format(eUser.replace(" ", "_")))
                    report["users"] += "{0} Created on Destination".format(
                        eUser, eUser.replace(" ", "_")
                    )
                    destinationUserPw[eUser.replace(" ", "_")] = newUser_pw

                else:
                    print(
                        "{1} -- {0}\n\n".format(
                            response.content.decode("utf-8"), response.status_code
                        )
                    )
        # uptade the destination Users in case we created one

    def get_userLibrary(user):
        user["Name"].replace("_", " ")
        print("getting destination DB for {0}".format(user["Name"]))
        api_url = "{0}Users/{2}/Items?Recursive=True&Fields=ProviderIds&IncludeItemTypes=Episode,Movie&api_key={1}".format(
            DEST_URLBASE, DEST_APIKEY, user["Id"]
        )
        DEST_HEADERS_movie = {
            "accept": "application/json",
            "api_key": "{0}".format(DEST_APIKEY),
        }
        response = requests.get(api_url, headers=DEST_HEADERS_movie)
        if response.status_code == 200:
            # print(json.loads(response.content.decode('utf-8')))
            debugFile = open("debug.json", "w")
            debugFile.write(json.dumps(json.loads(response.content.decode("utf-8"))))
            return json.loads(response.content.decode("utf-8"))
        else:
            print("error : " + response.content.decode("utf-8"))

    def send_watchedStatus():
        nonlocal report

        for user in destinationUsers:

            if (user["Name"].replace("_", " ") in selectedUsers) and (
                user["Name"] is not None
            ):
                report[user["Name"].replace("_", " ")] = {}
                report[user["Name"].replace("_", " ")]["ok"] = 0
                report[user["Name"].replace("_", " ")]["nok"] = []
                report[user["Name"].replace("_", " ")]["tosend"] = 0

                toSend = len(MigrationData[user["Name"].replace("_", " ")])
                report[user["Name"].replace("_", " ")]["tosend"] = toSend
                ok = 0
                nok = 0
                for MigrationMedia in MigrationDataFinal[
                    user["Name"].replace("_", " ")
                ]:
                    if MigrationMedia["DestinationId"] is not None:
                        authToken = getTokenForUser(DEST_URLBASE, user["Name"], destinationUserPw[user["Name"].replace("_", " ") ])
                        DEST_HEADERS_movie = {
                            "Content-Type": "application/json",
                            "Accepts": "application/json",
                            "Authorization": 'MediaBrowser Token="{0}"'.format(
                                authToken
                            ),
                        }
                        api_url = "{0}UserItems/{2}/UserData?userId={1}".format(
                            DEST_URLBASE, user["Id"], MigrationMedia["DestinationId"]
                        )
                        body = json.dumps(
                            MigrationMedia["UserData"], separators=(",", ":")
                        )
                        response = requests.post(
                            api_url, headers=DEST_HEADERS_movie, data=body
                        )
                        if response.status_code == 200:
                            ok += 1
                            report[user["Name"].replace("_", " ")]["ok"] += 1
                            print(
                                "\033[92mOK ! {2}/{3} - {0} has been seen by {1}\n\033[00m".format(
                                    MigrationMedia["Name"], user["Name"], ok, toSend
                                )
                            )
                            # print(response.json())
                        else:
                            print(
                                "\033[91merror : {0}\033[00m".format(
                                    response.content.decode("utf-8")
                                )
                            )
                            print("Status Code", response.status_code)
                            # print("JSON Response ", response.json())
                    else:
                        nok += 1
                        report[user["Name"].replace("_", " ")]["nok"].append(
                            MigrationMedia
                        )
                        print(
                            "Couldn't find Id for {0}\n{1}".format(
                                MigrationMedia["Name"], MigrationMedia["ProviderIds"]
                            )
                        )

    def search_byName(MigrationMedia, Library):

        for destination_movie in Library["Items"]:
            if destination_movie.get("Name") == MigrationMedia["Name"]:
                print("found by name {0}".format(destination_movie["Name"]))
                return destination_movie["Id"]
        return None

    def searchDestinationLibrary(MigrationMedia, Library):
        for Item in Library["Items"]:
            for itProv, itId in Item["ProviderIds"].items():
                for prov, id in MigrationMedia["ProviderIds"].items():
                    if itId == id and prov == itProv:
                        return Item["Id"]
        return None

    def iterateMigrationData():
        Library = {}
        nonlocal MigrationDataFinal
        # for u in selectedUsers:
        #     print(u)
        for user in destinationUsers:
            if user["Name"].replace("_", " ") in selectedUsers:
                MigrationDataFinal[user["Name"].replace("_", " ")] = []
                Library = get_userLibrary(user)
                for MigrationMedia in MigrationData[user["Name"].replace("_", " ")]:
                    MigrationMedia["DestinationId"] = searchDestinationLibrary(
                        MigrationMedia, Library
                    )
                    # print(MigrationMedia['DestinationId'])
                    if MigrationMedia["DestinationId"] is None:
                        MigrationMedia["DestinationId"] = search_byName(
                            MigrationMedia, Library
                        )
                    MigrationDataFinal[user["Name"].replace("_", " ")].append(
                        MigrationMedia
                    )

    def generate_report():
        nonlocal reportStr
        nonlocal report
        reportStr += "\n\n\n                      ### Source2Destination ###\n\n\n"
        reportStr += report["users"]
        reportStr += "\n\n"
        for user in destinationUsers:
            if user["Name"].replace("_", " ") in selectedUsers:
                reportStr += "--- {0} ---\n".format(user["Name"].replace("_", " "))
                reportStr += "Medias Migrated : {0} / {1}\n".format(
                    report[user["Name"].replace("_", " ")]["ok"],
                    report[user["Name"].replace("_", " ")]["tosend"],
                )
                if report[user["Name"].replace("_", " ")]["nok"] != []:
                    reportStr += "Unfortunately, I Missed {0} Medias :\n{1}\n".format(
                        report[user["Name"].replace("_", " ")]["tosend"]
                        - report[user["Name"].replace("_", " ")]["ok"],
                        list(report[user["Name"].replace("_", " ")]["nok"]),
                    )
        with open("RESULTS.txt", "w") as outfile:
            outfile.write("".join(reportStr))
            outfile.close()

    def set_pw(u, pw):
        p1 = "p1"
        p2 = "p2"
        if pw is not None:
            return pw
        while 1:
            print("\nEnter password for user {0}".format(u))
            p1 = getpass.getpass(prompt="Password : ")
            p2 = getpass.getpass(prompt="confirm   : ")
            if p1 == p2:
                if p1 == "":
                    print("Warning ! Password is set to empty !")
                return p1
            else:
                print("passwords does not match \n")

    MigrationDataFinal = {}
    DestinationUsersIdDict = {}
    NormalizedMigrationData = {}
    destinationUsers = destination_get_users_list()
    userTotal = len(destinationUsers)
    compare_users()
    # uptade the destination Users in case we created one
    destinationUsers = destination_get_users_list()
    userTotal = len(destinationUsers)
    iterateMigrationData()
    send_watchedStatus()

    generate_report()


if __name__ == "__main__":
    path = "jellysync.ini"

    global MigrationData
    global SOURCE_APIKEY
    global SOURCE_URLBASE
    global DEST_APIKEY
    global DEST_URLBASE
    MigrationData = {}
    selectedUsers = []

    argv = sys.argv[1:]
    tofile = None
    fromfile = None
    newUser_pw = None
    MigrationFile = None

    parser = argparse.ArgumentParser(prog='JellySync', usage='%(prog)s [options]')
    parser.add_argument('--tofile', help='run the script saving viewed statuses to a file instead of sending them to destination server')
    parser.add_argument('--fromfile', help='run the script with a file as source server and send viewed statuses to destination server')
    parser.add_argument('--pw', action='store_const', const='', help='set default password for new or existing users')
    # parser.print_help()
    args = parser.parse_args()
    tofile = args.tofile
    fromfile = args.fromfile
    newUser_pw = args.pw

    SOURCE_APIKEY = os.getenv("SOURCE_APIKEY")
    SOURCE_URLBASE = os.getenv("SOURCE_URLBASE")
    DEST_APIKEY = os.getenv("DEST_APIKEY")
    DEST_URLBASE = os.getenv("DEST_URLBASE")

    if tofile != None:
        print("Migration to file {0}".format(tofile))
        try:
            MigrationFile = open(tofile, "w")
        except:
            print("cannot open file {0}".format(tofile))
            sys.exit(1)

    elif fromfile != None:
        print("Migration from file {0}".format(fromfile))
        try:
            MigrationFile = open(fromfile, "r")
            MigrationData = json.loads(MigrationFile.read())
            for user in MigrationData:
                selectedUsers.append(user)
                # print("Adding Selected User: {0}".format(user))
        except:
            print("cannot open file {0}".format(tofile))
            sys.exit(1)
    else:
        print("no file specified, will run from source server to destination server")

    if fromfile is None:
        source(selectedUsers)
        if tofile is not None:
            MigrationFile.write(json.dumps(MigrationData))
            MigrationFile.close()
            sys.exit(1)

    if tofile is None:
        destination(newUser_pw)
    if MigrationFile is not None:
        MigrationFile.close()
    sys.exit(1)
