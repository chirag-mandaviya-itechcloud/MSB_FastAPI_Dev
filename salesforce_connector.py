from simple_salesforce import Salesforce
import os
from simple_salesforce.exceptions import SalesforceAuthenticationFailed, SalesforceError


username= os.getenv("SF_USERNAME", "dhruv.javiya@itechcloudsolution.com")
password= os.getenv("SF_PASSWORD", "Dhruv@101")
security_token= os.getenv("SF_TOKEN", "cLbHTLnMERpE0LVHz6Z56SH7")
domain= os.getenv("SF_DOMAIN", "test")

sf =None

def initialize_salesforce():
    try:
        # Replace 'your_username', 'your_password', and 'your_security_token' with your Salesforce credentials
        sf = Salesforce(username=username,
                        password=password, 
                        security_token=security_token,
                        client_id='Heroku', 
                        domain=domain)

    except SalesforceError as e:
        sf =None
        print(f"Database error: {e}")
        # Handle database errors and return appropriate HTTP response or raise an exception
    
    return sf

sf= initialize_salesforce()
    
