############################################################
SSO & REST API for WCW APA Learn - Integration Documentation
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

***
SSO
***

Login URL:
 - https://[domain]/learn/sso/

Query Sting Parameters:
 - **return_url** (optional): the URL to redirect the user (back) to after logging in. If not passed, defaults to https://apa.staging.coursestage.com/login/ if the [domain] is **staging.planning.org** or https://learn.planning.org/login/ if the [domain] is **www.planning.org**
 - **return_path** (optional): similar to return_url, but only specifying the path of the url to redirect the user (back) to after logging in. The redirect domain is set to apa.staging.coursestage.com if the [domain] is **staging.planning.org** or **learn.planning.org** if the [domain] is **www.planning.org**

Example login URLs:
 - example 1: https://staging.planning.org/learn/sso/?return_url=https://apa.staging.coursestage.com/somewhere/
 - example 2 (equivalent): https://staging.planning.org/learn/sso/?return_path=/somewhere/

Response:
 - if user is already logged into planning.org, or upon successful login, user is redirected to the return_url, with an authorization token passed in the querystring.

Example Response: 
 - successful login from https://staging.planning.org/learn/sso/?return_path=/anotherpath/ would redirected to https://apa.staging.coursestage.com/anotherpath/?token=MYTOKEN

NOTES: 
 - APA can change the default return url to whatever is needed. If both return_url and return_path are specified, then the return_url supercedes return_path.

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

Contact
=======

Request:
 - method name: **contact**
 - authorization token passed in the path
 - endpoint: https://[domain]/api/0.4/contact/[token]/?api_key=[api_key]

Example:
 - https://staging.planning.org/api/0.4/contact/MYTOKEN/?api_key=MYKEY

Response:
 - **sucess**: "true" when contact is found, "false" if not
 - **data**: JSON data for the requested contact

 Example Response:

::

   {
   "data": 
      {
         "imis_id": "000001", 
         "permission_groups": ["17CONF", "18CONF", "member", "aicpmember"],
         "first_name": "Thomas", 
         "last_name": "Hobbes", 
         "city": "Malmesbury", 
         "state": "IL", 
         "email": "thobbes@planning.org", 
         "member_type": "STF", 
         "chapter": "CHAPT IL", 
         "designation": "AICP", 
         "full_name": "Thomas Hobbes, AICP", 
         "company": "American Planning Association"
      }, 
   "success": true
   }


NOTES: 
 - permission groups list will be much longer for most users, although most permission groups are not applicable to APA Learn integration.

***************************************
Product Link for E-Commerce Integration
***************************************

 - https://[domain]/learn/course/[course master id]/




