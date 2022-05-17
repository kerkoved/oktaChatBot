import requests
import os
from dotenv import load_dotenv


load_dotenv()
OKTA_TOKEN = os.environ["OKTA_TOKEN"]
host = os.environ["OKTA_HOST"]
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "SSWS {}".format(OKTA_TOKEN)
}

# attributes for each user object
profileAttribs = ["firstName", "lastName", "mobilePhone", "secondEmail", "login", "email"]
generalAttribs = ["id", "status", "created", "activated", "statusChanged", "lastLogin", "lastUpdated", "passwordChanged"]
credentialAttribs = ["password", "recovery_question", "provider"]


# splits slack input by spaces
# determines which function to run based  on the command
def answerLookup(query):
    keywords = query.split(" ")
    command = keywords[1]
    if command == "query":
        try:
            email = keywords[2].strip("<>").split("|")[1]
        except IndexError:
            return "Failed to run command. Make sure format is correct"
        attributes = keywords[3:]
        return getUserAttribute(email, *attributes)
    elif command == "list":
        return userList()
    elif command == "create":
        try:
            email = keywords[2].strip("<>").split("|")[1]
        except IndexError:
            return "Failed to run command. Make sure format is correct"
        userDict = {}
        attributes = keywords[3:]
        for attrib in attributes:
            key = attrib.split("=")[0]
            value = attrib.split("=")[1]
            userDict[key] = value
        return createUserWithAttributes(email, userDict)
    elif command == "update":
        try:
            email = keywords[2].strip("<>").split("|")[1]
        except IndexError:
            return "Failed to run command. Make sure format is correct"
        userDict = {}
        attributes = keywords[3:]
        for attrib in attributes:
            key = attrib.split("=")[0]
            value = attrib.split("=")[1]
            userDict[key] = value
        return updateUser(email, userDict)
    else:
        return "I didn't recognize that command\nPlease try another command (ex. list, query, create, update)"


# returns list of users full name and email
def userList():
    usersStr = "Users:\n"
    url = "https://{}/api/v1/users".format(host)
    response = requests.get(url, headers=headers)
    for elem in response.json():
        for key, value in elem.items():
            if key == "profile":
                usersStr += "{} {} - {}\n".format(value["firstName"], value["lastName"], value["email"])
    return usersStr


# returns given user and their attributes
def getUserAttribute(email, *args):
    # not sure if it makes sense to provide credentials (security risk). maybe recovery question
    url = "https://{}/api/v1/users/{}".format(host, email)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "Email does not exist in directory"
    else:
        userStr = "Email: {}\n".format(email)
        for attrib in args:
            if attrib in generalAttribs:
                userStr += "{}: {}\n".format(attrib, response.json()[attrib])
            elif attrib in profileAttribs:
                userStr += "{}: {}\n".format(attrib, response.json()['profile'][attrib])
            elif attrib in credentialAttribs:
                return "Credential attributes can't be retrieved"
            else:
                return "{} - attribute does not exist".format(attrib)
    return userStr


# creates user with attributes
def createUserWithAttributes(email, userData):
    # profile attributes required
    # if login or email aren't provided set as username
    if 'login' not in userData:
        userData['login'] = email
    else:
        userData['login'] = userData['login'].strip("<>").split("|")[1]
    if 'email' not in userData:
        userData['email'] = userData['email'].strip("<>").split("|")[1]
    else:
        userData['email'] = email
    data = {'profile': {}, 'credentials': {}}
    for key, value in userData.items():
        if key in profileAttribs:
            data['profile'][key] = value
        elif key in credentialAttribs:
            if key == 'password':
                data['credentials'][key] = {'value': value}
            # implement recovery question
            else:
                return "Can't create user with these attributes"
        else:
            return "Can't create user with these attributes"
    url = "https://{}/api/v1/users?activate=false".format(host)
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        return "[Creation: Failure]\nEmail: {}".format(email)
    else:
        userStr = "[Creation: Success]\nEmail: {}\n".format(email)
        for key, value in data['profile'].items():
            userStr += "{}: {}\n".format(key, value)
    return userStr


# updates user with given attributes
def updateUser(email, userData):
    # can update profile and/or credentials attributes
    data = {'profile': {}, 'credentials': {}}
    for key, value in userData.items():
        if key in profileAttribs:
            if key == 'email' or key == 'login':
                value = value.strip("<>").split("|")[1]
            data['profile'][key] = value
        elif key in credentialAttribs:
            if key == 'password':
                data['credentials'][key] = {'value': value}
            # add option for recovery question. requires question and answer
            elif key == 'recovery_question':
                return "Recovery question not implemented"
            else:
                return "Can't update user with these attributes"
        elif key in generalAttribs:
            data[key] = value
        else:
            return "Can't update user with these attributes"
    url = "https://{}/api/v1/users/{}".format(host, email)
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        return "[Update: Failure]\nEmail: {}".format(email)
    else:
        userStr = "[Update: Success]\nEmail: {}\n".format(email)
        for key, value in data.items():
            if key in generalAttribs:
                userStr += "{}: {}\n".format(key, value)
            elif key == 'profile':
                for key1, value1 in data['profile'].items():
                    userStr += "{}: {}\n".format(key1, value1)
            elif key == 'credentials':
                for key1, value1 in data['credentials'].items():
                    if key1 == 'password':
                        for key2, value2 in data['credentials'][key1].items():
                            userStr += "{}: {}\n".format(key1, value2)
    return userStr
