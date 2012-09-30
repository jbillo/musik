$(document).ready(function() {
	$('.validate-error').hide();
});

$('#importmedia-form').submit(function() {
	$('.validate-error').html('');
	$('.validate-error').hide();
	
	// Validate path
	if ($('#path').val() == '') {
		$('#validate-error-top').html("Please provide a valid path to continue.");
		$('.validate-error').show();
		$('#path').focus();
		return false;
	}
	
	return true;
});
