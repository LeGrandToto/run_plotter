from gpx.waypoint import Waypoint
import ipyleaflet
import panel as pn
import param
from param import Event, Parameterized, ListSelector
import plotly.express as px
from gpx.gpx import GPX
from math import sqrt

import logging
import os

logger = logging.getLogger(__name__)

pn.extension('ipywidgets', 'plotly')

class TrackManager(Parameterized):
    tracks = ListSelector(objects= {
            "First Track": [[0.0, 0.0], [0.0,10.0]],
            "Second Track": [[1.0, 1.0], [2.0,2.0], [3.0,1.0]]
        }
    )
    ipyleaflet_map = param.Parameter(None, precedence= -1)
    marker: ipyleaflet.Marker = param.Parameter(None, precedence= -1)  # Global Marker 

    @param.depends("tracks")
    def create_map(self):
        if not self.tracks:
            return self.ipyleaflet_map

        tracks = {track: self.param.tracks.objects.get(track).tracks[0] for track in self.tracks}
        # AwesomeIcon list: https://fontawesome.com/v4/icons/
        from ipyleaflet import Marker, AwesomeIcon 
        ipyleaflet_map = self.ipyleaflet_map.object
        ipyleaflet_map.center= (float(tracks[self.tracks[0]].segments[0].points[0].lat), float(tracks[self.tracks[0]].segments[0].points[0].lon)),

        draw_control: ipyleaflet.DrawControl = ipyleaflet_map.controls[-1]

        def update_track(*args, **kwargs):
            logger.warning(f"{args=}")
            logger.warning(f"{kwargs=}")
            track_index = kwargs.get('geo_json', {}).get('track_index')
            if track_index is not None:
                new_locations = [(lat, lon) for lon, lat in kwargs['geo_json']['geometry']['coordinates']]
                for point, new_location in zip(tracks[track_index].segments[0].points, new_locations):
                    point.lat = new_location[0]
                    point.lon = new_location[1]
                print(self)

        draw_control._draw_callbacks.callbacks.clear()
        draw_control.on_draw(update_track)

        draw_data = []
        ipyleaflet_map.layers = ipyleaflet_map.layers[:1]

        for index, track in tracks.items():
            first_point = track.segments[0].points[0]
            last_point = track.segments[0].points[-1]

            draw_data.append(
                    {
                        'type': 'Feature',
                        'track_index': index, # Custom value to keep track of the track to update.
                        'properties': 
                        {
                            'style':
                            {
                                'stroke': True,
                                'color': '#6bc2e5',
                                'weight': 8,
                                'opacity': .8,
                                'fill': False,
                                'clickable': True,
                            }
                        },
                        'geometry':
                        {
                            'type': 'LineString', 
                            'coordinates':  
                            [[
                                float(point.lon),
                                float(point.lat)
                            ] for point in track.segments[0].points]

                        }
                    }
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
        draw_control.data = draw_data
        # return pn.panel(ipyleaflet_map)
        # panel_map = pn.panel(ipyleaflet_map)

        # return panel_map
        return self.ipyleaflet_map

    @param.depends("tracks")
    def create_speed_plots(self):
        if self.tracks is None:
            return None
        def compute_speed(current: Waypoint, next_loc: Waypoint):
            distance = sqrt((current.lat - next_loc.lat) ** 2 + (current.lon - next_loc.lon) ** 2) * 25000/360
            # import pdb; pdb.set_trace()
            time = next_loc.time - current.time
            return distance / (time.total_seconds() / 3600)
        plots = []
        for index, track_index in enumerate(self.tracks):
            track = self.param.tracks.objects.get(track_index).tracks[0]

            speeds = [compute_speed(c, n ) for c, n in zip(track.segments[0].points, track.segments[0].points[1:])]
            surface = px.line(x= range(len(speeds)), y= speeds)
            surface.layout.xaxis["title"] = {"text": "Time"}
            surface.layout.yaxis["title"] = {"text": "Speed in km/h"}
            plotly_object = pn.pane.Plotly(surface)
            plotly_object.width_policy = "max"
            plotly_object.index = index
            plots.append((os.path.basename(track_index), plotly_object))

        def speed_plot_callback(event: Event):
            from ipyleaflet import Marker, AwesomeIcon
            if event.name == "hover_data":
                if event.old:
                    self.ipyleaflet_map.object.remove_layer(self.marker)
                if event.new:
                    for track in event.new["points"]:
                        # track_index = track["curveNumber"]
                        track_index = event.cls.index
                        segment_index = track["pointIndex"]
                        selected_segment = self.param.tracks.objects[self.tracks[track_index]].tracks[0].segments[0].points[segment_index]
                        # pprint(dir(folium_map.object))
                        self.marker = Marker(
                                location= [float(selected_segment.lat), float(selected_segment.lon)],
                                icon= AwesomeIcon(
                                    name= "dot-circle-o"
                                ),
                                draggable= False,
                            )
                        self.ipyleaflet_map.object.add_layer(self.marker)

        tabs = pn.Tabs(*plots)
        tabs.width_policy = "max"

        for speed_plot in tabs:
            speed_plot.param.watch(speed_plot_callback, ["hover_data"])

        return tabs


def create_map(tracks: list[GPX]):
    # AwesomeIcon list: https://fontawesome.com/v4/icons/
    from ipyleaflet import Map, basemaps, Marker, Polyline, AwesomeIcon, AntPath
    from ipywidgets import Layout
    ipyleaflet_map = Map(
            center= (float(tracks[0].tracks[0].segments[0].points[0].lat), float(tracks[0].tracks[0].segments[0].points[0].lon)),
            # center= (0, 0),
            zoom=16,
            # basemap = basemaps.Stamen.Terrain,
            # basemap = basemaps.OpenTopoMap,
            # basemap = basemaps.Esri.DeLorme,
            basemap = basemaps.OpenStreetMap.HOT,
            # basemap = ,
            layout = Layout(height= "775px")
            )

    draw_control = ipyleaflet.DrawControl()


    draw_control.polyline =  {
        "shapeOptions": {
            "color": "#6bc2e5",
            "weight": 8,
            "opacity": 1.0
        }
    }

    ipyleaflet_map.add_control(draw_control)

    return pn.panel(ipyleaflet_map)

def main(track_files):
    if not track_files:
        return pn.pane.Markdown("No track found!")
    tracks = {file_path:GPX.from_file(file_path) for file_path in track_files}
    folium_map = create_map(list(tracks.values()))

    track_manager = TrackManager()
    track_manager.param.tracks.objects = tracks
    track_manager.ipyleaflet_map = folium_map

    save_button = pn.widgets.Button(name="Save")

    def save_callback(event):
        for file_path, track in tracks.items():
            track.to_file(file_path)

    save_button.on_click(save_callback)

    # template = pn.template.BootstrapTemplate(
    template = pn.template.FastListTemplate(
            title= "Run Plotter",
            main= [pn.Column(*[
                    # "Hello",
                    pn.Row(track_manager, save_button),
                    # folium_map,
                    track_manager.create_map,
                    # speed_plots,
                    track_manager.create_speed_plots,
                    ]),
                   ]
            )
 

    # return pn.Column(*template.main)
    return template

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("track_files", nargs="*", default=[], help= "A list of GPX file to plot")

    args = parser.parse_args()

    return args.__dict__

if __name__ == "__main__":
    from panel.command import main as panel_main
    import sys
    import glob


    sys.argv = ["panel", "serve", __file__, "--args"] + glob.glob("/home/marc/trace_*.gpx")

    exit(panel_main())
    
main(**parse_args()).servable()

