import json
import time
import requests
import hashlib

from planning.settings import SCHOLAR_LAB_ADDRESS, SCHOLAR_LAB_API_KEY

# Exam ScholarLab Product Code
CUSTOMER_PRODUCT_ID = "APAAPI"


class ScholarLab():

    def create_user_json(self, user):
        """
        returns JSON for user created in scholar lab creation
        """
        user_json = {}
        user_json['userid'] = user.username
        user_json['firstname'] = user.first_name
        user_json['lastname'] = user.last_name
        user_json['email'] = user.email

        return user_json

    def authorize(self, user):
        """
        login user to scholarlab 
        """

        try:
            authorize_url = SCHOLAR_LAB_ADDRESS + "/api/auth/authorizeuserentry"

            #user_agent = r.request.headers.get('User-Agent')
            user_json = self.create_user_json(user)

            time_stamp = int(time.time())
            data_payload = {"user": user_json}
            encrypted_token = hashlib.md5(str.encode(SCHOLAR_LAB_API_KEY + str(time_stamp) + str(data_payload) + SCHOLAR_LAB_API_KEY)).hexdigest()

            customer_product = {"user": user_json}

            api_call = {
                        "apivers": "01_24_12",
                        "authtoken": str(encrypted_token),
                        "time": time_stamp,
                         "data": {"user": user_json,
                                "useragent":""
                                }
                        }

            r = requests.post(authorize_url, data=json.dumps(api_call))

            if r.json().get("status") == 'ok':
                user_auth_token = r.json().get("data").get("userauthtoken")

                http_redirect = (SCHOLAR_LAB_ADDRESS + "/home?uat={0}&time={1}".format(user_auth_token, time_stamp))

                hashed_url = hashlib.md5(str.encode(SCHOLAR_LAB_API_KEY + http_redirect + SCHOLAR_LAB_API_KEY)).hexdigest()
                       
                full_redirect_url = http_redirect + "&h=" + hashed_url

                return full_redirect_url
            else:
                return None
        except Exception as e:

            print(str(e))

    def create_access(self, user):
        user_json = self.create_user_json(user)

        time_stamp = int(time.time())
        end_point = SCHOLAR_LAB_ADDRESS + "/api/provisionaccesstoproducts"

        data_payload_json_string = {"user": user_json, "customerproductids": CUSTOMER_PRODUCT_ID}

        encrypted_token = hashlib.md5(str.encode(SCHOLAR_LAB_API_KEY + str(time_stamp) + json.dumps(data_payload_json_string) + SCHOLAR_LAB_API_KEY)).hexdigest()
        
        api_call = {
            "apivers":"01_24_12",
            "authtoken":encrypted_token,
            "time":time_stamp,
            "data":data_payload_json_string
        }

        r = requests.post(end_point, data=json.dumps(api_call))

        return r
