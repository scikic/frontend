function send(data) {
    $.ajax({
	method: "GET",
	url: "account.cgi?ajax=on",
	data: {reply:data}
    })
    .done(function( msg ) {
        $('span.clickfeedback').fadeOut(function() {$(this).html('Selection updated').fadeIn(function() {$(this).delay(1000).fadeOut();}); });
      //nothing to do
    });
}

$("body").on("click", "div.option", function(){
//    alert($(this).attr('id'));
    $('div.option').removeClass('selected');
    $(this).addClass('selected');
    send({'policy':$(this).attr('id')});
});
