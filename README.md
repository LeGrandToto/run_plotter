A simple interactive app to look at tracked runs. It aims to be very similar to [GPX Studio]https://gpx.studio/ but also add tools to extract trends accross runs.

Setup
-----

Requirements:
- python >= 3.6
- pip

Install the code simply with `pip`

```bash
pip install .
```

Start the application
---------------------

The application requires to be provided with a list of [GPS Exchange formated](https://en.wikipedia.org/wiki/GPS_Exchange_Format) files. You might get your GPX files by asking for your data to your run tracking provider.

```bash
panel serve --autoreload app.py --args ~/Documents/01-runkeeper-data-export/*.gpx
```

Roadmap
-------

- [ ] Import and display basic GPX:
    - [x] V0: Basic loading and display done
    - [ ] V1: Provide better and faster UI
    - [ ] V2: Load tracks in a background thread or process
- [ ] Allow edits of tracks:
    - [x] V0: Use existing library to edit track location
    - [ ] V1: Add UI to edit time for each point
    - [ ] V2: Allow for multiple points to be edited together or in batch
    - [ ] V3: Allow for tracks to be aligned with a circuit (correct GPS location to match a user defined path)
- [ ] Provide track summary:
    - [ ] V0: Provide simple metrics per tracks:
        - [ ] Total distance
        - [ ] Total time
        - [ ] Average speed
        - [ ] Calories
    - [ ] V1: Compute trends within a track:
        - [ ] Splits for each km
        - [ ] Charts:
            - [x] speed
            - [ ] pace
            - [ ] elevation
- [ ] User management:
    - [ ] V0: Add user creation:
        - Name/alias, height, weight (Required for calorie calculation)
        - Assign tracks to users (users can run together and share tracks)


Limitations
-----------

Unless this project becomes VERY popular, I am not planning to look at localisation. Supporting multiple languages or converting measurements to the imperial system is not planned (yet?). If you want to see those features implemented, please use the issue tracker.
