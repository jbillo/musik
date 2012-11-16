$(document).ready(function() {
	$('.validate-error').hide();
});

$('#importmedia-form').submit(function(event) {

	//stop the form from submitting normally
	event.preventDefault();

	$('.validate-error').html('');
	$('.validate-error').hide();

	// TODO: better path validation is a plus
	if ($('#path').val() == '') {
		$('#validate-error-top').html("Please provide a valid path to continue.");
		$('.validate-error').show();
		$('#path').focus();
		return false;
	}

	//TODO: error and success handling need some work
	$.post('/api/importmedia/directory', $('#importmedia-form').serialize())
	 .success(function() {
	 	alert('great success!');
	 })
	 .error(function(jqXHR) {
	 	if (jqXHR.status == 404) {
	 		alert(jqXHR.responseText);
	 	}
	 });

	return true;
});
