var latlng = L.latLng(5.4163, 100.3328);

var autocomp_opt={
		 source: function(request, response) {
			$.ajax({
				url: "https://nominatim.openstreetmap.org/search",
				dataType: "json",
				type: "get",
				data: {
					'format': 'json',
					'countrycodes': 'MY',
					'q': $('#locationsearch').val(),
					'limit': 4
				},
			}).done(function (data) {
				response($.map(data, function(item) {
						return {
								label: item.display_name,
								value: item.display_name
						};
					}));
			});
		},
	};

$(function() {
	$("#locationsearch").autocomplete(autocomp_opt);
	$('#locationsearch').on('keypress', function(e){
		if(e.keyCode == 13)
		{
			$(this).trigger("enterKey");
		}
	});
	$('#locationsearch').bind("enterKey",function(e){
		L.Realtime.reqwest({
			url: 'https://nominatim.openstreetmap.org/search',
			type: 'json',
			method: 'get',
			data: {
				'format': 'json',
				'countrycodes': 'MY',
				'q': $('#locationsearch').val(),
				'limit': 1
			},
			crossOrigin: true,
			success: function (resp) {
				latlng = L.latLng(resp[0].lat, resp[0].lon);
				set_global_latlng({'latlng': latlng});
			}
		});
		$('html, body').animate({
			scrollTop: $("#mapid").offset().top
		}, 1000);
	});
});

var currentbutton = function() {
	map.locate({
		'setView': true
	});
	$('html, body').animate({
		scrollTop: $("#mapid").offset().top
	}, 1000);
};

$(document).ready(function() {
	$('input').onfocus = function () {
        window.scrollTo(0, 0);
        document.body.scrollTop = 0;
    };
});