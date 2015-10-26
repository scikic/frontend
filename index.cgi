#!/usr/bin/env python

#TODO: Figure out which modules are needed!
import sha, time, Cookie, os
import sqlite3 as lite
import uuid
import pandas as pd
import json
import random
import cgi
import web_helper_functions as whf
import other_helper_functions as ohf
import config
import json

import logging
logging.basicConfig(filename=config.loggingFile,level=logging.DEBUG)

#connect to database

con = lite.connect(config.pathToData + 'psych.db') 
form = cgi.FieldStorage()

def gen_main_form():
    logging.info('generating_main_form')
    sid,cookie = whf.get_session_id();
    print cookie
    print 'Content-Type: text/html\n';
    print '<html><head><title>Scikic</title>';
    print '<meta property="og:url"           content="https://www.scikic.org" />';
    print '<meta property="og:type"          content="website" />';
    print '<meta property="og:title"         content="Scikic" />';
    print '<meta property="og:description"   content="Welcome to the scikic experience. I will ask you some questions, and, using my psychic powers (and maths) I shall predict the unpredictable!" />';
    print '<meta property="og:image"         content="http://www.scikic.org/scikic/avatar_small.png" />';

    print '<link rel="stylesheet" href="style.css" type="text/css" media="screen">';
    print '<link rel="stylesheet" href="animate.css" type="text/css">';
    print '<meta name=viewport content="width=500">';
    print '</head><body>';


    print '<script src="jquery-1.11.2.min.js"></script>';
    print '<script src="psych.js"></script>';
    print '<div class="page"><div class="pageinner"><div class="pageinnerinner">';
    print '<div id="conversation"></div>';
    print '<div id="response_section">';
    print '<div class="selects"></div>';
    print '<div class="multiselects"></div>';
    print '<span class="textbox">';
    print '<input type="text" id="chatbox" size="27" autofocus />';
    print '<script>if (!("autofocus" in document.createElement("input"))) {document.getElementById("chatbox").focus(); }</script>'; #does autofocus for old versions of IE.
    print '<button id="reply">Reply</button>';
    print '</span>'; #end of textbox
    print '<div class="skipbuttondiv" alt="Skip Question: Click if you don\'t want to answer the question."><button id="skip">Skip</button></div>';
    print '</div>'; #end of "response_section"

    print '<br />';
    print '<div class="loader"><div class="circle">&nbsp;</div><div class="circle">&nbsp;</div><div class="circle">&nbsp;</div><div class="circle">&nbsp;</div></div>';
    print '</div>';
    print '</div></div>';
    import footer
    print footer.text()
    print '</body></html>',

def process_ajax():
    logging.info('process_ajax')
    sid,cookie = whf.get_session_id();
    print cookie
    print 'Content-Type: text/html\n'
   # print '<html><body>'
  
    msg = '';
    reply = '';
    continues = False;
    question_details = {'type':'none'}
    userid = whf.get_user_id(con,sid);
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM qa WHERE userid=?;',(userid,));
    data = cur.fetchone();	
    cur.close()
    state = whf.get_conversation_state(con,sid)

