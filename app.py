from gpx.waypoint import Waypoint
import ipyleaflet
import panel as pn
from param import Event
import plotly.express as px
from gpx.gpx import GPX
from math import sqrt

import logging

logger = logging.getLogger(__name__)

pn.extension('ipywidgets', 'plotly')

def create_map(tracks: list[GPX]):
    # AwesomeIcon list: https://fontawesome.com/v4/icons/
    from ipyleaflet import Map, basemaps, Marker, Polyline, AwesomeIcon
    from ipywidgets import Layout
    ipyleaflet_map = Map(
            center= (float(tracks[0].segments[0].points[0].lat), float(tracks[0].segments[0].points[0].lon)),
            zoom=16,
            basemap = basemaps.Stamen.Terrain,
            layout = Layout(height= "800px")
            )
    for track in tracks:
        first_point = track.segments[0].points[0]
        last_point = track.segments[0].points[-1]

        ipyleaflet_map.add_layer(
                Polyline( 
                    locations = [
                        [
                            float(point.lat),
                            float(point.lon)
                        ] for point in track.segments[0].points
                    ],
                    # color = "green",
                    fill= False,
                    smooth_factor= 5,
                )
            )

        ipyleaflet_map.add_layer(
                Marker(
                    location= [float(last_point.lat), float(last_point.lon)],
                    icon= AwesomeIcon(
                        name="check-circle-o",
                        marker_color= "red"
                    ),
                    draggable= False,
                )
            )
        ipyleaflet_map.add_layer(
                Marker(
                    location= [float(first_point.lat), float(first_point.lon)],
                    icon = AwesomeIcon(
                        name="check-circle-o",
                        marker_color= "green"
                    ),
                    draggable= False,
                )
            )
    return pn.panel(ipyleaflet_map)

def create_speed_plots(file_paths):
    def compute_speed(current: Waypoint, next_loc: Waypoint):
        distance = sqrt((current.lat - next_loc.lat) ** 2 + (current.lon - next_loc.lon) ** 2) * 25000/360
        # import pdb; pdb.set_trace()
        time = next_loc.time - current.time
        return distance / (time.total_seconds() / 3600)
    plots = []
    for index, file_path in enumerate(file_paths):
        track = GPX.from_file(file_path).tracks[0]

        speeds = [compute_speed(c, n ) for c, n in zip(track.segments[0].points, track.segments[0].points[1:])]
        surface = px.line(x= range(len(speeds)), y= speeds)
        surface.layout.xaxis["title"] = {"text": "Time"}
        surface.layout.yaxis["title"] = {"text": "Speed in km/h"}
        plotly_object = pn.pane.Plotly(surface)
        plotly_object.index = index
        plots.append(plotly_object)
    return pn.FlexBox(*plots)

marker: ipyleaflet.Marker = None
def main(track_files):
    if not track_files:
        return "No track found!"
    tracks = [GPX.from_file(file_path).tracks[0] for file_path in track_files]
    folium_map = create_map(tracks)
    speed_plots = create_speed_plots(track_files)

    template = pn.template.BootstrapTemplate(
            title= "Run Plotter",
            main= [
                    # "Hello",
                    pn.Column(folium_map,),
                    speed_plots,
                ],
            )

    def speed_plot_callback(event: Event):
        from ipyleaflet import Marker, AwesomeIcon
        global marker
        if event.name == "hover_data":
            if event.old:
                folium_map.object.remove_layer(marker)
            if event.new:
                for track in event.new["points"]:
                    # track_index = track["curveNumber"]
                    track_index = event.cls.index
                    segment_index = track["pointIndex"]
                    selected_segment = tracks[track_index].segments[0].points[segment_index]
                    # pprint(dir(folium_map.object))
                    marker = Marker(
                            location= [float(selected_segment.lat), float(selected_segment.lon)],
                            icon= AwesomeIcon(
                                name= "dot-circle-o"
                            ),
                            draggable= False,
                        )
                    folium_map.object.add_layer(marker)


    for speed_plot in speed_plots:
        speed_plot.param.watch(speed_plot_callback, ["hover_data"])
    return pn.Column(*template.main)
    # return template

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("track_files", nargs="*", default=[], help= "A list of GPX file to plot")

    args = parser.parse_args()

    return args.__dict__


main(**parse_args()).servable()

