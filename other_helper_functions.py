import web_helper_functions as whf
import config

def query_api(action,data):
    import requests    
    payload = {"version":1, 'data': data, 'apikey': 'YOUR_API_KEY_HERE', 'action':action}
    r = requests.post(config.apiUrl,json=payload)
    return r.content

#overall method to instantiate and recover the question for user 'userid'
def get_last_question_string(con,userid):
    cur = con.cursor()
    cur.execute('SELECT dataset, dataitem, detail FROM qa WHERE userid=? AND asked_last = 1;',(userid,));
    data = cur.fetchone();
    cur.close()
    if (data==None): #we shouldn't get to this state... TODO Handle this better.
        return "No more questions!";
    dataset = data[0]
    dataitem = data[1]
    detail = data[2]    
    data = {"dataset":data[0],"dataitem":data[1],"detail":data[2]}
    query_result = query_api('questionstring',data)
    try:
        output = json.loads(query_result)
    except ValueError:
        import sys
        print >>sys.stderr, "Unable to parse JSON from "+res
        return ('','') #not sure what to return yet if problem occurs TODO 
    return output

def do_inference(con,userid):
    cur = con.cursor()
    results = cur.execute('SELECT dataset, dataitem, detail, answer FROM qa WHERE userid=? AND asked_last=0;',(userid,)); #asked_last=0 -> don't want datasets without answers.
    data = []
    for it in results:
        data.append({'dataset':it[0],'dataitem':it[1],'detail':it[2],'answer':it[3]})
    res = query_api('inference',data)
    try:
        output = json.loads(res)
    except ValueError:
        import sys
        print >>sys.stderr, "Unable to parse JSON from "+res
        return ([],[],[])

    features = output['features']
    insights = output['insights']
    facts = output['facts']

    return features, insights, facts


def pick_question(con,userid):
    cur = con.cursor()
    results = cur.execute('SELECT dataset, dataitem, detail, answer FROM qa WHERE userid=? AND asked_last=0;',(userid,)); #asked_last=0 -> don't want datasets without answers.
    data = []
    for it in results:
        data.append({'dataset':it[0],'dataitem':it[1],'detail':it[2],'answer':it[3]})
    res = query_api('question',data)
    try:
        question = json.loads(res)
    except ValueError:
        import sys
        print >>sys.stderr, "Unable to parse JSON from "+res
        return {'dataset':None,'dataitem':None,'detail':None,'answer':None}

    return question

def delete_users_data(con,userid):
    cur = con.cursor()
    cur.execute("DELETE FROM qa WHERE userid = ?;",(userid,))
    cur.close()
    con.commit()

import json

def set_answer_to_last_question(con,userid, answer):
    cur = con.cursor()
    cur.execute("SELECT dataset, dataitem, detail FROM qa WHERE asked_last = 1 AND userid = ?;",(userid,))
    sqldata = cur.fetchone();
    #if sqldata is None: #silently fail to set the answer
    #    return
    cur.close()
    data = {'dataset':sqldata[0],'dataitem':sqldata[1],'detail':sqldata[2],'answer':answer}
    data = json.loads(query_api('processanswer',data))
    cur = con.cursor()
    cur.execute('UPDATE qa SET answer = ?, detail = ?, asked_last = 0 WHERE userid = ? AND asked_last = 1;',(data['answer'],data['detail'],userid,)); 
    cur.close()
    con.commit()
