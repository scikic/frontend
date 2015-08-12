#!/usr/bin/env python

#TODO: Figure out which modules are needed!

#TODO: Find out why these have to be before pymc to avoid "OSError: Could not find library c or load any of its variants []" error.
from shapely.geometry import Point
from shapely.geometry import Polygon

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

#connect to database

con = lite.connect(config.pathToData + 'psych.db') 
form = cgi.FieldStorage()

def gen_main_form():
    sid,cookie = whf.get_session_id();
    print cookie
    print 'Content-Type: text/html\n';
    print '<html><head><title>Psychic</title>';
    print '<link rel="stylesheet" href="style.css" type="text/css" media="screen">';
    print '<link rel="stylesheet" href="animate.css" type="text/css">';
    print '</head><body>';


    print '<script src="jquery-1.11.2.min.js"></script>';
    print '<script src="psych.js"></script>';
    print '<div class="page"><div class="pageinner"><div class="pageinnerinner">';
    #print '<h1>Psychoc Sally</h1>';
    print '<div id="conversation"></div>';
    print '<div id="response_section">';
    print '<div class="selects"></div>';
    print '<span class="textbox">';
    print '<input type="text" id="chatbox" size="27" autofocus />';
    print '<script>if (!("autofocus" in document.createElement("input"))) {document.getElementById("chatbox").focus(); }</script>'; #does autofocus for old versions of IE.
    print '<button id="reply">Reply</button>';
    print '</span>'; #end of textbox
    print '</div>'; #end of "response_section"
    print '<br />';
    print '<div class="loader"><div class="circle">&nbsp;</div><div class="circle">&nbsp;</div><div class="circle">&nbsp;</div><div class="circle">&nbsp;</div></div>';
    print '</div>';
    print '</div></div>';
    print '<span class="footertextright">Background image provided by <a href="https://www.flickr.com/photos/kwarz/14628848258">zeitfaenger.at</a>. Avatar image provided by <a href="http://clipartist.net/svg/emily-the-strange-emily-the-strange-awesome-rss-openclipart-org-commons-wikimedia-org/">clipartist.net</a>.</span>';
    print '<span class="footertextleft"><a href="privacy.html">Privacy</a> | <a href="tos.html">Terms</a> | <a href="help.html">Help</a> | <a href="account.cgi">Account</a></span>';
    print '</body></html>';

def process_ajax():
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
        msg = 'Welcome to this psychic experience (v0.1). I will ask you some questions, and, using my psychic powers (and maths) I shall predict the unpredictable!<br/></br>'# <!--query-->';
        continues = True
        whf.set_conversation_state(con,sid,1)
    if (state==1):
        if ('reply' in form):
            ohf.set_answer_to_last_question(con, userid, form['reply'].value);

        if (data[0]>1): #12
            msg = 'Enough questions! I shall now peer into my crystal ball of now, to find your age... (this might take me a while)' #<!--query-->';
            continues = True
            whf.set_conversation_state(con,sid,2)
        else:
            moreQavailable = True
            if (not whf.outstanding_question(con,userid)):
                moreQavailable = False
                question = ohf.pick_question(con,userid);
                if (question['dataset']!=None):
                    moreQavailable = True
                    whf.add_question(con, userid, question['dataset'], question['dataitem'], question['detail']);
                else:
                    #not found any new questions. TODO: We shouldn't really get into this situation, as we should
                    #have more questions always available. However, if we do; set conversation to state=1, to reveal what
                    #we know.
                    whf.set_conversation_state(con,sid,2)
                    msg = "I've no more questions to ask!";
                    continues = True
            if moreQavailable:
                question = ohf.get_last_question_string(con,userid); 
                msg = question['question']
                question_details = question
                
    if (state==2):
        output, insights, facts = ohf.do_inference(con,userid);
        msg = '<br/>'.join(insights)
        continues = True
        whf.set_conversation_state(con,sid,3)
    if (state==3):
        if ('reply' in form):
            ans = form['reply'].value
            msg = "%s? Interesting." % ans # <!--query-->" % ans; #TODO: SANITISE INPUT
            continues = True
            ohf.set_answer_to_last_question(con, userid, ans);
        else:
            cur = con.cursor()
            results = cur.execute('SELECT dataitem FROM qa WHERE dataset = "direct" AND userid = ?', (userid,));
            dataitems = ['age','religion']
            for data in results:
                dataitems.remove(data[0])
            cur.close()
            if (len(dataitems)==0):
                whf.set_conversation_state(con,sid,4)
                msg = "One more thing..." # <!--query-->";
                continues = True
            else:
                if (dataitems[0]=='age'):
                    msg = "I wonder if I was correct about your age. What is your actual age (if you don't mind me asking?)";
                    question_details = {'type':'text'}
                    whf.add_question(con, userid, 'direct', 'age', ''); 
                if (dataitems[0]=='religion'):
                    msg = "I wonder if I was correct about your religion. What religion (or none) do you identify as?";
                    question_details = {'type':'text'} 
                    whf.add_question(con, userid, 'direct', 'religion', ''); 
    if (state==4):
        msg = "If it's ok with you, we would like to keep these answers to improve our psychic abilities in future. We won't use your data for anything else, or pass it on to anyone else.<br/>";
        msg+= "If you want us to delete the data, you can type 'delete' here, now or later. Or in the future, <a href='scikic@michaeltsmith.org.uk'>contact</a> us."
        question_details = {'type':'text'} 
        whf.set_conversation_state(con,sid,5)
    if (state==5):
        msg = "Thanks for helping with the psychic experiment: It's now complete. To find out more, please follow us on twitter."
        question_details = {'type':'text'}
#       msg = 'Enough questions, please visit the <a href="index.cgi?infer=on&userid=%d&feature=age">calculation</a> to see an estimate of your age. It\'s quite slow: Please be patient.' % userid;
    
     
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
#stick this in the database
    import json
    whf.set_answer_to_new_question(con, userid, 'facebook', 'data', '', json.dumps(data)) #form['reply[birthday]'].value)


def process_env_data():
    sid,cookie = whf.get_session_id()
#    print cookie
#    print 'Content-Type: text/html\n'
#    print '<html><body>'    
    userid = whf.get_user_id(con,sid); 
    import json
    import os
    user_agent_info = os.environ
    whf.set_answer_to_new_question(con, userid, 'user_agent_info', 'data', '', str(user_agent_info)) #TODO optimise: Only do this if this row isn't in the database already.

process_env_data()
if ('facebook' in form):
    process_facebook()
elif ('ajax' in form):
    process_ajax()
elif ('setup' in form): #If setup is passed, then we download all the stuff the site might need.
    ohf.setupdatabase(con)
else:
    gen_main_form()



con.commit();
con.close();
