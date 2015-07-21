conversation_item_id = 0

var timer = 0;

function opacity_calc() {
      op = 0.95;
      for (i = conversation_item_id-2; i >= 0; i --) {
        $('div#item'+i.toString()).css('opacity',op.toString());
        op = op - 0.18;
      }
}

var keystrokeclockstart = 0;
var keystrokerecord = [];

function startKeyStrokeClock() {
  keystrokeclockstart = $.now();
  keystrokerecord = [];
}

function recordKey(desc,key) {
  time = $.now()-keystrokeclockstart;
  keystrokerecord.push({'event':desc,'key':key,'time':time})
}


function replymsg() {
   timer = setInterval(add_thinking_message, 5000);
   // $('div.loader').css("visibility","visible");
    $('div.loader').fadeTo('slow', 1);
    $.ajax({
	method: "GET",
	url: "index.cgi?ajax=on",
	data: {'reply':$('input#chatbox').val(),keystrokerecord:JSON.stringify(keystrokerecord)}
    })
    .done(function( msg ) {
      clearTimeout(timer);
      startKeyStrokeClock();
      $('input#chatbox').val(""); //clear the input box
      $('div#conversation').append(msg);
      if ($('div.reply').last().attr('id')==undefined) {
        $('div.reply').last().attr('id','item'+conversation_item_id.toString());
        conversation_item_id ++;
      }
      $('div.msg').last().attr('id','item'+(conversation_item_id).toString());
      conversation_item_id ++;
      opacity_calc();
   //   $('div.loader').css("visibility","hidden");
      $('div.loader').fadeTo('slow', 0);
      if (msg.indexOf("<!--query-->")>=0)
      {
   //     $('div.loader').css("visibility","visible"); //TODO Make them appear when it's having a good think.
        $('div.loader').fadeTo('slow', 1);
        replymsg(); //the server wants to say something else!
      }   
    });
}

function add_thinking_message() {
  msg = 'Thinking...';
  r = conversation_item_id % 10;
  if (r==9) {msg = 'So...'; }
  if (r==8) { msg = 'Looking in my crystal ball...'; }
  if (r==7) { msg = 'Hmm. Interesting.'; }
  if (r==6) { msg = 'I must take a little more time...'; }
  if (r==5) { msg = 'You are difficult to read...'; }
  if (r==4) { msg = 'Soon I will have the answer'; }
  if (r==3) { msg = 'I\'m looking into the swirling path of life.'; }
  if (r==2) { msg = 'Ok...'; }
  if (r==1) { msg = 'I\'ve nearly an answer.'; }
  if (r==0) { msg = 'I\'m just thinking...'; }
  $('div#conversation').append('<div class="msg"><span class="innermsg">'+msg+'</span></div>');
  $('div.msg').last().attr('id','item'+(conversation_item_id).toString());
  conversation_item_id = conversation_item_id + 1;
  opacity_calc();
}

function sendfacebook(data) {
    $.ajax({
	method: "POST", //posting the data as it's too big to GET
	url: "index.cgi",
	data: {'facebook':'on', reply:data}
    })
    .done(function( msg ) {
      //nothing to do
    });
}

function trypaging(data) {
    if(data.likes.paging.hasOwnProperty('next')){
        $.getJSON( data.likes.paging.next, function( morelikes ) {
          $.merge(data.likes.data, morelikes.data) //append our new data
          data.likes.paging = morelikes.paging //update the paging info too
          trypaging(data)
        });
    }
    else
    {
        sendfacebook(JSON.stringify(data));
    }
}

$(document).ready(function() {
 replymsg();
 $('button#reply').click(function() {replymsg();});
//the 'enter' key would normally trigger a submit (if it existed). We're using AJAX and a button, so have to do this manually.
 $("#chatbox").keyup(function(event){
    recordKey('up',event.keyCode);
    if(event.keyCode == 13){
        $("#reply").click();
    }
 });
 $("#chatbox").keydown(function(event){
    recordKey('down',event.keyCode);
 });
});


$(document).ready(function() {
/*--------Facebook connection code------*/
window.fbAsyncInit = function() {
	FB.init({
		appId      : '380462442159554',
		xfbml      : true,
		version    : 'v2.3'
   	});

	function onLogin(response) {
		if (response.status == 'connected') {
            FB.api('/me?fields=picture', function(data) {
                var style = $('<style>div.replypic { background-image: url("'+data.picture.data.url+'"); }</style>');
                $('html > head').append(style);
            });
			FB.api('/me?fields=first_name', function(data) {
            //     console.log('Have name');  
				//var welcomeBlock = document.getElementById('conversation');
                  if (conversation_item_id==0) {
                    msg = 'Hello, ' + data.first_name + '!';
                    $('div#conversation').prepend('<div class="msg"><span class="innermsg">'+msg+'</span></div>');
                    $('div.msg').last().attr('id','item'+(conversation_item_id).toString());
                    conversation_item_id = conversation_item_id + 1;
                  }
	    		});
//unclear if we need summary=true
			FB.api('/me?fields=id,bio,email,first_name,gender,last_name,link,locale,name,timezone,updated_time,verified,birthday,likes', function(data) {
              //      console.log('Trying to get data');  
              //      console.log(JSON.stringify(data));
                    trypaging(data)
 
	    		});
	  	}
       // replymsg();
	}
//see https://developers.facebook.com/docs/reference/fql/permissions
//see https://developers.facebook.com/docs/graph-api/reference/user

	FB.getLoginStatus(function(response) {
		// Check login status on load, and if the user is
		// already logged in, go directly to the welcome message.
		if (response.status == 'connected') {
			onLogin(response);
		} else {
	    	// Otherwise, show Login dialog first.
		  	FB.login(function(response) {
		 		onLogin(response);
		 	}, {scope: 'user_birthday, user_likes'}); //{scope: 'user_friends, email, user_birthday, user_about_me, user_likes, user_photos'});
		}
	});
  };

  (function(d, s, id){
     var js, fjs = d.getElementsByTagName(s)[0];
     if (d.getElementById(id)) {return;}
     js = d.createElement(s); js.id = id;
     js.src = "//connect.facebook.net/en_US/sdk.js";
     fjs.parentNode.insertBefore(js, fjs);
   }(document, 'script', 'facebook-jssdk'));
/*--------------------------------------*/
});
