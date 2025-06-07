#!/usr/bin/env python3
"""
WebGL VTK Client
================
Client-side VTK visualization using Three.js WebGL rendering.
Receives geometry data from VTK server and renders locally in browser.

Features:
- WebGL-based 3D rendering with Three.js
- Mouse controls (orbit, zoom)
- Real-time material controls (opacity, wireframe)
- WebSocket communication with VTK server
- Local GPU acceleration
"""
import dash
from dash import dcc, html, Input, Output, clientside_callback
import dash_bootstrap_components as dbc

class WebGLVTKClient:
    def __init__(self, vtk_server_host="localhost", vtk_server_port=8080, 
                 client_host="0.0.0.0", client_port=8052):
        """
        Initialize WebGL VTK Client
        
        Args:
            vtk_server_host: VTK server hostname
            vtk_server_port: VTK server port (WebSocket will be port+1)
            client_host: Client interface host
            client_port: Client interface port
        """
        self.vtk_server_host = vtk_server_host
        self.vtk_server_port = vtk_server_port
        self.vtk_server_url = f"http://{vtk_server_host}:{vtk_server_port}"
        
        self.client_host = client_host
        self.client_port = client_port
        
        self.app = dash.Dash(
            __name__, 
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            external_scripts=[
                "https://unpkg.com/three@0.155.0/build/three.min.js"
            ]
        )
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup the WebGL interface layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("🚀 WebGL VTK Visualization", className="text-center mb-4"),
                    
                    dbc.Alert([
                        html.H5("🎮 Client-Side 3D Rendering", className="alert-heading"),
                        html.P([
                            "VTK Server: ", html.Code(self.vtk_server_url), html.Br(),
                            "Rendering: ✅ Three.js WebGL with GPU acceleration", html.Br(),
                            "Status: ", html.Span(id="system-status", children="🔄 Initializing...")
                        ])
                    ], color="info", className="mb-4"),
                    
                    dbc.Row([
                        # WebGL Viewport
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("🎨 Three.js WebGL Viewport"),
                                dbc.CardBody([
                                    html.Canvas(
                                        id="webgl-canvas",
                                        width=800,
                                        height=600,
                                        style={
                                            "width": "100%",
                                            "height": "600px",
                                            "border": "2px solid #007bff",
                                            "border-radius": "8px",
                                            "background": "#1a1a2e",
                                            "cursor": "grab"
                                        }
                                    ),
                                    html.P([
                                        "🎮 Mouse: Drag to orbit, scroll to zoom", html.Br(),
                                        "🎯 GPU: Local WebGL rendering", html.Br(),
                                        "📡 Data: Real-time from VTK server"
                                    ], className="mt-3 text-muted small")
                                ])
                            ])
                        ], md=8),
                        
                        # Control Panel
                        dbc.Col([
                            # Material Controls
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("🎨 Material Properties"),
                                    
                                    html.Label("Opacity:"),
                                    dcc.Slider(
                                        id='opacity-control',
                                        min=0, max=1, step=0.05, value=1.0,
                                        marks={0: '0%', 0.5: '50%', 1: '100%'},
                                        tooltip={"placement": "bottom", "always_visible": True}
                                    ),
                                    
                                    html.Div(className="mt-3"),
                                    dbc.Switch(
                                        id="wireframe-control",
                                        label="Wireframe Mode",
                                        value=False
                                    ),
                                    html.Small("Toggle between solid surface and wireframe mesh", 
                                             className="text-muted")
                                ])
                            ], className="mb-3"),
                            
                            # Camera Controls
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("📷 Camera Controls"),
                                    dbc.Button(
                                        "🔄 Reset View",
                                        id="reset-btn",
                                        color="primary",
                                        size="sm",
                                        className="w-100"
                                    ),
                                    html.Small("Reset camera to default position", 
                                             className="text-muted")
                                ])
                            ], className="mb-3"),
                            
                            # Status Information
                            dbc.Card([
                                dbc.CardBody([
                                    html.H6("📊 Status"),
                                    html.Div(id="status-info", className="small"),
                                    html.Small(id="last-update", className="text-muted")
                                ])
                            ])
                        ], md=4)
                    ])
                ], width=12)
            ])
        ], fluid=True)
    
    def setup_callbacks(self):
        """Setup WebGL rendering and control callbacks"""
        
        # Main WebGL rendering callback
        clientside_callback(
            f"""
            function(opacity, wireframe, reset_clicks) {{
                const canvas = document.getElementById('webgl-canvas');
                const statusDiv = document.getElementById('system-status');
                const infoDiv = document.getElementById('status-info');
                
                if (!canvas) return ['Canvas not found', 'Error'];
                
                // Initialize Three.js scene
                if (!window.sceneInitialized) {{
                    initializeWebGLScene(canvas, statusDiv, infoDiv);
                    window.sceneInitialized = true;
                }}
                
                // Handle control updates
                handleControlUpdates(opacity, wireframe, reset_clicks);
                
                // Initialize WebGL scene
                function initializeWebGLScene(canvas, statusDiv, infoDiv) {{
                    try {{
                        // Check WebGL support
                        if (typeof THREE === 'undefined') {{
                            if (statusDiv) statusDiv.innerHTML = '❌ Three.js failed to load';
                            return;
                        }}
                        
                        // Scene setup
                        window.scene = new THREE.Scene();
                        window.camera = new THREE.PerspectiveCamera(75, canvas.width / canvas.height, 0.1, 1000);
                        window.renderer = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true }});
                        
                        window.renderer.setSize(canvas.width, canvas.height);
                        window.renderer.setClearColor(0x1a1a2e);
                        
                        // Lighting
                        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                        directionalLight.position.set(5, 5, 5);
                        window.scene.add(directionalLight);
                        
                        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
                        window.scene.add(ambientLight);
                        
                        // Camera position
                        window.camera.position.set(0, 0, 8);
                        window.camera.lookAt(0, 0, 0);
                        
                        // Mouse controls
                        setupMouseControls(canvas, window.camera);
                        
                        // Animation loop
                        function animate() {{
                            requestAnimationFrame(animate);
                            if (window.vtkMesh) {{
                                window.vtkMesh.rotation.y += 0.005;
                            }}
                            window.renderer.render(window.scene, window.camera);
                        }}
                        animate();
                        
                        if (statusDiv) statusDiv.innerHTML = '✅ WebGL initialized';
                        
                        // Connect to VTK server
                        connectToVTKServer();
                        
                    }} catch (error) {{
                        console.error('WebGL initialization failed:', error);
                        if (statusDiv) statusDiv.innerHTML = '❌ WebGL initialization failed';
                    }}
                }}
                
                // Handle UI control updates
                function handleControlUpdates(opacity, wireframe, reset_clicks) {{
                    if (window.vtkMesh) {{
                        window.vtkMesh.material.opacity = opacity;
                        window.vtkMesh.material.transparent = opacity < 1.0;
                        window.vtkMesh.material.wireframe = wireframe;
                    }}
                    
                    if (reset_clicks && window.camera) {{
                        window.camera.position.set(0, 0, 8);
                        window.camera.lookAt(0, 0, 0);
                    }}
                }}
                
                // Setup mouse interaction
                function setupMouseControls(canvas, camera) {{
                    let isMouseDown = false;
                    let mouseX = 0, mouseY = 0;
                    
                    canvas.addEventListener('mousedown', (event) => {{
                        isMouseDown = true;
                        mouseX = event.clientX;
                        mouseY = event.clientY;
                    }});
                    
                    canvas.addEventListener('mouseup', () => {{
                        isMouseDown = false;
                    }});
                    
                    canvas.addEventListener('mousemove', (event) => {{
                        if (!isMouseDown) return;
                        
                        const deltaX = event.clientX - mouseX;
                        const deltaY = event.clientY - mouseY;
                        
                        const spherical = new THREE.Spherical();
                        spherical.setFromVector3(camera.position);
                        spherical.theta -= deltaX * 0.01;
                        spherical.phi += deltaY * 0.01;
                        spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
                        
                        camera.position.setFromSpherical(spherical);
                        camera.lookAt(0, 0, 0);
                        
                        mouseX = event.clientX;
                        mouseY = event.clientY;
                    }});
                    
                    canvas.addEventListener('wheel', (event) => {{
                        event.preventDefault();
                        const scale = event.deltaY > 0 ? 1.1 : 0.9;
                        camera.position.multiplyScalar(scale);
                    }});
                }}
                
                // Connect to VTK server via WebSocket
                function connectToVTKServer() {{
                    const wsUrl = 'ws://{self.vtk_server_host}:{self.vtk_server_port + 1}';
                    
                    try {{
                        window.vtkWebSocket = new WebSocket(wsUrl);
                        
                        window.vtkWebSocket.onopen = function() {{
                            console.log('Connected to VTK server');
                            if (infoDiv) infoDiv.innerHTML = '🟢 VTK server connected';
                        }};
                        
                        window.vtkWebSocket.onmessage = function(event) {{
                            const data = JSON.parse(event.data);
                            if (data.type === 'geometry_data') {{
                                renderVTKGeometry(data.data);
                            }}
                        }};
                        
                        window.vtkWebSocket.onerror = function() {{
                            if (infoDiv) infoDiv.innerHTML = '❌ VTK connection failed';
                        }};
                        
                        window.vtkWebSocket.onclose = function() {{
                            if (infoDiv) infoDiv.innerHTML = '🔌 VTK disconnected';
                        }};
                        
                    }} catch (error) {{
                        console.error('WebSocket connection failed:', error);
                    }}
                }}
                
                // Render VTK geometry data
                function renderVTKGeometry(geometryData) {{
                    if (!window.scene || !geometryData.vertices) return;
                    
                    // Remove existing mesh
                    if (window.vtkMesh) {{
                        window.scene.remove(window.vtkMesh);
                    }}
                    
                    try {{
                        // Create BufferGeometry
                        const geometry = new THREE.BufferGeometry();
                        
                        const vertices = new Float32Array(geometryData.vertices);
                        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
                        
                        if (geometryData.colors) {{
                            const colors = new Float32Array(geometryData.colors);
                            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
                        }}
                        
                        if (geometryData.faces) {{
                            const indices = new Uint16Array(geometryData.faces);
                            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
                        }}
                        
                        geometry.computeVertexNormals();
                        
                        // Create material
                        const material = new THREE.MeshLambertMaterial({{
                            vertexColors: true,
                            side: THREE.DoubleSide,
                            opacity: opacity || 1.0,
                            transparent: (opacity || 1.0) < 1.0
                        }});
                        
                        // Create and add mesh
                        window.vtkMesh = new THREE.Mesh(geometry, material);
                        window.scene.add(window.vtkMesh);
                        
                        if (infoDiv) {{
                            infoDiv.innerHTML = `🎨 VTK Mesh: ${{geometryData.vertex_count || 'N/A'}} vertices`;
                        }}
                        
                    }} catch (error) {{
                        console.error('VTK rendering failed:', error);
                    }}
                }}
                
                return [
                    window.vtkMesh ? '🎨 VTK rendered' : '🔄 Loading...',
                    new Date().toLocaleTimeString()
                ];
            }}
            """,
            [Output('status-info', 'children'),
             Output('last-update', 'children')],
            [Input('opacity-control', 'value'),
             Input('wireframe-control', 'value'),
             Input('reset-btn', 'n_clicks')],
            prevent_initial_call=False
        )
    
    def run(self, debug=False):
        """Run the WebGL VTK client"""
        print("🚀 Starting WebGL VTK Client")
        print(f"📍 Client Interface: http://{self.client_host}:{self.client_port}")
        print(f"🎯 VTK Server: {self.vtk_server_url}")
        print("🔧 Features:")
        print("   - WebGL 3D rendering with Three.js")
        print("   - Mouse orbit and zoom controls")
        print("   - Real-time material adjustments")
        print("   - GPU-accelerated local rendering")
        
        self.app.run(
            debug=debug,
            host=self.client_host,
            port=self.client_port,
            dev_tools_hot_reload=False
        )

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    vtk_host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    vtk_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    client_host = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"
    client_port = int(sys.argv[4]) if len(sys.argv) > 4 else 8052
    
    client = WebGLVTKClient(
        vtk_server_host=vtk_host,
        vtk_server_port=vtk_port,
        client_host=client_host,
        client_port=client_port
    )
    client.run() 