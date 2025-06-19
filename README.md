# VTK Dash WebGL Visualization

Unified VTK visualization using Dash + Three.js WebGL rendering in a single application.

## Architecture

This project implements a unified VTK visualization system with:

- **Single Dash Application**: All VTK processing and WebGL rendering in one app
- **Direct Integration**: VTK processing integrated with Dash callbacks
- **WebGL Client**: Browser-based Three.js rendering with GPU acceleration
- **No External Dependencies**: Eliminated WebSockets and Trame

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
- Single application architecture
- Direct VTK-Dash integration
- Cross-platform WebGL compatibility
- Real-time parameter adjustments
- Eliminated network complexity

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch Unified Application

```bash
python launch_unified_app.py
```

Or directly:
```bash
python vtk_dash_app.py
```

This starts the unified app on `http://localhost:8050`

### 3. Open Browser

Navigate to `http://localhost:8050` to view the WebGL visualization.

## Usage

### Command Line Arguments

**Unified Application:**
```bash
python vtk_dash_app.py [host] [port] [debug]
```

**Launcher Script:**
```bash
python launch_unified_app.py [host] [port] [debug]
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

1. **User Interaction**: UI controls trigger Dash callbacks
2. **VTK Processing**: Direct geometry processing (vertices, faces, colors)
3. **Data Transfer**: JSON data via Dash Store component
4. **WebGL Rendering**: Browser GPU-accelerated visualization

### Benefits of Unified Architecture

- **Simplicity**: Single application, no network complexity
- **Performance**: Direct function calls, no serialization overhead
- **Reliability**: No WebSocket connection issues
- **Development**: Standard Dash patterns and debugging

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
├── vtk_dash_app.py          # Unified VTK + Dash application
├── launch_unified_app.py    # Simple launcher script
├── requirements.txt         # Python dependencies
├── ARCHITECTURE.md         # Detailed architecture documentation
└── README.md               # This file
```

### Key Technologies

- **Backend**: VTK, Dash
- **Frontend**: Dash, Three.js, WebGL
- **Communication**: Direct Dash callbacks
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