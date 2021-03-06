import web_helper_functions as whf
import config
import logging
logging.basicConfig(filename=config.loggingFile,level=logging.DEBUG)

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
        return None #"No more questions!";
    dataset = data[0]
    dataitem = data[1]
    detail = data[2]    
    data = {"dataset":data[0],"dataitem":data[1],"detail":data[2]}
    query_result = query_api('questionstring',data)
    try:
        output = json.loads(query_result)
    except ValueError:
        import sys
        print >>sys.stderr, "While getting question string, unable to parse JSON from "+query_result
        return None # ('question':'no question','') #not sure what to return yet if problem occurs TODO 
    return output

def do_inference(con,userid):
    data = get_data_structure(con,userid)
    res = query_api('inference',data)
    try:
        output = json.loads(res)
    except ValueError:
        import sys
        print >>sys.stderr, "While performing inference, unable to parse JSON from "+res
        return ([],[],[])

    features = output['features']
    insights = output['insights']
    facts = output['facts']

    return features, insights, facts

def get_data_structure(con,userid):
    cur = con.cursor()
    results = cur.execute('SELECT dataset, dataitem, detail, answer, processed FROM qa WHERE userid=? AND asked_last=0;',(userid,)); #asked_last=0 -> don't want datasets without answers. and don't want answers that have already been processed.
    data = {}
    questions_asked = []
    unprocessed_questions = []
    for it in results:
        logging.info('   adding question to list of questions already answered that haven\'t been put into facts: %s,%s,%s,%s' % (it[0],it[1],it[2],it[3]))
        if it[4]==0: #it's not yet been processed
            unprocessed_questions.append({'dataset':it[0],'dataitem':it[1],'detail':it[2],'answer':it[3]}) #ones that need processing are added to this list
        questions_asked.append({'dataset':it[0],'dataitem':it[1],'detail':it[2],'answer':it[3]}) #all questions are added to this list

    results = cur.execute('SELECT fact FROM facts WHERE userid=?;',(userid,)); 
    row = results.fetchone()
    if row!=None:
        jsonfact = row[0]
        try:          
            facts = json.loads(jsonfact)
        except ValueError:
            import sys
            print >>sys.stderr, "While picking question, unable to parse JSON from (fact) "+jsonfact
            return {'dataset':None,'dataitem':None,'detail':None,'answer':None}
    else:
        facts = {}

    data = {'unprocessed_questions':unprocessed_questions,'questions_asked':questions_asked,'facts':facts}
    cur.close()
    return data

def pick_question(con,userid):
    data = get_data_structure(con,userid)
    resjson = query_api('question',data)    
    cur = con.cursor()
    try:
        logging.info('    processing...')
        res = json.loads(resjson)
        question = res['question']
        fact = res['facts']
        factjson = json.dumps(fact)
        logging.info('    updating qa...')
        cur.execute('UPDATE qa SET processed=1 WHERE userid=? AND asked_last=0 AND processed=0;',(userid,));
        cur.execute('INSERT OR REPLACE INTO facts (fact, userid) VALUES (?,?);',(factjson,userid,));
    except ValueError:
        import sys
        print >>sys.stderr, "While picking question, unable to parse JSON from "+resjson
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
    if sqldata==None:
        return #there is no question to assign an answer to, so we'll quietly return (chances are we displayed a 'continue' question, that doesn't really have a question assigned).
    data = {'dataset':sqldata[0],'dataitem':sqldata[1],'detail':sqldata[2],'answer':answer}
#    data = json.loads(query_api('processanswer',data)) #deprecated and now removed.
    cur = con.cursor()
    cur.execute('UPDATE qa SET answer = ?, detail = ?, asked_last = 0 WHERE userid = ? AND asked_last = 1;',(data['answer'],data['detail'],userid,)); 
    cur.close()
    con.commit()
    return data
