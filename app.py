#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

import http.client, base64

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

    #print("Request:")
    #print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    print("Response:")
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
		conn = http.client.HTTPSConnection("my316075.sapbydesign.com")
		baseurl = "/sap/byd/odata/cust/v1/purchasing/PurchaseOrderCollection/"
		query = makeQuery(req)
		qry_url = baseurl + query
		print(qry_url)
		base64string = base64.encodestring(('%s:%s' % ("odata_demo", "Welcome01")).encode()).decode().replace('\n', '')    
		headers = {
					'authorization': "Basic " + base64string
				  }

		conn.request("GET", qry_url, headers=headers)
		res = conn.getresponse()
		result = res.read()
		print("result")
		print(result)

		data = json.loads(result)
		print("data")
		print(data)
		res = makeWebhookResult(data, req)
		return res	

def makeQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    poid = parameters.get("id")
    status = parameters.get("status")
    print("PO ID and status ", poid, status)
	
    action = result.get("action")    
    if action == "find-status":	
        return "?%24filter=PurchaseOrderID%20eq%20'" + poid + "'&%24format=json" 
    elif action == "find-count":               
        return "$count?%24filter=PurchaseOrderLifeCycleStatusCodeText%20eq%20'" + status + "'"
    else:
        return {}
	
def makeWebhookResult(data, req):
    action = req.get("result").get("action")    
    if action == "find-status":		
        d = data.get('d')
        value = d.get('results')
        print("json.results: ")
        print(json.dumps(value, indent=4))
        speech = "The status of Purchase Order ID " + str(value[0].get('PurchaseOrderID')) + \
             	 " is " + value[0].get('PurchaseOrderLifeCycleStatusCodeText')
    
    elif action == "find-count":        
        if int(data) > 1:
            print(data)
            speech = "There are " + str(data) + \
             	 " purchase orders in the system with " + status + "status"
            print(speech)
        elif int(data) == 1:
            speech = "There is " + str(data) + \
             	 " purchase order in the system with " + status + "status"
        else:
            speech = "There are no purchase orders in the system with " + status + "status"
        print(speech)
    else:
        speech = "I did not understand you, please try again"
    print(speech)
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
