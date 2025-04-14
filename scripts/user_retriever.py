import requests
import json
from typing import List, Dict
import urllib3

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
            raise Exception("Customer ID is required")
            
        all_users = []
        base_url = f'https://{self.server_url}/work/api/v2/customers/{self.customer_id}/libraries/{self.library_id}/users'
        
        # First try with maximum limit
        params = {
            'limit': 9999,
            'offset': 0
        }
        
        response = requests.get(base_url, headers=self.headers, params=params, verify=False)
        if not response.ok:
            # Create debug-safe headers by indicating presence of auth tokens
            debug_headers = {
                k: ('Bearer token present' if k == 'Authorization' 
                    else 'Token present' if k == 'X-Auth-Token'
                    else v)
                for k, v in self.headers.items()
            }
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
                    
                    response = requests.get(base_url, headers=self.headers, params=params, verify=False)
                    if not response.ok:
                        # Create debug-safe headers by indicating presence of auth tokens
                        debug_headers = {
                            k: ('Bearer token present' if k == 'Authorization' 
                                else 'Token present' if k == 'X-Auth-Token'
                                else v)
                            for k, v in self.headers.items()
                        }
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
                    
        return all_users

    def get_user_list(self) -> List[str]:
        """Returns just the list of user aliases"""
        users = self.get_all_users()
        return [user['alias'] for user in users]