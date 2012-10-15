$(document).ready(function() {

	//load artists with an ajax call
	//TODO: generate links to artist pages
	$.get("/api/artists/", function(data){
		var html = '<ul>'
		for (var a in data) {
			html += '<li>' + data[a]['name'] + '</li>'
		}
		html += '</ul>'
		$('.artist-list').html(html);
	}, "json");

	//load albums with an ajax call
	//TOOD: generate links to album pages
	$.get("/api/albums/", function(data){
		var html = '<ul>'
		for (var a in data) {
			html += '<li>' + data[a]['title'] + '</li>'
		}
		html += '</ul>'
		$('.album-list').html(html);
	}, "json");
});