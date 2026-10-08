# Liniennetz Gießen

Live-Karte aller Buslinien durch Gießen (35390): Linienwege, Fahrzeiten, Takt und Echtzeit-Positionen mit Verspätung. Läuft im Browser und als Homescreen-App auf dem iPhone.

- Linienwege: © OpenStreetMap-Mitwirkende (ODbL)
- Fahrzeiten: Sollfahrplan DELFI via gtfs.de (CC BY 4.0), Stand 03.10.2026
- Live-Positionen: Transitous / MOTIS (api.transitous.org), Echtzeitdaten DELFI/RMV

`tools/` enthält die Skripte, mit denen die Daten aufbereitet wurden (`proc2.py` für OSM, `gtfs1.py`/`gtfs2.py` für den Fahrplan, `build.py` baut `index.html` aus `tpl4.html`).
