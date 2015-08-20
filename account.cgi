#!/usr/bin/env python

import web_helper_functions as whf
import sqlite3 as lite
import config
import cgi

def set_user_policy(con, userid, policy):
    import sys
    print >>sys.stderr, (userid, policy)
    cur = con.cursor()
    results = cur.execute('INSERT OR REPLACE INTO users (user, policy) VALUES (?,?);',(userid,policy))
    cur.close()
    con.commit()

def get_user_policy(con, userid):
    cur = con.cursor()
    results = cur.execute('SELECT policy FROM users WHERE user=?;',(userid,))
    row = results.fetchone()
    policy = 0 #default (keep for scikic)
    if row!=None:
        if row[0]!=None:
            policy = row[0] #1=delete, 2=donate
    return policy

def get_user_answers(con, userid):
    cur = con.cursor()
    results = cur.execute('SELECT dataset, dataitem, detail, answer FROM qa WHERE userid=? AND asked_last=0;',(userid,))
    data = []
    for r in results:
        if r[3]!=None:
           data.append([','.join(r[0:3]),r[3]])
    table = {'header':['question','answer'],'data':data}
    return table

def make_table(table):
    hd = table['header']
    data = table['data']
    res = ""
    res += "<table>"
    res += "<tr>"
    for h in hd:
        res+= "<th>"+h+"</th>"
    res+="</tr>"
    for row in data:
        res+= "<tr>"
        for r in row:
            if r == None:
                r = 'No Information'
            if len(r)>30:
                r = r[0:30]+'...'
            res+="<td>"+r+"</td>"                
        res+= "</tr>"
    res+="</table>"
    return res

def gen_main_page(con, userid):
    res = ''
    res+= '<h1>Scikic: Account</h1>'
    res+= '<div style="width:50%; margin-left:25%; margin-right:25%;">'
    res+= '<h2>Information you\'ve provided</h2>'
    res+= '<p>'
    res+= 'Below is a table of the information you have provided (currently displayed in "raw" form) or information that your browser made available:'
    res+= make_table(get_user_answers(con,userid))
    res+= '</p><br />'
    res+= '<h2>Control over this information</h2>'
    res+= '<p>After you have finished with the scikic what will happen to your data?'
    res+= '<div width="100%">';
    policy = get_user_policy(con, userid)
    optionnumbers = [1,0,2]
    optiontexts = ['It will be deleted within 7 days.','It will be used by the scikic to improve its insights.','It will be anonymised and made available for research in the field of personalised medicine.']
    for n,text in zip(optionnumbers,optiontexts):
        classtext = ''
        if n==policy:
            classtext = ' selected'
        
        res+= '<div class="option%s" id="opt_%d"><img src="opt%d.png"><br /><span class="option">%s</span></div>' % ( classtext, n, n, text)
    print '<script src="jquery-1.11.2.min.js"></script>';
    print '<script src="account.js"></script>';
    res+= '</table>';
    res += '</p>';

    res += '<h2>Future Control</h2>'
    res += '<p>If in the future you want to change this choice, you may need to <a href="login.html">log in</a>. You can do that with this password:</p>'
    return res


sid,cookie = whf.get_session_id();
con = lite.connect(config.pathToData + 'psych.db') 
userid = whf.get_user_id(con,sid)
form = cgi.FieldStorage()

print cookie
print 'Content-Type: text/html\n';
if ('ajax' in form):
    if 'reply[policy]' in form:
        newpolicy = int(form['reply[policy]'].value[4])
        set_user_policy(con, userid, newpolicy)
else:
    print '<html><head><title>Scikic: Account</title>';
    print '<link rel="stylesheet" href="style.css" type="text/css" media="screen">';
    print '<link rel="stylesheet" href="animate.css" type="text/css">';
    print '</head><body>';
    print gen_main_page(con, userid)
    import footer
    print footer.text()
    print '</body></html>'
