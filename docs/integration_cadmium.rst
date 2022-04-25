###############################################
Cadmium Proposals SSO and Harvester Integration
###############################################

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

**************
Authentication
**************

REST Client Authentication (API Key)
====================================

A permanant client API key is required for all API requests to planning.org, passed as a query string parameter. If an API key is not passed or is invalid, the server will return a 401 Unauthorized response. Contact the APA dev team to acquire the key.

Example:
 - https://staging.planning.org/api/0.4/?api_key=MYKEY

*****************
NPC Proposals SSO
*****************

Login URL:
 - https://[domain]/authentication/npc-proposals/sso/

Query Sting Parameters:
 - **return_url** (optional): the URL to redirect the user (back) to after logging in.

Example login URL:
 - https://staging.planning.org/authentication/npc-proposals/sso/?return_url=https://www.mycadmium.com/login.asp

Response:
 - if user is already logged into planning.org, or upon successful login, user is redirected to the return_url, with an authorization token passed in the querystring.

Example Response:
 - successful login from https://staging.planning.org/authentication/npc-proposals/sso/?return_url=https://www.mycadmium.com/login.asp would redirect to https://www.mycadmium.com/login.asp/?token=MYTOKEN

NOTES:
 - APA can change the default return url to whatever is needed.


***************************
NPC Proposals SSO User Data
***************************

Login URL:
 - https://[domain]/authentication/npc-proposals/user/

Query Sting Parameters:
 - **key** (optional): the API key.
 - **token** (optional): the authorization token to confirm login status.

Example login URL:
 - https://staging.planning.org/authentication/npc-proposals/user/?key=<API_KEY>&token=<MY_TOKEN>

Response:
 - **sucess**: "true" when contact is found, "false" if not
 - **data**: JSON data for the requested contact
 - **message**: Information provided in the event of failure

Example Response:

::

   {
   "data":
      {
         "first_name"="Thelonious",
         "middle_name"="Sphere",
         "last_name"="Monk",
         "credentials"="Mons.",
         "organization"="Minton's Playhouse",
         "title"="House Pianist",
         "address1"="210 W. 118th St.",
         "address2"="",
         "city"="New York",
         "state"="NY",
         "zip"="10026",
         "country"="United States",
         "member_status"="A",
         "member_type"="MEM",
         "member_id"="000000",
         "email"="thelonious@gmail.com",
         "bio"="jazz pianist and composer",
         "divisions"=[{"code":"JAZZ", "title":"Jazz Division"},{"code":"PIANO", "title":"Piano Division"}]
      },
   "success": true
   }

NOTES:
 - Divisions data is a list of dicts with code and title of each Division.

*********************
Harvester Integration
*********************


Update Presentation
===================

Request:
 - method name: **add**, **update** or **delete**
 - external_key: The Cadmium id for the presentation
 - endpoint: https://[domain]/presentations/[method]/?external_key=<EXTERNAL_KEY>/
 - MUST ADD THE PRESENTATION DATA HERE !!

Example:
 - https://planning.org/presentations/update/?external_key=<EXTERNAL_KEY>

Response:
 - **master_id**: The APA id for the presentation
 - **success**: "true" when presentation is updated, else "false"
 - **message**: Information about the success or failure of request

 Example Response:

::

  {
    "master_id": 9170824,
    "success": true,
    "message": "Successfully updated event."
  }


NOTES:
 - Update and add methods are equivalent.


Update Presenter
================

Request:
 - method name: **add** or **update**
 - external_id: The Cadmium id for the presenter
 - endpoint: https://[domain]/presenters/[method]/?external_id=<EXTERNAL_ID>/
 - MUST ADD THE PRESENTER DATA HERE !!

Example:
 - https://planning.org/presenters/update/?external_id=<EXTERNAL_ID>

Response:
 - **success**: "true" when presentation is updated, else "false"
 - **message**: Information about the success or failure of request

 Example Response:

::

  {
    "success": true,
    "message": "Successfully added/updated speaker info."
  }


NOTES:
 - Update and add methods are equivalent.
