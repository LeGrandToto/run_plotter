from gpx.waypoint import Waypoint
import ipyleaflet
import panel as pn
import param
from param import Event, Parameterized, ListSelector
import plotly.express as px
from gpx.gpx import GPX
from math import sqrt

from pprint import pprint

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

    @param.depends("tracks")
    def create_map(self):
        if not self.tracks:
            return self.ipyleaflet_map

        tracks = {track: self.param.tracks.objects.get(track) for track in self.tracks}
        # AwesomeIcon list: https://fontawesome.com/v4/icons/
        from ipyleaflet import Marker, AwesomeIcon 
        ipyleaflet_map = self.ipyleaflet_map.object
        ipyleaflet_map.center= (float(tracks[self.tracks[0]].segments[0].points[0].lat), float(tracks[self.tracks[0]].segments[0].points[0].lon)),

        draw_control = ipyleaflet_map.controls[-1]

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

        # TODO: Only add the callback once
        draw_control.on_draw(update_track)

        draw_data = []

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

            # TODO: Re-use Markers instead of creating new ones all the time.
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
        return self.map


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
            track = self.param.tracks.objects.get(track_index)

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
                        selected_segment = self.param.tracks.objects[self.tracks[track_index]].segments[0].points[segment_index]
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
            center= (float(tracks[0].segments[0].points[0].lat), float(tracks[0].segments[0].points[0].lon)),
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
    # draw_control.polygon = {
    #     "shapeOptions": {
    #         "fillColor": "#6be5c3",
    #         "color": "#6be5c3",
    #         "fillOpacity": 1.0
    #     },
    #     "drawError": {
    #         "color": "#dd253b",
    #         "message": "Oups!"
    #     },
    #     "allowIntersection": False
    # }
    # draw_control.circle = {
    #     "shapeOptions": {
    #         "fillColor": "#efed69",
    #         "color": "#efed69",
    #         "fillOpacity": 1.0
    #     }
    # }
    # draw_control.rectangle = {
    #     "shapeOptions": {
    #         "fillColor": "#fca45d",
    #         "color": "#fca45d",
    #         "fillOpacity": 1.0
    #     }
    # }

    ipyleaflet_map.add_control(draw_control)

    return pn.panel(ipyleaflet_map)
    
    draw_data = []

    for index, track in enumerate(tracks):
        first_point = track.segments[0].points[0]
        last_point = track.segments[0].points[-1]

        # ipyleaflet_map.add_layer(
        #         # Polyline( 
        #         AntPath(
        #             # dash_array=[1, 10],
        #             # delay= 1000,
        #             color='#7590ba',
        #             pulse_color='#3f6fba',
        #             locations = [
        #                 [
        #                     float(point.lat),
        #                     float(point.lon)
        #                 ] for point in track.segments[0].points
        #             ],
        #             # color = "green",
        #             fill= False,
        #             smooth_factor= 5,
        #         )
        #     )
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
    panel_map = pn.panel(ipyleaflet_map)

    logging.getLogger(__name__)
    logger.warning(f"{dir(panel_map)=}")
    logger.warning(f"{dir(panel_map.param)=}")
    logger.warning(f"{dir(panel_map.params)=}")


    import param
    @param.depends("draw_control.data", watch= True)
    def log_data(*args, **kwargs):
        logger.warning(f"{draw_control.data}")

    butt = pn.widgets.Button(name= "Click me")

    def butt_callback(event):
        logger.warning(f"{draw_control.data=}")
        draw_control.data = [{'type': 'Feature', 'properties': {'style': {'stroke': True, 'color': '#6bc2e5', 'weight': 8, 'opacity': 1, 'fill': False, 'clickable': True}}, 'geometry': {'type': 'LineString', 'coordinates': [[-0.088878, 51.509744], [-0.073535, 51.508876], [-0.073213, 51.504749], [-0.087097, 51.504829]]}}]

    butt.on_click(butt_callback)

    # return pn.Row(panel_map, butt)
    return panel_map

def create_seed_plots(file_paths):
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
        plotly_object.width_policy = "max"
        plotly_object.index = index
        plots.append((os.path.basename(file_path), plotly_object))
    tabs = pn.Tabs(*plots)
    tabs.width_policy = "max"
    return tabs

def main(track_files):
    if not track_files:
        return pn.pane.Markdown("No track found!")
    tracks = [GPX.from_file(file_path).tracks[0] for file_path in track_files]
    folium_map = create_map(tracks)

    track_manager = TrackManager()
    track_manager.param.tracks.objects = {file_path: GPX.from_file(file_path).tracks[0] for file_path in track_files}
    track_manager.ipyleaflet_map = folium_map

    template = pn.template.BootstrapTemplate(
            title= "Run Plotter",
            main= [
                    # "Hello",
                    track_manager,
                    # folium_map,
                    track_manager.create_map,
                    # speed_plots,
                    track_manager.create_speed_plots,
                ],
            )
 

    return pn.Column(*template.main)
    # return template

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

