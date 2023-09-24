from setuptools import setup
from setuptools import find_packages

setup(
        name= "run_plotter",
        author= "Marc Amberg",
        description= "Simple panel application for measuring run progress.",
        packages= find_packages(where= "run_plotter"),
        install_requires= [
            "panel",
            "folium",
            "gpx",
            "plotly",
            ],
    )
