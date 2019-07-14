"""
EasyCloud Chameleon Cloud Resources ID Viewer
"""

from gnocchiclient.v1 import client
from keystoneauth1 import loading

__author__ = "Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato"
__copyright__ = "Copyright (C) 2019"
__credits__ = ["Andrea Lombardo", "Irene Lovotti"]
__license__ = "GPL v3"
__version__ = "0.10.0"
__maintainer__ = "Luca Banzato"
__email__ = "20005492@studenti.uniupo.it"
__status__ = "Prototype"

############################
# To be filled by the user #
############################
AUTH_URL = ""
USERNAME = ""
PASSWORD = ""
PROJECT_ID = ""
REGION_NAME = ""
############################

print("\nChameleon Cloud Resources ID Viewer\n")

# Authentication
_loader = loading.get_plugin_loader('password')
_auth = _loader.load_from_options(auth_url=AUTH_URL,
                                  username=USERNAME,
                                  password=PASSWORD,
                                  project_id=PROJECT_ID,
                                  user_domain_name="default")
gnocchi_client = client.Client(adapter_options={"region_name": REGION_NAME},
                               session_options={"auth": _auth})
# Instance ID request
instance_id = str(input("Insert the instance id: "))

try:
    # Get resources for a specified instance (can raise an exception)
    resources = gnocchi_client.resource.get("generic", instance_id)
    # Print metrics if available
    if "metrics" in resources:
        metrics = resources["metrics"]
        i = 0
        print("\nMetrics available for instance " + instance_id + ":\n")
        for key, value in metrics.items():
            print(("ID: %-25s - Name: %-25s" % (value, key)))
        print("")
    else:
        print("No metrics available for instance " + instance_id)
except Exception as e:
    print("An error has occourred while fetching metrics details: " + str(e))
