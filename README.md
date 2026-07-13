# ORMP (Overcomplicated Rotational Music Player)

A music player built with PySide6 and QtQuick3D that focuses on physical interaction. Instead of a standard playback bar, ORMP simulates a spinning vinyl or CD with real inertia and momentum. You can grab it, scratch it, and watch the 3D environment react in real-time.

## Features

- **Physics-Driven Playback**: The audio playback is tied directly to the rotation of the 3D record. It accelerates, decelerates, and responds to mouse drags naturally.
- **3D**: Rendering with anti-aliasing and PBR materials. Includes a free-look camera to explore the scene.
- **Multi-Source**: Plays local files (`.mp3`, `.flac`, `.wav`) and streams directly from Spotify via `librespot`.
- **Custom 3D Models**: Includes a utility (`3d_fixer.py`) to automatically center, scale, and fix the orientation of your own `.glb` files without losing textures.

## Installation

1. Clone or download this repository.
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
*(Requires Python 3.8+ and PySide6)*

## Usage

To start the player, run:
```bash
python main.py
```
The application will automatically load the first song in your `songs/` directory. You can add more local files there or use the UI to add Spotify tracks.

### Controls

- **Mouse Left-Click + Drag**: Grab and scratch the record.
- **Key `R`**: Toggle continuous Y-axis rotation (3D showcase mode).
- **Camera (3D Mode)**:
  - `W A S D`: Move forward, left, backward, right.
  - `Q / E`: Move up and down.
  - `Arrow Keys`: Look around.

### Fixing Custom 3D Models

If you have a `.glb` file that doesn't look right (off-center or wrong rotation), run the included fixer tool:

```bash
python 3d_fixer.py path/to/your_model.glb
```
This will generate a `_fixed.glb` file ready to be loaded into the player.


## Credits

### Libraries

- librespot-python
  https://github.com/kokarare1212/librespot-python

### 3D Assets

- Vinyl Record
  https://sketchfab.com/3d-models/7-vinyl-record-a3b32c49a1044b59a8ee2a0bdb9fd4df

- Playboi Carti Vinyl
  https://sketchfab.com/3d-models/playboi-carti-vinyl-a30db4efabc84ca68483d00fa164a1a1

- Very Simple CD Disc
  https://sketchfab.com/3d-models/very-simple-cd-disc-9749f5ba1221476993376a3cb8fee1a5

- Vinyl Record
  https://sketchfab.com/3d-models/vinyl-record-1bbf5d34cae24d3d9cfa460022aaebc6
