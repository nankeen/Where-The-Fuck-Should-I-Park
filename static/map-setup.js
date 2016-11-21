var southWest = L.latLng(5.7, 100.0);
var northEast = L.latLng(5.0, 100.7);
var bound = L.latLngBounds(southWest, northEast);

function get_nearby(sucs, err) {
	L.Realtime.reqwest({
		url: '/geojson/nodes/near/1/',
		type: 'json',
		method: 'get',
		data: {lat: window.latlng.lat, lng: window.latlng.lng},
		crossOrigin: true,
		success: function (resp) {
			sucs(resp);
		}
	});
}

var map = L.map('mapid', {
	center: latlng,
	zoom: 12,
	maxBound: bound,
	}),
	realtime = L.realtime(get_nearby, {
		interval: 5 * 1000,
		pointToLayer: function(feature, latlng) {
			marker = new L.CircleMarker(latlng, {
				radius: 5,
				color: feature.properties.color,
				fillOpacity: 0.85});
			marker.setStyle({'color': feature.properties.color});
			return marker;
		},
	}).addTo(map);

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
	attribution: 'Imagery from <a href="http://mapbox.com/about/maps/">MapBox</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
	minZoom: 11,
	maxZoom: 20,
	id: 'andrewrawr.25b6c5gk',
	accessToken: 'pk.eyJ1IjoiYW5kcmV3cmF3ciIsImEiOiJjaXZvcW9yZmkwMWV5MnlxdnpoeXU3OTB6In0.0AKBzCRQm8VKtjVNwx6yAA'
}).addTo(map);

realtime.on('update', function(e) {
		popupContent = function(fId) {
			var feature = e.features[fId];
			var navigation = '<br/><a href="geo:' + feature.geometry.coordinates[1] + ',' +
			feature.geometry.coordinates[0] +
			'" target="_blank">Navigate here</a>';
			var iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
			if (iOS) {
				navigation = '<br/><a href="comgooglemaps://?center=' + feature.geometry.coordinates[1]+ ',' +
				feature.geometry.coordinates[0] +
				'" target="_blank">Navigate here</a>';
			}
			if (feature.properties.available > 1) {
				return feature.properties.available + ' spots free at ' + feature.properties.name + ' since ' +
				feature.properties.since + navigation;
			}
			else if (feature.properties.available === 1) {
				return 'A spot free at ' + feature.properties.name + ' since ' + feature.properties.since + navigation;
			}
			else {
				return 'No spots available since ' + feature.properties.since + navigation;
			}
			
		};
		bindFeaturePopup = function(fId) {
			realtime.getLayer(fId).bindPopup(popupContent(fId));
		};
		updateFeaturePopup = function(fId) {
			realtime.getLayer(fId).getPopup().setContent(popupContent(fId));
			realtime.getLayer(fId).setStyle({'color': e.features[fId].properties.color});
		};

	Object.keys(e.enter).forEach(bindFeaturePopup);
	Object.keys(e.update).forEach(updateFeaturePopup);
});

function set_global_latlng(locevent) {
	window.latlng = locevent.latlng;
	window.map.setView(locevent.latlng, 18);
}

map.on('locationfound', set_global_latlng);