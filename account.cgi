import web_helper_functions as whf

sid,cookie = whf.get_session_id();
print cookie
print 'Content-Type: text/html\n';
print '''<h2>Scikic: Account</h2>
<div style="width:50%; margin-left:25%; margin-right:25%;">
<h2>Account</h2>
<p>
In future versions of the Scikic this page will allow you to view, edit and delete your data, and will explain what inferences are possible using this data and how they work.
</p>
<p>If you want to delete your data from the scikic, please <a href="mailto:scikic@michaeltsmith.org.uk">email us</a>.</p>
</body>
</html>'''
