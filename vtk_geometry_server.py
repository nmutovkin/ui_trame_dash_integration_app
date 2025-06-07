#!/usr/bin/env python3
"""
VTK Geometry Server
==================
Extracts geometry data from VTK objects and streams to WebGL clients.
Designed for client-side rendering with minimal server load.

Features:
- VTK unstructured grid processing
- Real-time geometry extraction (vertices, faces, colors)
- WebSocket streaming to multiple clients
- Trame-based minimal UI for direct access
- Colormap and opacity controls
"""
import numpy as np
import vtk
import json
import asyncio
import websockets
import threading
from trame.app import get_server
from trame.widgets import html, vtk as vtk_widgets
from trame.ui.html import DivLayout

class VTKGeometryServer:
    def __init__(self, host="0.0.0.0", port=8080, ws_port=8081):
        """
        Initialize VTK Geometry Server
        
        Args:
            host: Server interface host
            port: Trame server port 
            ws_port: WebSocket port for geometry streaming
        """
        self.host = host
        self.port = port
        self.ws_port = ws_port
        
        # Initialize Trame server for VTK processing
        self.server = get_server()
        self.server.client_type = "vue3"
        
        # VTK objects
        self.vtk_data = None
        self.mapper = vtk.vtkDataSetMapper()
        self.actor = vtk.vtkActor()
        
        # WebSocket clients
        self.clients = set()
        
        # State variables
        self.current_opacity = 1.0
        self.current_colormap = "elevation"
        self.wireframe_mode = False
        
        self.setup_vtk_pipeline()
        self.setup_ui()
        
    def setup_vtk_pipeline(self):
        """Setup VTK visualization pipeline"""
        # Create sample unstructured grid (sphere)
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetThetaResolution(30)
        sphere_source.SetPhiResolution(30)
        sphere_source.Update()
        
        # Convert to unstructured grid
        appendFilter = vtk.vtkAppendFilter()
        appendFilter.SetInputData(sphere_source.GetOutput())
        appendFilter.Update()
        self.vtk_data = appendFilter.GetOutput()
        
        # Setup mapper and actor
        self.mapper.SetInputData(self.vtk_data)
        self.actor.SetMapper(self.mapper)
        
        # Apply elevation filter for coloring
        self.update_colormap()
        
    def setup_ui(self):
        """Setup minimal Trame UI"""
        state, ctrl = self.server.state, self.server.controller
        
        with DivLayout(self.server) as layout:
            html.Div("VTK Geometry Server - WebGL Ready", 
                    style="padding: 20px; text-align: center; font-size: 24px; font-weight: bold;")
            
            html.Div([
                html.P(f"🎯 Geometry Server: {self.host}:{self.port}"),
                html.P(f"🔌 WebSocket Streaming: ws://{self.host}:{self.ws_port}"),
                html.P("📊 Status: Ready for WebGL clients")
            ], style="text-align: center; margin: 20px;")
            
            # VTK Render Window (minimal size)
            with html.Div(style="display: flex; justify-content: center;"):
                vtk_view = vtk_widgets.VtkLocalView(
                    self.create_render_window(),
                    style="width: 400px; height: 300px; border: 2px solid #007bff;"
                )
        
        # Set up control handlers
        self.setup_control_handlers()
        
    def create_render_window(self):
        """Create VTK render window"""
        renderer = vtk.vtkRenderer()
        renderer.AddActor(self.actor)
        renderer.SetBackground(0.1, 0.1, 0.2)  # Dark blue background
        
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetSize(400, 300)
        
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)
        interactor.Initialize()
        
        return render_window
        
    def setup_control_handlers(self):
        """Setup WebSocket control message handlers"""
        async def handle_client_controls(websocket, path):
            """Handle WebSocket messages from clients"""
            try:
                self.clients.add(websocket)
                print(f"🔗 New WebSocket client connected from {websocket.remote_address}")
                
                # Send initial geometry data
                await self.send_geometry_data(websocket)
                
                async for message in websocket:
                    data = json.loads(message)
                    await self.handle_control_message(data)
                    
            except websockets.exceptions.ConnectionClosed:
                print("🔌 WebSocket client disconnected")
            finally:
                self.clients.discard(websocket)
        
        # Start WebSocket server in background thread
        def start_websocket_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_server = websockets.serve(handle_client_controls, self.host, self.ws_port)
            print(f"🔌 WebSocket server starting on ws://{self.host}:{self.ws_port}")
            loop.run_until_complete(start_server)
            loop.run_forever()
        
        ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
        ws_thread.start()
        print("✅ WebSocket server thread started")
    
    async def handle_control_message(self, data):
        """Handle control messages from WebGL clients"""
        if data.get('type') == 'control':
            control_type = data.get('control_type')
            value = data.get('value')
            
            if control_type == 'opacity':
                self.current_opacity = float(value)
                self.actor.GetProperty().SetOpacity(self.current_opacity)
                print(f"🎨 Opacity changed to {self.current_opacity}")
                
            elif control_type == 'wireframe':
                self.wireframe_mode = bool(value)
                if self.wireframe_mode:
                    self.actor.GetProperty().SetRepresentationToWireframe()
                    print("🎨 Wireframe mode: ON")
                else:
                    self.actor.GetProperty().SetRepresentationToSurface()
                    print("🎨 Wireframe mode: OFF")
                    
            elif control_type == 'colormap':
                self.current_colormap = str(value)
                self.update_colormap()
                print(f"🌈 Colormap changed to {self.current_colormap}")
            
            # Broadcast updated geometry to all clients
            await self.broadcast_geometry_data()
    
    def update_colormap(self):
        """Update VTK colormap"""
        # Apply elevation filter for coloring
        elevation = vtk.vtkElevationFilter()
        elevation.SetInputData(self.vtk_data)
        elevation.SetLowPoint(0, -1, 0)
        elevation.SetHighPoint(0, 1, 0)
        elevation.Update()
        
        self.mapper.SetInputData(elevation.GetOutput())
        self.mapper.SetScalarModeToUsePointData()
        self.mapper.SetColorModeToMapScalars()
        
        # Set color map
        lut = vtk.vtkLookupTable()
        lut.SetHueRange(0.667, 0.0)  # Blue to Red
        lut.Build()
        self.mapper.SetLookupTable(lut)
    
    def extract_geometry_data(self):
        """Extract geometry data for WebGL rendering"""
        # Get the current VTK data
        elevation = vtk.vtkElevationFilter()
        elevation.SetInputData(self.vtk_data)
        elevation.SetLowPoint(0, -1, 0)
        elevation.SetHighPoint(0, 1, 0)
        elevation.Update()
        
        polydata = elevation.GetOutput()
        
        # Extract vertices
        points = polydata.GetPoints()
        num_points = points.GetNumberOfPoints()
        vertices = []
        
        for i in range(num_points):
            point = points.GetPoint(i)
            vertices.extend([point[0], point[1], point[2]])
        
        # Extract faces
        faces = []
        cells = polydata.GetPolys()
        cells.InitTraversal()
        
        id_list = vtk.vtkIdList()
        while cells.GetNextCell(id_list):
            if id_list.GetNumberOfIds() >= 3:
                # Convert to triangles
                for i in range(1, id_list.GetNumberOfIds() - 1):
                    faces.extend([
                        id_list.GetId(0),
                        id_list.GetId(i),
                        id_list.GetId(i + 1)
                    ])
        
        # Extract colors from scalar data
        colors = []
        scalars = polydata.GetPointData().GetScalars()
        if scalars:
            lut = self.mapper.GetLookupTable()
            for i in range(num_points):
                scalar_val = scalars.GetValue(i)
                color = [0, 0, 0]
                lut.GetColor(scalar_val, color)
                colors.extend(color)
        else:
            # Default orange color
            colors = [1.0, 0.5, 0.0] * num_points
            
        return {
            "vertices": vertices,
            "faces": faces,
            "colors": colors,
            "vertex_count": num_points,
            "face_count": len(faces) // 3,
            "opacity": self.current_opacity,
            "wireframe": self.wireframe_mode
        }
    
    async def send_geometry_data(self, websocket):
        """Send geometry data to a specific client"""
        try:
            geometry_data = self.extract_geometry_data()
            message = {
                "type": "geometry_data",
                "data": geometry_data
            }
            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"❌ Failed to send geometry data: {e}")
    
    async def broadcast_geometry_data(self):
        """Broadcast geometry data to all connected clients"""
        if not self.clients:
            return
            
        geometry_data = self.extract_geometry_data()
        message = {
            "type": "geometry_data", 
            "data": geometry_data
        }
        
        # Send to all clients
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected
    
    def run(self):
        """Start the VTK geometry server"""
        print("🚀 Starting VTK Visualization Server (embed-ready)")
        print(f"📍 Visualization URL: http://{self.host}:{self.port}")
        print(f"🔌 WebSocket Controls: ws://{self.host}:{self.ws_port}")
        print("🎯 Minimal UI - designed for iframe embedding")
        print("🎮 External controls via WebSocket")
        
        self.server.start(
            host=self.host,
            port=self.port,
            dev_tools=False,
            open_browser=False
        )

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    ws_port = int(sys.argv[3]) if len(sys.argv) > 3 else 8081
    
    server = VTKGeometryServer(host=host, port=port, ws_port=ws_port)
    server.run() 