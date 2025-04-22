import requests
import json
from typing import List, Dict
import urllib3
from ui.utils import log_function_execution

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UserRetriever:
    def __init__(self, server_url: str, access_token: str, customer_id: str, library_id: str):
        self.server_url = server_url
        self.access_token = access_token
        self.customer_id = customer_id
        self.library_id = library_id
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Auth-Token': access_token,
            'Content-Type': 'application/json'
        }

    def get_all_users(self) -> List[Dict]:
        """Retrieves all users using pagination strategy"""
        if not self.customer_id:
            error_msg = "Customer ID is required"
            log_function_execution("get_all_users", "FAILED", {
                "error": error_msg
            })
            raise Exception(error_msg)
            
        all_users = []
        base_url = f'https://{self.server_url}/work/api/v2/customers/{self.customer_id}/users'
        
        # First try with maximum limit
        params = {
            'limit': 9999,
            'offset': 0
        }
        
        log_function_execution("get_all_users", "STARTED", {
            "api_url": base_url,
            "parameters": params
        })
        
        response = requests.get(base_url, headers=self.headers, params=params, verify=False)
        if not response.ok:
            # Create debug-safe headers by indicating presence of auth tokens
            debug_headers = {
                k: ('Bearer token present' if k == 'Authorization' 
                    else 'Token present' if k == 'X-Auth-Token'
                    else v)
                for k, v in self.headers.items()
            }
            error_msg = f"Failed to retrieve users"
            log_function_execution("get_all_users", "FAILED", {
                "api_url": base_url,
                "parameters": params,
                "status_code": response.status_code,
                "error": error_msg
            })
            raise Exception(f"""Failed to retrieve users:
URL: {base_url}
Parameters: {json.dumps(params, indent=2)}
Headers: {json.dumps(debug_headers, indent=2)}
Response: {response.text}""")
            
        data = response.json()
        all_users.extend(data['data'])
        
        # If we got max users, we need to use pagination with alphabet filtering
        if len(data['data']) == 9999:
            # Clear the list and start fresh with pagination
            all_users = []
            
            # Define characters to search by
            chars = "abcdefghijklmnopqrstuvwxyz0123456789_-"
            
            for char in chars:
                offset = 0
                while True:
                    params = {
                        'limit': 1111,
                        'offset': offset,
                        'alias': f"{char}*"
                    }
                    
                    log_function_execution("get_all_users", "PROGRESS", {
                        "api_url": base_url,
                        "parameters": params,
                        "prefix": char,
                        "offset": offset
                    })
                    
                    response = requests.get(base_url, headers=self.headers, params=params, verify=False)
                    if not response.ok:
                        # Create debug-safe headers by indicating presence of auth tokens
                        debug_headers = {
                            k: ('Bearer token present' if k == 'Authorization' 
                                else 'Token present' if k == 'X-Auth-Token'
                                else v)
                            for k, v in self.headers.items()
                        }
                        error_msg = f"Failed to retrieve users for prefix '{char}'"
                        log_function_execution("get_all_users", "FAILED", {
                            "api_url": base_url,
                            "parameters": params,
                            "status_code": response.status_code,
                            "error": error_msg,
                            "prefix": char
                        })
                        raise Exception(f"""Failed to retrieve users for prefix '{char}':
URL: {base_url}
Parameters: {json.dumps(params, indent=2)}
Headers: {json.dumps(debug_headers, indent=2)}
Response: {response.text}""")
                        
                    data = response.json()
                    users = data['data']
                    if not users:
                        break
                        
                    all_users.extend(users)
                    
                    if len(users) < params['limit']:
                        break
                        
                    offset += params['limit']
        
        log_function_execution("get_all_users", "SUCCESS", {
            "api_url": base_url,
            "users_count": len(all_users)
        })
        return all_users

    def get_user_list(self) -> List[Dict]:
        """Returns the list of user data containing complete information"""
        try:
            users = self.get_all_users()
            log_function_execution("get_user_list", "SUCCESS", {
                "users_count": len(users)
            })
            return users
        except Exception as e:
            log_function_execution("get_user_list", "FAILED", {
                "error": str(e)
            })
            raise