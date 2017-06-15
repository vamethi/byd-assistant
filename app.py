#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    print("Response:")
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    #baseurl = "https://my316075.sapbydesign.com/sap/byd/odata/cust/v1/purchasing/PurchaseOrderCollection/?"
    baseurl = "https://services.odata.org/Northwind/Northwind.svc/Products?"
    yql_query = makeYqlQuery(req)
    yql_url = baseurl + yql_query + "&$format=json"
    print(yql_url)
    result = urlopen(yql_url).read()
    data = json.loads(result)
    print("data")
    print(data)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    """result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None """

    return "$top=1"


def makeWebhookResult(data):
    value = data.get('value')
    print("json.value: ")
    print(json.dumps(value, indent=4)) 
    
    prodID = value[0].get('ProductID')
    print("json.ID: ")
    print(json.dumps(prodID, indent=4)) 
    
    prodName = value[0].get('ProductName')
    print("json.name: ")
    print(json.dumps(prodName, indent=4)) 
    
    #speech = "Purchase Order ID is " + item.get('PurchaseOrderID') + \
    #         "and the status of this PO is " + item.get('PurchaseOrderLifeCycleStatusCodeText')
    speech = "Product ID is " + prodID + \
             "The description of product is " + prodName
    
    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        #"contextOut": "",
        "source": "byd-assistant"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

app.run(debug=False, port=port, host='0.0.0.0')
