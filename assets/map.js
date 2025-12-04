// map.js

let map = null;
let markersLayer = null;

Shiny.addCustomMessageHandler("update_map", function(data) {

    // 1. Create map first time
    if (map === null) {
        map = L.map("map");

        // 2. Update center
        map.setView([data.center.lat, data.center.lng], 4);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 18,
        }).addTo(map);

        markersLayer = L.markerClusterGroup();
        map.addLayer(markersLayer);
    }

    // 3. Clear markers
    markersLayer.clearLayers();

    // 4. Add new markers
    data.markers.forEach(function(m) {
        const marker = L.marker([m.lat, m.lng]);

        // ADD POPUP WITH HTML
        if (m.popup) {
            marker.bindPopup(m.popup, { maxWidth: 300 });
        }

        markersLayer.addLayer(marker);
    });
});
