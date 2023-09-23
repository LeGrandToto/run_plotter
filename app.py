import panel as pn
import folium
from gpx.gpx import GPX

def create_folium(file_paths: list[str]):
    tracks = [GPX.from_file(file_path).tracks[0] for file_path in file_paths]

    map = folium.Map(location= [tracks[0].segments[0].points[0].lat, tracks[0].segments[0].points[0].lon], zoom_start = 12)
    for track in tracks:
        first_point = track.segments[0].points[0]
        last_point = track.segments[0].points[-1]

        folium.PolyLine(((point.lat, point.lon) for point in track.segments[0].points), tooltip= "Sunday Run").add_to(map)
        folium.Marker(location= [last_point.lat, last_point.lon],
                      icon= folium.Icon(color= "red", icon= 'ok-sign')
                      ).add_to(map)
        folium.Marker(location= [first_point.lat, first_point.lon],
                      icon= folium.Icon(color= "green", icon= 'ok-sign')
                      ).add_to(map)
    return pn.pane.plot.Folium(map, height= 1000)

def main(track_files):
    template = pn.template.BootstrapTemplate(
            title= "Run Plotter",
            main= create_folium(track_files),
            )

    return template

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("track_files", nargs="+", default=[], help= "A list of GPX file to plot")

    args = parser.parse_args()

    return args.__dict__


main(**parse_args()).servable()

