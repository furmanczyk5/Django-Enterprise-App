# WHERE DO THESE METHODS GET CALLED? WHEN DO WE NEED TO HIT
# EVENTSCRIBE API?
def get_eventscribe_pdf_assets():

    api_key = EVENTSCRIBE_API_KEY
    url = 'https://mycadmium.com/webservices/eventScribeAPIs.asp'

    params = {
    'APIKey': api_key,
    'Method': 'getAssets'}

    r = requests.post(url, params=params)
    json_list = r.json()

    return json_list


def get_eventscribe_favorites(contact=None):

    api_key = EVENTSCRIBE_API_KEY
    url = 'https://mycadmium.com/webservices/eventScribeAPIs.asp'
    account_id = contact.external_id if contact else None

    params = {
    'APIKey': api_key,
    'Method': 'getFavorites',
    'AccountID': account_id
    }

    r = requests.post(url, params=params)
    json_list = r.json()

    return json_list


def add_or_remove_eventscribe_favorites(username=None, add_or_remove=None,
    cadmium_id=None, ticketed=True):

    api_key = EVENTSCRIBE_API_KEY
    url = 'https://mycadmium.com/webservices/eventScribeAPIs.asp'
    if username:
        try:
            contact = Contact.objects.get(user__username=username)
        except Exception:
            contact = None
        account_id = contact.external_id if contact else None

    params = {
    'APIKey': api_key,
    'Method': 'addRemoveFavorite',
    'AccountID': account_id,
    'FavoriteMethod': add_or_remove
    }

    data = {
        "id": cadmium_id,
        "ticketed": ticketed
    }

    r = requests.post(url, params=params, json=data)

    json_list = r.json()

    return json_list

def create_or_update_eventscribe_account(contact=None):

    api_key = EVENTSCRIBE_API_KEY
    url = 'https://mycadmium.com/webservices/eventScribeAPIs.asp'
    account_id = None
    username = None
    favorites = []
    user_tokens = None # ??
    json_list = None
    data = None

    if contact:
        account_id = contact.external_id if contact else None
        username = contact.user.username
        schedule_records = CustomEventSchedule.objects.filter(id=username)

        for sched in schedule_records:
            code = sched.product_code.strip("NPC19/")
            content = Content.objects.filter(code=code).first()
            favorites.append(content.external_key)

    params = {
    'APIKey': api_key,
    'Method': 'NewAccount'
    }

    if contact:
        c = contact
        data = {
            "EventExternalID":"",
            "AccountPrefix":c.prefix_name,
            "AccountFirstName":first_name,
            "AccountMiddleInitial":c.middle_name,
            "AccountLastName":last_name,
            "AccountSuffix":c.suffix_name,
            "AccountEmail":email,
            "AccountPosition":c.job_title,
            "AccountOrganization":c.company,
            "AccountTelephoneOffice":c.phone,
            "AccountTelephoneCell":"",
            "AccountKey":username,
            "AccountKey2":"",
            "AccountAccessLevel":"Standard",
            "AccountAddress1":c.address1,
            "AccountAddress2":c.address2,
            "AccountAddress3":"",
            "AccountCity":c.city,
            "AccountState":c.state,
            "AccountCountry":c.country,
            "AccountZip":c.zip_code,
            "AccountAssociationID":username,
            "AccountAssociationKey":user_tokens,
            "Favorites":favorites,
            "AccountCredentials":c.designation,
            "AccountRegID":"",
            "AccountCustomField1":"",
            "AccountCustomField2":"",
            "AccountCustomField3":"",
            "AccountCustomField4":"",
            "AccountCustomField5":"",
            "AccountCustomField6":"",
            "AccountCustomField7":"",
            "AccountCustomField9":"",
            "AccountCustomField10":"",
            "AccountRegType":"",
            "AccountASort":"",
            "AccountUnlockCodesPDF":"",
            "AccountUnlockCodesAudio":"",
        }

        data = {k: v for k, v in data.items() if not (
            v == None or v == "" or v == [])}
    r = requests.post(url, params=params, json=data)

    json_list = r.json()

    return json_list

def cancel_eventscribe_account(contact=None, add_or_remove=None,
    id=None, ticketed=True):

    api_key = EVENTSCRIBE_API_KEY
    url = 'https://mycadmium.com/webservices/eventScribeAPIs.asp'
    account_id = contact.external_id if contact else None

    params = {
    'APIKey': api_key,
    'Method': 'cancelAccount',
    'AccountID': account_id,
    }

    r = requests.post(url, params=params)

    json_list = r.json()

    return json_list

def delete_eventscribe_account(contact=None, add_or_remove=None,
    id=None, ticketed=True):

    api_key = EVENTSCRIBE_API_KEY
    url = 'https://mycadmium.com/webservices/eventScribeAPIs.asp'
    account_id = contact.external_id if contact else None

    params = {
    'APIKey': api_key,
    'Method': 'deleteAccount',
    'AccountID': account_id,
    }

    r = requests.post(url, params=params)

    json_list = r.json()

    return json_list