#user can delete the data at any point
    if ('keystrokerecord' in form):
        cur = con.cursor()
        keystrokes = form['keystrokerecord'].value;
        import datetime
        dt = str(datetime.datetime.now());
        cur.execute('INSERT INTO keystrokes (qid, keystrokes, date) VALUES ((SELECT qid FROM qa WHERE userid=? AND asked_last=1), ?, ?);',(userid,keystrokes,dt))
        cur.close()
        con.commit()
    if ('reply' in form):
        if form['reply'].value.upper()[0:3]=='SET':
            a = form['reply'].value.upper().split(',')
            if (a[1]=='NAME'):
                temp = '{"reply[first_name]": "%s"}' % a[2]
                cur = con.cursor()
                cur.execute("UPDATE qa SET answer=? WHERE userid=? AND dataset='facebook'",(temp,userid))
                cur.close()
                con.commit()
                msg = "Updating names to %s." % a[2]
                response = {'message':msg,'reply':reply}
                print json.dumps(response)
                return

        if form['reply'].value.upper()=='DELETE':
            msg = "Your data has been deleted."
            ohf.delete_users_data(con,userid)
            whf.set_conversation_state(con,sid,100)
            state = -1;
    if (state==100):
        msg = "The answers you gave to us about you have been erased.";
    if (state==0):
        if ('reply' not in form):
            msg = 'Welcome to the <b>scikic</b> experience. I will ask you some questions, and, using my psychic powers (and maths) I shall predict the unpredictable!<br/><br /><a href="about.html">Learn more</a>. \n<br/><br /><b>The data you enter will be stored by the scikic to help improve it in future.</b><br />I may ask some personal questions. <br />You may choose not to answer some questions.<br /> If you want to erase your data from the scikic later, you can.<br /><br /><b>Do you want to continue?</b>'
            continues = False
            question_details = {'type':'select', 'options':['Yes','No']}
#            question_details = {'type':'multiselect', 'options':['Yes','No']}
        else:
            if form['reply'].value.upper()=='YES':
                msg = 'Thank you!<br/> Let the Scikic experience begin...'
                continues = True
                whf.set_conversation_state(con,sid,1)
            else:
                msg = 'Thank you for your interest in the Scikic. <br />Good bye.'
                continues = False
    if (state==1):
        if ('reply' in form):
            logging.info('handling reply')
            ohf.set_answer_to_last_question(con, userid, form['reply'].value);

        if (data[0] % 9==0): #12
            msg = 'Enough questions! I shall now peer into my crystal ball... (this might take me a while)' #<!--query-->';
            continues = True
            whf.set_conversation_state(con,sid,2)
        else:
            logging.info('getting question...')
            moreQavailable = True
            if (not whf.outstanding_question(con,userid)): #is there isn't a question we're awaiting an answer to...
                logging.info('picking question...')
                moreQavailable = False
                question = ohf.pick_question(con,userid);
                if (question['dataset']!=None):
                    moreQavailable = True
                    whf.add_question(con, userid, question['dataset'], question['dataitem'], question['detail']);
                else:
                    #not found any new questions. TODO: We shouldn't really get into this situation, as we should
                    #have more questions always available. However, if we do; set conversation to state=2, to reveal what
                    #we know.
                    whf.set_conversation_state(con,sid,2)
                    msg = "I've no more questions to ask!";
                    continues = True
            if moreQavailable: #if there is (supposed) to be a question that we've not yet answered...
                question = ohf.get_last_question_string(con,userid); 
                if question==None:
                    whf.set_conversation_state(con,sid,2)
                    msg = 'I have no more questions to ask.' #TODO
                    question_details = {'type':'none'}
                else:
                    msg = question['question']
                    question_details = question
                
    if (state==2):
        output, insights, facts = ohf.do_inference(con,userid);
        msg = '<br/>'.join(insights)
        #continues = True
        whf.set_conversation_state(con,sid,2.5)
        continues = False
        question_details = {'type':'select', 'options':['Continue']}
    if (state==2.5):
        msg = 'You were very difficult to read...'
        continues = True
        whf.set_conversation_state(con,sid,3)
    if (state==3):
        logging.info('state=3');
        if ('reply' in form):
            ans = form['reply'].value
            logging.info('reply in form, %s' % ans);
            msg = "%s? Interesting." % ans # <!--query-->" % ans; #TODO: SANITISE INPUT
            continues = True
            ohf.set_answer_to_last_question(con, userid, ans);
        else:
            logging.info('reply NOT in form');
            if (not whf.outstanding_question(con,userid)):    
                logging.info('no outstanding question');         
                cur = con.cursor()
                results = cur.execute('SELECT dataitem FROM qa WHERE dataset = "direct" AND userid = ?', (userid,));
                dataitems = ['age'] #,'religion'] #Disabled religion question (can't collect this!)
                for data in results:
                    dataitems.remove(data[0])
                cur.close()
                logging.info('    %d items of [age,religion] available to ask' % len(dataitems));
                if (len(dataitems)==0):
                    logging.info('No dataitems available to ask, skipping to next state...');
                    whf.set_conversation_state(con,sid,4)
                    msg = "One more thing..." # <!--query-->";
                    continues = True
                else:
                    logging.info('    dataitems exist to ask...');
                    if (dataitems[0]=='age'):
                        logging.info('    adding age question...');
                        whf.add_question(con, userid, 'direct', 'age', ''); 
                    if (dataitems[0]=='religion'):
                        logging.info('    adding religion question...');
                        whf.add_question(con, userid, 'direct', 'religion', ''); 
            if (whf.outstanding_question(con,userid)):
                logging.info('outstanding questions exist');
                question = ohf.get_last_question_string(con,userid); 
                logging.info('last question...%s' % question);
                msg = question['question']
                question_details = question
    if (state==4):
        msg = "If it's ok with you, we would like to keep these answers to improve our psychic abilities in future. We won't use your data for anything else, or pass it on to anyone else.\n<br/>";
        msg+= "We would also like to be able to use this data, in an anonymised form, for future research into personalised health and medicine. <a href='account.cgi'>Choose how you want us to use your data</a>.\nIf you have any questions, please <a href='mailto:scikic@michaeltsmith.org.uk'>contact</a> us."
