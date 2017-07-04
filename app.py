#!/usr/bin/env python
import http.client, base64

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)
node_id = ""

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print(node_id)
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
    baseurl = "/sap/byd/odata/cust/v1/purchasing/"
    auth = base64.encodestring(('%s:%s' % ("odata_demo", "Welcome01")).encode()).decode().replace('\n', '')
    csrf = fetch_csrf(conn, baseurl, auth)
    headers = {
                'authorization': "Basic " + auth,
                'x-csrf-token': csrf
              }    
    method, query = makeQuery(req, conn, baseurl, headers)
    qry_url = baseurl + query
    print(method, qry_url, headers)
    
    conn.request(method, qry_url, headers=headers)
    res = conn.getresponse()
    result = res.read()
    print(result)
    
    data = json.loads(result)
    print("data")
    print(data)
    res = makeWebhookResult(data, req)
    return res	

def fetch_csrf(conn, url, auth): 
    headers = {
                'authorization': "Basic " + auth,
                'x-csrf-token': "fetch"
              }
    conn.request("GET", url, headers=headers)
    reshdr = conn.getresponse()
    reshdr.read()
    return reshdr.getheader('x-csrf-token')

def makeQuery(req, conn, baseurl, headers):
    result = req.get("result")
    parameters = result.get("parameters")
    poid = parameters.get("id")
    status = parameters.get("status")
    action = parameters.get("po-action")
    print("PO ID and status ", poid, status)
	
    intent = result.get("action")    
    if intent == "find-status":
        return "GET","PurchaseOrderCollection/?%24filter=PurchaseOrderID%20eq%20'" + poid + "'&%24format=json" 
    elif intent == "find-count":
        return "GET","PurchaseOrderCollection/$count?%24filter=PurchaseOrderLifeCycleStatusCodeText%20eq%20'" + status + "'"
    elif intent == "po-action":
        #qry_url = baseurl + "Query?ID='" + poid + "'"
        qry_url = baseurl + "PurchaseOrderCollection/?%24filter=PurchaseOrderID%20eq%20'" + poid + "'&%24format=json" 
        conn.request("GET", qry_url, headers=headers)
        res = conn.getresponse()
        result = res.read()
        data = json.loads(result)
        node_id = data.get('d').get('results')[0].get('ObjectID')
        return "POST", action + "?" + "ObjectID='" + node_id +"'"
    else:
        return {}
	
def makeWebhookResult(data, req):
    intent = req.get("result").get("action")    
    if intent == "find-status":		
        d = data.get('d')
        value = d.get('results')
        node_id = value[0].get('ObjectID')
        print(node_id)
        print("json.results: ")
        print(json.dumps(value, indent=4))
        speech = "The status of Purchase Order ID " + str(value[0].get('PurchaseOrderID')) + \
             	 " is " + value[0].get('PurchaseOrderLifeCycleStatusCodeText')
    
    elif intent == "find-count":        
        if int(data) > 1:
            speech = "There are " + str(data) + " purchase orders in the system with " + \
                      req.get("result").get("parameters").get("status") + " status"
        elif int(data) == 1:
            speech = "There is " + str(data) + " purchase order in the system with " + \
                      req.get("result").get("parameters").get("status") + " status"
        else:
            speech = "There are no purchase orders in the system with " + \
                      req.get("result").get("parameters").get("status") + " status"
    else:
        speech = "Sorry, I did not understand you! Please try again"
	
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
