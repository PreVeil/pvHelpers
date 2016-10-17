import requests

from . import misc
from . import apiclient

class UserData:
    def __init__(self, user_id, display_name, mail_cid):
        self.user_id      = user_id
        self.display_name = display_name
        self.mail_cid     = mail_cid

def fetchUser(user_id, client, key_version=-1):
    if not isinstance(user_id, unicode):
        return False, None
    if not isinstance(key_version, (int, long)):
        return False, None

    status, user_data = fetchUsers([(user_id, key_version)], client)
    if status == False:
        return False, None
    if len(user_data) != 1:
        return False, None
    if user_id not in user_data:
        return False, None
    user_datum = user_data[user_id]
    if user_datum == False:
        return False, None
    return True, user_datum

def _materializeUserDatum(json_user):
    user_id = json_user.get("user_id")
    if user_id == None:
        return False, None

    display_name = json_user.get("display_name")
    if display_name == None:
        return False, None

    mail_cid = json_user.get("mail_collection_id")
    if mail_cid == None:
        return False, None

    return True, UserData(user_id, display_name, mail_cid)

# You probably want to use fetchUsers().
def _fetchUsers(queries, client):
    if not isinstance(client, apiclient.APIClient):
        return False, None
    params = {"spec" : misc.jdumps(queries)}
    try:
        resp = client.get("/users", params=params)
        if resp.status_code != requests.codes.ok:
            return False, None
    except requests.exceptions.RequestException as e:
        return False, None

    text = resp.text
    if resp.encoding != 'utf-8' or not isinstance(text, unicode):
        return False, None
    status, data = misc.jloads(text)
    if status == False:
        return False, None

    return True, data

def fetchUsers(user_ids, client):
    if not isinstance(user_ids, list):
        return False, None
    query_data = []
    for x in user_ids:
        if len(x) != 2:
            return False, None
        query_data.append({"user_id": x[0], "key_version": x[1]})

    status, query_result = _fetchUsers(query_data, client)
    if status == False:
        return False, None
    users = query_result.get("users")
    if users == None:
        return False, None

    output = misc.CaseInsensitiveDict()
    for u in users:
        status, user_datum = _materializeUserDatum(u)
        if status == False:
            continue
        output[user_datum.user_id] = user_datum

    for (x, _) in user_ids:
        if x not in output:
            output[x] = False

    return True, output
