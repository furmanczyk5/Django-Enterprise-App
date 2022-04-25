############################################################
REST API & SSO for Cadmium Events Mobile App - Integration Documentation
############################################################

****************
Endpoints
****************

Production Domain:
 - **www.planning.org**

Staging Domain:
 - **staging.planning.org**

NOTES:
 - all requests must use HTTPS
 - all requests, including REST API calls, must include trailing slash in URL (otherwise, planning.org server will return a redirect response)

*************
REST Endpoint
*************

https://[domain]/api/[version]/

Version:
 - the current API version is **0.4**

**************
Authentication
**************

REST Client Authentication (API Key)
====================================

A permanant client API key is required for all API requests to planning.org, passed as a query string parameter. If an API key is not passed or is invalid, the server will return a 401 Unauthorized response. Contact the APA dev team to acquire the key.

Example:
 - https://staging.planning.org/api/0.4/?api_key=MYKEY

*******
Methods
*******

Login (SSO)
===========

Request:
 - method name: **login**
 - endpoint: https://[domain]/api/0.4/login/

Example:
 - https://[domain]/api/0.4/login/?api_key=[api_key]&username=[id or email]&password=[password]

Response:
 - **sucess**: "true" when contact is found, "false" if not
 - **data**: JSON data for the requested contact

 Example Response:

::

   {
   "data":
      {
         "imis_id": "000321",
         "permission_groups": ["17CONF", "18CONF", "member", "aicpmember"],
         "first_name": "Thomas",
         "middle_name":"Foo",
         "last_name": "Hobbes",
         "city": "Malmesbury",
         "state": "Wiltshire",
         "country":"England",
         "cell_phone":"312-555-5555",
         "work_phone":"312-555-5554",
         "email": "thobbes@planning.org",
         "member_type": "STF",
         "chapter": "CHAPT IL",
         "designation": "AICP",
         "full_name": "Thomas Hobbes, AICP",
         "position_title":"Philosopher",
         "company": "American Planning Association",
         "token": "p0SDFJHSDF878er798987kjdsf999"
      },
   "success": true
   }

::

Example Response Failure:

::

   {
   "data":
      {
         "msg": "You can never log in again."
      },
   "success": false
   }

::

NOTES:
 - permission groups list will be much longer for most users, although most permission groups are not applicable to the mobile app integration.

**(QUESTION: do we need to provide a similar endpoint to re-retrieve contact info based on token or ID after already having been authenticated?)**

Get Schedule
============

Returns complete list of items on attendee's schedule

Request:
 - method name: **conference/schedule**
 - endpoint: https://[domain]/api/0.4/conference/schedule/

Query Sting Parameters:
 - **imis_id** : the user's 6-character iMIS number. [TBD: consider whether to pass token instead?]

Example:
 - https://staging.planning.org/api/0.4/conference/schedule/?api_key=[api_key]&imis_id=000321

 Example Response:

::

   {
   "data":
      {
         "activities": [
            {
            "id":9165311,
            "code":"NPC198083",
            "quantity":1,
            "ticketed":false,
            },
            {
            "id":9165312,
            "code":"NPC198090",
            "quantity":2,
            "ticketed":true
            },
         ]
      },
   "success": true
   }

Update Schedule
============

Adds or removes an activity to/from an attendee's schedule

Request:
 - method name: **conference/schedule/update**
 - endpoint: https://[domain]/api/0.4/conference/schedule/update/

Query Sting Parameters:
 - **imis_id** : the user's 6-character iMIS number. **(TBD: consider whether to pass token instead?)**
 - **activity_id** : the id of the activity to add/remove **(TBD would code be better?)**
 - **method** : "ADD" or "REMOVE"

Example:
 - https://staging.planning.org/api/0.4/conference/schedule/update/?api_key=[api_key]&imis_id=000321&activity_id=9165311&method=ADD

***************************************************************
SSO (back to planning.org for CM logging or purchasing tickets)
***************************************************************

Login URL:
 - https://[domain]/login/sso/?token=[token]&next=[redirect url]

Query Sting Parameters:
 - **token** : the user token. The user will be authenticated on the planning.org site if token matches. **(TBD: whether tokens expire)**
 - **next** (optional): redirects user to specific path on site (e.g. for evaluating or buying tickets)

Example login URL:
 - https://staging.planning.org/login/sso/?token=p0SDFJHSDF878er798987kjdsf999&next=/events/9163237/evaluation/

Response:
 - if user user token matches, user is logged into planning.org, and user is redirected to the  next url.





