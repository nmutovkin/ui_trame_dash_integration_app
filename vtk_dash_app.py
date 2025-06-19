#!/usr/bin/env python3
"""
VTK Dash WebGL Application
=========================
Unified VTK visualization using Dash + Three.js WebGL rendering.
All VTK processing, UI controls, and WebGL rendering in one application.

Features:
- VTK unstructured grid processing
- Real-time geometry extraction (vertices, faces, colors)
- Three.js WebGL rendering with GPU acceleration
- Interactive material controls (opacity, wireframe)
- Mouse controls (orbit, zoom)
- Single application architecture
"""

import dash
import dash_bootstrap_components as dbc
import vtk
from dash import Input, Output, clientside_callback, dcc, html


class VTKDashApp:
    def __init__(self, host="0.0.0.0", port=8050):
        """
        Initialize unified VTK Dash Application

        Args:
            host: Application host interface
            port: Application port
        """
        self.host = host
        self.port = port

        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            external_scripts=[
                "https://unpkg.com/three@0.160.0/build/three.min.js"
            ],
        )

        # VTK objects
        self.vtk_data = None
        self.mapper = vtk.vtkDataSetMapper()
        self.actor = vtk.vtkActor()

        # State variables
        self.current_opacity = 1.0
        self.current_colormap = "elevation"
        self.wireframe_mode = False

        self.setup_vtk_pipeline()
        self.setup_layout()
        self.setup_callbacks()

    def setup_vtk_pipeline(self):
        """Setup VTK visualization pipeline"""
        # Create sample polydata (sphere)
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetThetaResolution(30)
        sphere_source.SetPhiResolution(30)
        sphere_source.Update()
        
        # Keep as PolyData (no need to convert to UnstructuredGrid)
        self.vtk_data = sphere_source.GetOutput()

        # Setup mapper and actor
        self.mapper.SetInputData(self.vtk_data)
        self.actor.SetMapper(self.mapper)

        # Apply elevation filter for coloring
        self.update_colormap()

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
                    faces.extend(
                        [
                            id_list.GetId(0),
                            id_list.GetId(i),
                            id_list.GetId(i + 1),
                        ]
                    )

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
            "wireframe": self.wireframe_mode,
        }

    def setup_layout(self):
        """Setup the unified Dash layout"""
        self.app.layout = dbc.Container(
            [
                        # Store for VTK geometry data
        dcc.Store(id="vtk-geometry-store"),
        
        # Hidden div to trigger initial geometry load
        html.Div(id="trigger-initial-load", style={"display": "none"}),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(
                                    "🚀 VTK Dash WebGL Visualization",
                                    className="text-center mb-4",
                                ),
                                dbc.Alert(
                                    [
                                        html.H5(
                                            "🎮 Unified VTK + WebGL Application",
                                            className="alert-heading",
                                        ),
                                        html.P(
                                            [
                                                "Architecture: ✅ Single Dash app with VTK + Three.js",
                                                html.Br(),
                                                "Rendering: ✅ Client-side WebGL with GPU acceleration",
                                                html.Br(),
                                                "Status: ",
                                                html.Span(
                                                    id="system-status",
                                                    children="🟢 Ready",
                                                ),
                                            ]
                                        ),
                                    ],
                                    color="success",
                                    className="mb-4",
                                ),
                                dbc.Row(
                                    [
                                        # WebGL Viewport
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            "🎨 Three.js WebGL Viewport"
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                html.Canvas(
                                                                    id="webgl-canvas",
                                                                    width=800,
                                                                    height=600,
                                                                    style={
                                                                        "width": "100%",
                                                                        "height": "600px",
                                                                        "border": "2px solid #28a745",
                                                                        "border-radius": "8px",
                                                                        "background": "#1a1a2e",
                                                                        "cursor": "grab",
                                                                    },
                                                                ),
                                                                html.P(
                                                                    [
                                                                        "🎮 Mouse: Drag to orbit, scroll to zoom",
                                                                        html.Br(),
                                                                        "🎯 GPU: Local WebGL rendering",
                                                                        html.Br(),
                                                                        "📊 Data: Direct VTK processing",
                                                                    ],
                                                                    className="mt-3 text-muted small",
                                                                ),
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            md=8,
                                        ),
                                        # Control Panel
                                        dbc.Col(
                                            [
                                                # Material Controls
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H6(
                                                                    "🎨 Material Properties"
                                                                ),
                                                                html.Label(
                                                                    "Opacity:"
                                                                ),
                                                                dcc.Slider(
                                                                    id="opacity-control",
                                                                    min=0,
                                                                    max=1,
                                                                    step=0.05,
                                                                    value=1.0,
                                                                    marks={
                                                                        0: "0%",
                                                                        0.5: "50%",
                                                                        1: "100%",
                                                                    },
                                                                    tooltip={
                                                                        "placement": "bottom",
                                                                        "always_visible": True,
                                                                    },
                                                                ),
                                                                html.Div(
                                                                    className="mt-3"
                                                                ),
                                                                dbc.Switch(
                                                                    id="wireframe-control",
                                                                    label="Wireframe Mode",
                                                                    value=False,
                                                                ),
                                                                html.Small(
                                                                    "Toggle between solid surface and wireframe mesh",
                                                                    className="text-muted",
                                                                ),
                                                            ]
                                                        )
                                                    ],
                                                    className="mb-3",
                                                ),
                                                # VTK Processing Controls
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H6(
                                                                    "🔧 VTK Processing"
                                                                ),
                                                                html.Label(
                                                                    "Sphere Resolution:"
                                                                ),
                                                                dcc.Slider(
                                                                    id="resolution-control",
                                                                    min=10,
                                                                    max=50,
                                                                    step=5,
                                                                    value=30,
                                                                    marks={
                                                                        10: "10",
                                                                        30: "30",
                                                                        50: "50",
                                                                    },
                                                                    tooltip={
                                                                        "placement": "bottom",
                                                                        "always_visible": True,
                                                                    },
                                                                ),
                                                                html.Div(
                                                                    className="mt-3"
                                                                ),
                                                                dbc.Button(
                                                                    "🔄 Regenerate Geometry",
                                                                    id="regenerate-btn",
                                                                    color="info",
                                                                    size="sm",
                                                                    className="w-100",
                                                                ),
                                                                html.Small(
                                                                    "Update VTK pipeline with new parameters",
                                                                    className="text-muted",
                                                                ),
                                                            ]
                                                        )
                                                    ],
                                                    className="mb-3",
                                                ),
                                                # Camera Controls
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H6(
                                                                    "📷 Camera Controls"
                                                                ),
                                                                dbc.Button(
                                                                    "🔄 Reset View",
                                                                    id="reset-btn",
                                                                    color="primary",
                                                                    size="sm",
                                                                    className="w-100",
                                                                ),
                                                                html.Small(
                                                                    "Reset camera to default position",
                                                                    className="text-muted",
                                                                ),
                                                            ]
                                                        )
                                                    ],
                                                    className="mb-3",
                                                ),
                                                # Status Information
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H6(
                                                                    "📊 Status"
                                                                ),
                                                                html.Div(
                                                                    id="status-info",
                                                                    className="small",
                                                                ),
                                                                html.Small(
                                                                    id="last-update",
                                                                    className="text-muted",
                                                                ),
                                                            ]
                                                        )
                                                    ]
                                                ),
                                            ],
                                            md=4,
                                        ),
                                    ]
                                ),
                            ],
                            width=12,
                        )
                    ]
                ),
            ],
            fluid=True,
        )

    def setup_callbacks(self):
        """Setup Dash callbacks for VTK processing and WebGL rendering"""

        # VTK geometry processing callback (includes initial load)
        @self.app.callback(
            Output("vtk-geometry-store", "data"),
            [
                Input("opacity-control", "value"),
                Input("wireframe-control", "value"),
                Input("resolution-control", "value"),
                Input("regenerate-btn", "n_clicks"),
                Input("trigger-initial-load", "children"),
            ],
            prevent_initial_call=False
        )
        def update_vtk_geometry(opacity, wireframe, resolution, regenerate_clicks, trigger_initial):
            """Process VTK data and return geometry for WebGL"""
            # Update state
            self.current_opacity = opacity if opacity is not None else 1.0
            self.wireframe_mode = wireframe if wireframe is not None else False

            # Regenerate VTK pipeline if needed
            ctx = dash.callback_context
            if (
                ctx.triggered
                and "regenerate-btn" in ctx.triggered[0]["prop_id"]
            ):
                self.regenerate_vtk_pipeline(resolution if resolution is not None else 30)

            # Extract and return geometry data
            geometry_data = self.extract_geometry_data()

            print(
                f"🎨 VTK Update: opacity={self.current_opacity:.2f}, wireframe={self.wireframe_mode}, vertices={geometry_data['vertex_count']}"
            )

            return geometry_data

        # Status update callback
        @self.app.callback(
            [
                Output("status-info", "children"),
                Output("last-update", "children"),
            ],
            [Input("vtk-geometry-store", "data")],
        )
        def update_status_info(geometry_data):
            """Update status information"""
            if not geometry_data:
                return "No data", ""

            status = [
                f"🎨 Vertices: {geometry_data.get('vertex_count', 'N/A'):,}",
                html.Br(),
                f"🔺 Faces: {geometry_data.get('face_count', 'N/A'):,}",
                html.Br(),
                f"🎭 Opacity: {geometry_data.get('opacity', 1.0):.2f}",
                html.Br(),
                f"📐 Wireframe: {'On' if geometry_data.get('wireframe', False) else 'Off'}",
            ]

            import datetime

            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            return status, f"Last update: {timestamp}"

        # Main WebGL rendering callback (clientside)
        clientside_callback(
            """
            function(geometryData, resetClicks) {
                const canvas = document.getElementById('webgl-canvas');
                const statusDiv = document.getElementById('system-status');
                
                if (!canvas) {
                    console.error('Canvas not found');
                    return 'Canvas not found';
                }
                
                console.log('WebGL callback called with data:', geometryData ? 'YES' : 'NO');
                
                // Initialize Three.js scene once
                if (!window.sceneInitialized) {
                    console.log('Initializing WebGL scene...');
                    initializeWebGLScene(canvas, statusDiv);
                    window.sceneInitialized = true;
                }
                
                // Update geometry when data changes
                if (geometryData && geometryData.vertices) {
                    console.log('Rendering VTK geometry:', geometryData.vertex_count, 'vertices');
                    renderVTKGeometry(geometryData);
                } else {
                    console.warn('No geometry data available');
                }
                
                // Handle camera reset
                if (resetClicks && window.camera) {
                    console.log('Resetting camera view');
                    window.camera.position.set(0, 0, 8);
                    window.camera.lookAt(0, 0, 0);
                }
                
                // Initialize WebGL scene
                function initializeWebGLScene(canvas, statusDiv) {
                    try {
                        // Check Three.js availability
                        if (typeof THREE === 'undefined') {
                            console.error('Three.js not loaded');
                            if (statusDiv) statusDiv.innerHTML = '❌ Three.js failed to load';
                            return;
                        }
                        
                        console.log('Setting up Three.js scene...');
                        
                        // Scene setup
                        window.scene = new THREE.Scene();
                        window.camera = new THREE.PerspectiveCamera(75, canvas.width / canvas.height, 0.1, 1000);
                        window.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
                        
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
                        
                        // Add a simple test cube to verify Three.js is working
                        const testGeometry = new THREE.BoxGeometry(1, 1, 1);
                        const testMaterial = new THREE.MeshLambertMaterial({ color: 0xff0000 });
                        const testCube = new THREE.Mesh(testGeometry, testMaterial);
                        testCube.position.set(3, 0, 0);  // Place it to the side
                        window.scene.add(testCube);
                        window.testCube = testCube;
                        console.log('Test red cube added to scene');

                        // Animation loop
                        function animate() {
                            requestAnimationFrame(animate);
                            if (window.vtkMesh) {
                                window.vtkMesh.rotation.y += 0.005;
                            }
                            if (window.testCube) {
                                window.testCube.rotation.x += 0.01;
                                window.testCube.rotation.y += 0.01;
                            }
                            window.renderer.render(window.scene, window.camera);
                        }
                        animate();
                        
                        console.log('WebGL scene initialized successfully');
                        if (statusDiv) statusDiv.innerHTML = '🟢 WebGL Ready';
                        
                    } catch (error) {
                        console.error('WebGL initialization failed:', error);
                        if (statusDiv) statusDiv.innerHTML = '❌ WebGL failed';
                    }
                }
                
                // Setup mouse interaction
                function setupMouseControls(canvas, camera) {
                    let isMouseDown = false;
                    let mouseX = 0, mouseY = 0;
                    
                    canvas.addEventListener('mousedown', (event) => {
                        isMouseDown = true;
                        mouseX = event.clientX;
                        mouseY = event.clientY;
                    });
                    
                    canvas.addEventListener('mouseup', () => {
                        isMouseDown = false;
                    });
                    
                    canvas.addEventListener('mousemove', (event) => {
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
                    });
                    
                    canvas.addEventListener('wheel', (event) => {
                        event.preventDefault();
                        const scale = event.deltaY > 0 ? 1.1 : 0.9;
                        camera.position.multiplyScalar(scale);
                    });
                }
                
                // Render VTK geometry data
                function renderVTKGeometry(geometryData) {
                    if (!window.scene) {
                        console.error('Scene not initialized');
                        return;
                    }
                    
                    if (!geometryData || !geometryData.vertices) {
                        console.error('No vertices in geometry data');
                        return;
                    }
                    
                    console.log('Processing geometry data:', {
                        vertices: geometryData.vertices.length,
                        faces: geometryData.faces ? geometryData.faces.length : 0,
                        colors: geometryData.colors ? geometryData.colors.length : 0
                    });
                    
                    // Remove existing mesh
                    if (window.vtkMesh) {
                        window.scene.remove(window.vtkMesh);
                        window.vtkMesh.geometry.dispose();
                        window.vtkMesh.material.dispose();
                    }
                    
                    try {
                        // Create BufferGeometry
                        const geometry = new THREE.BufferGeometry();
                        
                        const vertices = new Float32Array(geometryData.vertices);
                        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
                        console.log('Added vertices:', vertices.length / 3);
                        
                        if (geometryData.colors && geometryData.colors.length > 0) {
                            const colors = new Float32Array(geometryData.colors);
                            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
                            console.log('Added colors:', colors.length / 3);
                        }
                        
                        if (geometryData.faces && geometryData.faces.length > 0) {
                            const indices = new Uint16Array(geometryData.faces);
                            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
                            console.log('Added indices:', indices.length);
                        }
                        
                        geometry.computeVertexNormals();
                        geometry.computeBoundingSphere();
                        
                        // Create material
                        const material = new THREE.MeshLambertMaterial({
                            vertexColors: geometryData.colors && geometryData.colors.length > 0,
                            color: geometryData.colors && geometryData.colors.length > 0 ? 0xffffff : 0x00ff00,
                            side: THREE.DoubleSide,
                            opacity: geometryData.opacity || 1.0,
                            transparent: (geometryData.opacity || 1.0) < 1.0,
                            wireframe: geometryData.wireframe || false
                        });
                        
                        // Create and add mesh
                        window.vtkMesh = new THREE.Mesh(geometry, material);
                        window.scene.add(window.vtkMesh);
                        
                        console.log('VTK mesh added to scene successfully');
                        console.log('Mesh position:', window.vtkMesh.position);
                        console.log('Mesh scale:', window.vtkMesh.scale);
                        console.log('Bounding sphere:', geometry.boundingSphere);
                        
                    } catch (error) {
                        console.error('VTK rendering failed:', error);
                        console.error('Error details:', error.stack);
                    }
                }
                
                return 'WebGL scene updated';
            }
            """,
            Output("system-status", "children"),
            [
                Input("vtk-geometry-store", "data"),
                Input("reset-btn", "n_clicks"),
            ],
        )

    def regenerate_vtk_pipeline(self, resolution):
        """Regenerate VTK pipeline with new parameters"""
        # Create new sphere with updated resolution
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetThetaResolution(resolution)
        sphere_source.SetPhiResolution(resolution)
        sphere_source.Update()

        # Keep as PolyData
        self.vtk_data = sphere_source.GetOutput()

        # Update mapper
        self.mapper.SetInputData(self.vtk_data)
        self.update_colormap()

        print(f"🔄 VTK pipeline regenerated with resolution {resolution}")

    def run(self, debug=False):
        """Start the unified VTK Dash application"""
        print("🚀 Starting Unified VTK Dash WebGL Application")
        print("=" * 60)
        print(f"🌐 Application URL: http://{self.host}:{self.port}")
        print("=" * 60)
        print("🎯 Open browser and start visualizing!")

        self.app.run(host=self.host, port=self.port, debug=debug)


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8050
    debug = len(sys.argv) > 3 and sys.argv[3].lower() == "debug"

    app = VTKDashApp(host=host, port=port)
    app.run(debug=debug)
