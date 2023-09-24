from gpx.waypoint import Waypoint
import panel as pn
import folium
import plotly.express as px
from gpx.gpx import GPX
from math import sqrt

def create_folium(file_paths: list[str]):
    if not file_paths:
        return "No track found!"

    tracks = [GPX.from_file(file_path).tracks[0] for file_path in file_paths]

    tiles = ["OpenStreetMap", "CartoDB positron", "Stamen Terrain", "Stamen Watercolor", "CartoDB dark_matter"]
    default_tile_index = 2
    
    folium_map = folium.Map(location= [tracks[0].segments[0].points[0].lat, tracks[0].segments[0].points[0].lon], zoom_start = 16, tiles = tiles[default_tile_index])
    for tile_layer in tiles[:default_tile_index] + tiles[default_tile_index + 1:]:
        folium.TileLayer(tile_layer).add_to(folium_map)
    folium.LayerControl().add_to(folium_map)
    for track in tracks:
        first_point = track.segments[0].points[0]
        last_point = track.segments[0].points[-1]

        folium.PolyLine(((point.lat, point.lon) for point in track.segments[0].points), tooltip= "Sunday Run").add_to(folium_map)
        folium.Marker(location= [last_point.lat, last_point.lon],
                      icon= folium.Icon(color= "red", icon= 'ok-sign')
                      ).add_to(folium_map)
        folium.Marker(location= [first_point.lat, first_point.lon],
                      icon= folium.Icon(color= "green", icon= 'ok-sign')
                      ).add_to(folium_map)
    return pn.pane.plot.Folium(folium_map, height= 800)

def create_speed_plots(file_paths):
    def compute_speed(current: Waypoint, next_loc: Waypoint):
        distance = sqrt((current.lat - next_loc.lat) ** 2 + (current.lon - next_loc.lon) ** 2) * 25000/360
        # import pdb; pdb.set_trace()
        time = next_loc.time - current.time
        return distance / (time.total_seconds() / 3600)
    plots = []
    for file_path in file_paths:
        track = GPX.from_file(file_path).tracks[0]

        speeds = [compute_speed(c, n ) for c, n in zip(track.segments[0].points, track.segments[0].points[1:])]
        surface = px.line(x= range(len(speeds)), y= speeds)
        surface.layout.xaxis["title"] = {"text": "Time"}
        surface.layout.yaxis["title"] = {"text": "Speed in km/h"}
        plots.append(pn.pane.Plotly(surface))
    return pn.Column(*plots)

def main(track_files):
    folium_map = create_folium(track_files)
    speed_plots = create_speed_plots(track_files)

    template = pn.template.BootstrapTemplate(
            title= "Run Plotter",
            main= [
                    folium_map,
                    speed_plots,
                ],
            )

    return template

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("track_files", nargs="*", default=[], help= "A list of GPX file to plot")

    args = parser.parse_args()

    return args.__dict__


main(**parse_args()).servable()

