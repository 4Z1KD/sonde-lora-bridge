import json
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QPushButton

from SondeLoraClient import SondeLoraClient
from ConfigLoader import ConfigLoader


LEAFLET_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Sonde Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    html, body, #map {
      height: 100%;
      margin: 0;
    }
  </style>
</head>
<body>
<div id="map"></div>

<script>
  const map = L.map('map').setView([31.8, 34.7], 7);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  const callsignColors = {};
  const tracks = {};
  const lastBalloon = {};
  const markerLayer = L.layerGroup().addTo(map);

  function colorFromCallsign(callsign) {
    let hash = 0;
    for (let i = 0; i < callsign.length; i++) {
      hash = callsign.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash) % 360;
    return `hsl(${hue}, 80%, 50%)`;
  }

  function balloonIcon(color) {
    const svg = `
      <svg
      xmlns="http://www.w3.org/2000/svg"
      width="32"
      height="32"
      viewBox="0 0 24 24"
      fill="${color}"
      stroke="#000000"
      stroke-width="1.25"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M14 8a2 2 0 0 0 -2 -2" />
      <path d="M6 8a6 6 0 1 1 12 0c0 4.97 -2.686 9 -6 9s-6 -4.03 -6 -9" />
      <path d="M12 17v1a2 2 0 0 1 -2 2h-3a2 2 0 0 0 -2 2" />
    </svg>
    `;
    return L.divIcon({
      html: svg,
      className: "",
      iconSize: [24, 36],
      iconAnchor: [12, 36]
    });
  }

  function addPacket(callsign, lat, lon, label) {
    if (!callsign) callsign = "UNKNOWN";

    if (!(callsign in callsignColors)) {
      callsignColors[callsign] = colorFromCallsign(callsign);
    }

    const color = callsignColors[callsign];

    // Convert previous balloon to a circle
    if (callsign in lastBalloon) {
      const old = lastBalloon[callsign];
      L.circleMarker(old.getLatLng(), {
        radius: 2,
        color: color,
        weight: 1,
        fillColor: color,
        fillOpacity: 0.6
      }).addTo(markerLayer);
      markerLayer.removeLayer(old);
    }

    // New balloon marker
    const balloon = L.marker([lat, lon], {
      icon: balloonIcon(color)
    })
    .bindPopup(label)
    .addTo(markerLayer);

    lastBalloon[callsign] = balloon;

    // Track line
    if (!(callsign in tracks)) {
      tracks[callsign] = L.polyline([], {
        color: color,
        weight: 2,
        opacity: 0.8
      }).addTo(map);
    }

    tracks[callsign].addLatLng([lat, lon]);

    map.panTo([lat, lon]);
  }

  function clearTracks() {
    markerLayer.clearLayers();

    for (const cs in tracks) {
      map.removeLayer(tracks[cs]);
    }

    for (const cs in tracks) delete tracks[cs];
    for (const cs in callsignColors) delete callsignColors[cs];
    for (const cs in lastBalloon) delete lastBalloon[cs];
  }

  window.addPacket = addPacket;
  window.clearTracks = clearTracks;
</script>
</body>
</html>
"""




# ===============================
# Worker thread (Meshtastic client)
# ===============================

class SondeWorker(QThread):
    sonde_received = pyqtSignal(dict)
    status_changed = pyqtSignal(str)

    def __init__(self, port=None, channel=None, source_device_id=None):
        super().__init__()

        self.client = SondeLoraClient(
            port=port,
            channel=channel,
            source_device_id=source_device_id,
            on_sonde_packet=self.on_sonde_packet
        )

    def on_sonde_packet(self, data: dict):
        self.sonde_received.emit(data)

    def run(self):
        if self.client.connect():
            self.status_changed.emit("Connected – listening for packets")
            self.client.listen()
        else:
            self.status_changed.emit("Failed to connect to Meshtastic device")


# ===============================
# Main GUI window
# ===============================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SondeLoraClient – Live View")
        self.resize(1440, 750)

        self.fields = [
            ("model", "Model"),
            ("callsign", "Callsign"),
            ("frame", "Frame"),
            ("time", "Time (UTC)"),
            ("latitude", "Latitude"),
            ("longitude", "Longitude"),
            ("altitude", "Altitude (m)"),
            ("freq", "Frequency"),
            ("snr", "SNR"),
            ("temp", "Temp (°C)"),
            ("humidity", "Humidity (%)"),
            ("pressure", "Pressure (hPa)"),
            ("sats", "Sats"),
            ("batt", "Battery (V)"),
        ]

        

        self.status_label = QLabel("Disconnected")

        self.table = QTableWidget(0, len(self.fields))
        self.table.setHorizontalHeaderLabels([label for _, label in self.fields])
        self.table.setSortingEnabled(True)

        # 🌍 Map
        self.map_view = QWebEngineView()
        self.map_view.setHtml(LEAFLET_HTML)

        self.clear_button = QPushButton("Clear tracks")
        self.clear_button.clicked.connect(self.clear_tracks)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.table, stretch=2)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.map_view, stretch=3)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


    # ===============================
    # GUI update logic
    # ===============================


    def add_packet_row(self, data: dict):
        sorting = self.table.isSortingEnabled()
        if sorting:
            self.table.setSortingEnabled(False)

        row = self.table.rowCount()
        self.table.insertRow(row)

        for col, (key, _) in enumerate(self.fields):
          value = str(data.get(key, ""))
          item = QTableWidgetItem(value)
          item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
          self.table.setItem(row, col, item)

        if sorting:
            self.table.setSortingEnabled(True)

        self.table.scrollToBottom()

        # 🌍 Send to map
        lat = data.get("latitude")
        lon = data.get("longitude")
        callsign = data.get("callsign", "UNKNOWN")

        if lat is not None and lon is not None:
            label = (
                f"<b>{callsign}</b><br>"
                f"Alt: {data.get('altitude', '')} m<br>"
                f"Time: {data.get('time', '')}"
            )

            js = (
                f"addPacket("
                f"{json.dumps(callsign)}, "
                f"{lat}, "
                f"{lon}, "
                f"{json.dumps(label)}"
                f");"
            )
            self.map_view.page().runJavaScript(js)
    
    def clear_tracks(self):
        # Clear map (markers + tracks)
        self.map_view.page().runJavaScript("clearTracks();")

        # Clear table
        self.table.setRowCount(0)

    def set_status(self, text: str):
        self.status_label.setText(text)

    # ===============================
    # Start background worker
    # ===============================

    def start_client(self, port=None, channel=None, source_device_id=None):
        self.worker = SondeWorker(
            port=port,
            channel=channel,
            source_device_id=source_device_id
        )
        self.worker.sonde_received.connect(self.add_packet_row)
        self.worker.status_changed.connect(self.set_status)
        self.worker.start()


# ===============================
# Application entry point
# ===============================

if __name__ == "__main__":
    config = ConfigLoader.load_config()

    meshtastic_port = config.get("client", {}).get("meshtastic_port", None)
    channel = config.get("client", {}).get("channel", None)
    source_device_id = config.get("client", {}).get("source_device_id", None)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    window.start_client(
        port=meshtastic_port,
        channel=channel,
        source_device_id=source_device_id
    )

    sys.exit(app.exec())
