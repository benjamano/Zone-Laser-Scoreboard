#

# [Click to View Technical Info & Packet Sniffing Details](TECHNICAL_INFO.md)


# Zone Laser Scoreboard

Zone Laser Scoreboard is the ultimate control and automation system designed for children's playcenters, family entertainment venues, and laser tag arenas. Whether you run a bustling playcenter, a birthday party venue, or a high-energy laser tag attraction, this system brings your space to life with synchronized lighting, music, and game event automation—all from a user-friendly web interface.

## Why Choose Zone Laser Scoreboard for Your Playcenter?

- **Transform Your Venue:** Instantly create immersive, themed environments for kids and families with dynamic lighting scenes, music playlists, and interactive triggers.
- **Perfect for Laser Tag:** Integrate game events (like scoring, game start/end, or special rounds) with lighting and sound effects to make every match unforgettable.
- **Birthday Parties & Events:** Easily switch between party modes, custom scenes, and music to keep the energy high and the experience unique for every group.
- **Operator-Friendly:** Designed for busy staff—no technical expertise required. Drag-and-drop controls, instant feedback, and automation make it simple to run your center.
- **Flexible & Customizable:** Works with a wide range of DMX lighting fixtures, music libraries, and game systems. Adapt it to your space and your needs.


## Key Features

- **DMX Lighting Control:**
	- Drag-and-drop fixture patching and easy channel management.
	- Real-time sliders for instant lighting changes.
	- Visual feedback and fixture highlighting for quick troubleshooting.

- **Scene Management:**
	- Build custom lighting and music scenes for games, parties, or special events.
	- Flash and loop modes for energetic effects.
	- Trigger scenes with keyboard shortcuts or game events.

- **Music Integration:**
	- Sync music playlists with lighting scenes for maximum impact.
	- Supports large MP3 libraries—perfect for parties and themed events.

- **Game Event Automation:**
	- Connect lighting and sound effects to laser tag game events (score, start, end, power-ups, etc.).
	- Flexible API for integrating with your game system.

- **Visual Rendering System (VRS):**
	- Built-in, fully integrated replacement for OBS—no external software required.
	- Control screens, displays, and media output for games, parties, and downtime.
	- Switch visuals automatically or manually based on game events, lighting scenes, or operator actions.

- **Web-Based UI:**
	- Modern, responsive interface for any device.
	- Drag-and-drop controls, virtual console, and instant feedback.
	- Context menus, tooltips, and editable fields for fast setup.

- **Extensible Architecture:**
	- Modular Python backend with SQL database for reliable storage.
	- RESTful API endpoints for DMX, scenes, fixtures, and events.
	- Socket.IO for real-time updates and control.

## Key Features


- **DMX Lighting Control:**
	- Drag-and-drop fixture patching and easy channel management.
	- Real-time sliders for instant lighting changes.
	- Visual feedback and fixture highlighting for quick troubleshooting.

- **Scene Management:**
	- Build custom lighting and music scenes for games, parties, or special events.
	- Flash and loop modes for energetic effects.
	- Trigger scenes with keyboard shortcuts or game events.

- **Music Integration:**
	- Sync music playlists with lighting scenes for maximum impact.
	- Supports large MP3 libraries—perfect for parties and themed events.

- **Game Event Automation:**
	- Connect lighting and sound effects to laser tag game events (score, start, end, power-ups, etc.).
	- Flexible API for integrating with your game system.

- **Web-Based UI:**
	- Modern, responsive interface for any device.
	- Drag-and-drop controls, virtual console, and instant feedback.
	- Context menus, tooltips, and editable fields for fast setup.

- **Extensible Architecture:**
	- Modular Python backend with SQL database for reliable storage.
	- RESTful API endpoints for DMX, scenes, fixtures, and events.
	- Socket.IO for real-time updates and control.

## Getting Started

1. **Clone the Repository:**
	 ```powershell
	 git clone https://github.com/benjamano/Zone-Laser-Scoreboard.git
	 ```
2. **Install Dependencies:**
	 - Python 3.13+
	 - Required packages (see `src/Utilities/checkDependencies.py`)
3. **Run the Application:**
	 ```powershell
	 cd Zone-Laser-Scoreboard
	 python src/ScoreBoard.py
	 ```
4. **Access the Web Interface:**
	 - Open your browser and navigate to `http://localhost:8080`

## Folder Structure

- `src/ScoreBoard.py` — Main application entry point
- `src/Web/Views/scene.html` — Web UI for scene and fixture control
- `src/Data/` — Models, database, and migrations
- `src/Utilities/` — Helper scripts and utilities
- `src/Web/API/` — API endpoints
- `src/Web/Archive/` — Legacy and backup files
- `src/Web/wwwroot/` — Static assets (images, CSS, JS)
- `src/Web/music/` — Music library


## Screenshots

> **Add your own screenshots here to showcase the UI and features!**

- ![Patch Panel](screenshots/patch_panel.png)
- ![Scene Management](screenshots/scene_management.png)
- ![Music Integration](screenshots/music_integration.png)
- ![Game Event Triggers](screenshots/game_event_triggers.png)
- ![VRS Display Control](screenshots/vrs_display_control.png)
- ![Fixture Drag-and-Drop](screenshots/fixture_drag_drop.png)
- ![DMX Channel Sliders](screenshots/dmx_channel_sliders.png)
- ![Scene Event Timeline](screenshots/scene_event_timeline.png)
- ![Game Event Trigger Setup](screenshots/game_event_trigger_setup.png)
- ![Music Library Integration](screenshots/music_library_integration.png)
- ![Patched Fixtures List](screenshots/patched_fixtures_list.png)
- ![Context Menu for Channels](screenshots/context_menu_channels.png)


## Why Zone Laser Scoreboard?

- **All-in-One Solution for Playcenters:** Lighting, music, and game automation in one easy-to-use platform.
- **Kid-Friendly & Staff-Friendly:** Intuitive controls, instant feedback, and automation designed for busy venues.
- **Customizable for Any Space:** Works with your fixtures, music, and game logic—no matter your setup.
- **Open Source & Community-Driven:** Ready for your ideas, improvements, and contributions!

## Contributing

We welcome contributions! Please open issues, submit pull requests, or suggest features to help make Zone Laser Scoreboard even better.

## License

This project is licensed under the MIT License.

---


**Zone Laser Scoreboard** — The ultimate control system for children's playcenters, laser tag, and family fun venues.