#        question_details = {'type':'text'}
        question_details = {'type':'select', 'options':['Continue']}
        whf.set_conversation_state(con,sid,5)
    if (state==5):
        msg = 'Thanks for helping with the scikic experiment. Feel free to <a href="#"><span class="fbshare">share on facebook</span></a> and continue gaining insights...'
        whf.set_conversation_state(con,sid,1) 
        question_details = {'type':'select', 'options':['Continue']}

    if ('reply' in form):
        reply = form['reply'].value
        #reply = '<div class="reply"><span class="innerreply">'+form['reply'].value+'</span><div class="replypic"></div></div>';
   #msg = '<div class="msg"><span class="innermsg">'+msg+'</span></div>';

    response = {'message':msg,'reply':reply,'continues':continues,'details':question_details}
    print json.dumps(response)

def process_facebook():
    if not whf.in_session():
        print 'Content-Type: text/html\n'
        print '<html><body>Cookie missing</body></html>'
        return #we'll sort out facebook once we have a session id (it's not been created and added to a cookie yet).
    sid,cookie = whf.get_session_id();
    print cookie
    print 'Content-Type: text/html\n'
    print '<html><body>'    
    userid = whf.get_user_id(con,sid);
#convert tricky cgi form into simple dictionary.
    data = {}
    for key in form:
        data[key] = form[key].value

    #get their facebook id
    fbdata = json.loads(data['reply'])
    fbid = fbdata['id']
    whf.set_facebook_id(con,userid,sid,fbid)
#stick this in the database

    whf.set_answer_to_new_question(con, userid, 'facebook', 'data', '', json.dumps(data)) #form['reply[birthday]'].value)

def process_env_data():
    sid,cookie = whf.get_session_id()
#    print cookie
#    print 'Content-Type: text/html\n'
#    print '<html><body>'    
    userid = whf.get_user_id(con,sid); 
    import json
    import os
    envs = os.environ
    user_agent_info = {}
    for env in envs:
        user_agent_info [env] = envs[env]
    logging.info('added user_agent_info %s' % type(user_agent_info))
    logging.info('added user_agent_info %s' % user_agent_info)
    whf.set_answer_to_new_question(con, userid, 'user_agent_info', 'data', '', json.dumps(user_agent_info)) #TODO optimise: Only do this if this row isn't in the database already.

process_env_data()
if ('facebook' in form):
    process_facebook()
elif ('ajax' in form):
    process_ajax()
#elif ('setup' in form): #If setup is passed, then we download all the stuff the site might need.
#    ohf.setupdatabase(con)
else:
    gen_main_form()



con.commit();
con.close();
