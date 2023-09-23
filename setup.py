from setuptools import setup
from setuptools import find_packages

setup(
        name= "run_plotter",
        author= "Marc Amberg",
        description= "Simple panel application for measuring run progress.",
        packages= find_packages("run_plotter"),
        requires= [
            "panel",
            ],
    )
