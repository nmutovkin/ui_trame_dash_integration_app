# VTK WebGL Visualization

Client-side VTK visualization using Three.js WebGL rendering with real-time server streaming.

## Architecture

This project implements a distributed VTK visualization system with:

- **VTK Geometry Server**: Extracts geometry data from VTK objects and streams via WebSocket
- **WebGL Client**: Browser-based Three.js rendering with GPU acceleration
- **Real-time Communication**: WebSocket streaming for live data updates

## Features

### 🎨 Client-Side Rendering
- Three.js WebGL with local GPU acceleration
- Real-time 3D visualization in browser
- No server-side image generation

### 🎮 Interactive Controls
- Mouse orbit and zoom navigation
- Material property controls (opacity, wireframe)
- Camera reset and positioning

### 🔧 Technical Benefits
- Minimal server load (geometry data only)
- Scalable to multiple concurrent users
- Cross-platform WebGL compatibility
- Real-time parameter adjustments

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start VTK Server

```bash
python vtk_geometry_server.py localhost 8080 8081
```

This starts:
- VTK server on `http://localhost:8080`
- WebSocket streaming on `ws://localhost:8081`

### 3. Start WebGL Client

```bash
python webgl_vtk_client.py localhost 8080 0.0.0.0 8052
```

This starts the WebGL client on `http://localhost:8052`

### 4. Open Browser

Navigate to `http://localhost:8052` to view the WebGL visualization.

## Usage

### Command Line Arguments

**VTK Server:**
```bash
python vtk_geometry_server.py [host] [port] [websocket_port]
```

**WebGL Client:**
```bash
python webgl_vtk_client.py [vtk_host] [vtk_port] [client_host] [client_port]
```

### Web Interface

The WebGL client provides:
- **3D Viewport**: Interactive Three.js rendering
- **Material Controls**: Opacity and wireframe toggles
- **Camera Controls**: Reset view button
- **Status Panel**: Connection and rendering information

### Mouse Controls

- **Drag**: Orbit camera around object
- **Scroll**: Zoom in/out
- **Reset**: Use reset button to return to default view

## Architecture Details

### Data Flow

1. **VTK Processing**: Server extracts geometry (vertices, faces, colors)
2. **WebSocket Streaming**: Real-time data transmission
3. **WebGL Rendering**: Browser GPU-accelerated visualization
4. **User Interaction**: Local mouse controls and UI updates

### Benefits of Client-Side Rendering

- **Performance**: Local GPU acceleration
- **Scalability**: Server only processes geometry
- **Responsiveness**: Real-time interaction without network delay
- **Bandwidth**: Efficient data streaming vs. image transmission

## System Requirements

### Software
- Python 3.8+
- VTK 9.0+
- Modern web browser with WebGL support

### Hardware
- Graphics card with WebGL 1.0/2.0 support
- Recommended: Dedicated GPU for large datasets

### Browser Compatibility
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Development

### Project Structure

```
├── vtk_geometry_server.py    # VTK data processing and WebSocket streaming
├── webgl_vtk_client.py       # Three.js WebGL client interface
├── requirements.txt          # Python dependencies
├── ARCHITECTURE.md          # Detailed architecture documentation
└── README.md               # This file
```

### Key Technologies

- **Backend**: VTK, Trame, WebSockets
- **Frontend**: Dash, Three.js, WebGL
- **Communication**: WebSocket (geometry streaming)
- **Rendering**: Client-side GPU acceleration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both server and client
5. Submit a pull request

## License

This project is open source. See the LICENSE file for details.

## Troubleshooting

### WebGL Issues
- Ensure graphics drivers are up to date
- Check browser WebGL support at `webglreport.com`
- Try different browsers if WebGL fails

### Connection Issues
- Verify server is running on specified ports
- Check firewall settings for WebSocket connections
- Ensure hostname resolution for multi-machine setup

### Performance Issues
- Use dedicated graphics card if available
- Close other graphics-intensive applications
- Reduce geometry complexity for large datasets 