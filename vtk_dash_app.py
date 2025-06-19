#!/usr/bin/env python3
"""
VTK XDMF Dash WebGL Application
==============================
Unified VTK visualization using Dash + Three.js WebGL rendering with XDMF file support.
Supports uploading and visualizing XDMF (XML + HDF5) files.

Features:
- XDMF file upload and parsing
- Real-time geometry extraction from uploaded data
- Three.js WebGL rendering with GPU acceleration
- Interactive material controls (opacity, wireframe)
- Mouse controls (orbit, zoom)
- Multiple scalar field visualization
"""

import dash
import dash_bootstrap_components as dbc
import vtk
from dash import Input, Output, clientside_callback, dcc, html, State, callback_context
import base64
import io
import os
import tempfile


class VTKXDMFDashApp:
    def __init__(self, host="0.0.0.0", port=8050):
        """
        Initialize unified VTK XDMF Dash Application

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
        self.reader = None

        # State variables
        self.current_opacity = 1.0
        self.current_colormap = "elevation"
        self.wireframe_mode = False
        self.uploaded_file_path = None
        self.available_arrays = []
        self.current_array = None

        self.setup_vtk_pipeline()
        self.setup_layout()
        self.setup_callbacks()

    def load_xdmf_file(self, file_path):
        """Load XDMF file using VTK"""
        try:
            # Create XDMF reader
            reader = vtk.vtkXdmfReader()
            reader.SetFileName(file_path)
            reader.Update()
            
            # Get the output
            output = reader.GetOutput()
            
            if output.GetNumberOfPoints() == 0:
                raise ValueError("No points found in XDMF file")
            
            self.reader = reader
            self.vtk_data = output
            self.uploaded_file_path = file_path
            
            # Get available arrays
            self.available_arrays = []
            point_data = output.GetPointData()
            cell_data = output.GetCellData()
            
            # Point arrays
            for i in range(point_data.GetNumberOfArrays()):
                array_name = point_data.GetArrayName(i)
                if array_name:
                    self.available_arrays.append(f"Point: {array_name}")
            
            # Cell arrays
            for i in range(cell_data.GetNumberOfArrays()):
                array_name = cell_data.GetArrayName(i)
                if array_name:
                    self.available_arrays.append(f"Cell: {array_name}")
            
            # Set first available array as current
            if self.available_arrays:
                self.current_array = self.available_arrays[0]
                self.apply_array_coloring(self.current_array)
            else:
                self.apply_elevation_filter()
            
            # Update mapper
            self.mapper.SetInputData(self.vtk_data)
            
            print(f"✅ Loaded XDMF file: {file_path}")
            print(f"   Points: {output.GetNumberOfPoints()}")
            print(f"   Cells: {output.GetNumberOfCells()}")
            print(f"   Arrays: {len(self.available_arrays)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load XDMF file: {str(e)}")
            return False

    def apply_array_coloring(self, array_selection):
        """Apply coloring based on selected array"""
        if not array_selection or not self.vtk_data:
            return
        
        # Parse array selection
        if array_selection.startswith("Point: "):
            array_name = array_selection[7:]
            array_data = self.vtk_data.GetPointData().GetArray(array_name)
            if array_data:
                self.vtk_data.GetPointData().SetActiveScalars(array_name)
                self.mapper.SetScalarModeToUsePointData()
        elif array_selection.startswith("Cell: "):
            array_name = array_selection[6:]
            array_data = self.vtk_data.GetCellData().GetArray(array_name)
            if array_data:
                self.vtk_data.GetCellData().SetActiveScalars(array_name)
                self.mapper.SetScalarModeToUseCellData()
        
        self.mapper.SetColorModeToMapScalars()
        
        # Set color map
        lut = vtk.vtkLookupTable()
        lut.SetHueRange(0.667, 0.0)  # Blue to Red
        lut.Build()
        self.mapper.SetLookupTable(lut)
        
        self.current_array = array_selection

    def apply_elevation_filter(self):
        """Apply elevation filter for coloring when no arrays are available"""
        elevation = vtk.vtkElevationFilter()
        elevation.SetInputData(self.vtk_data)
        elevation.SetLowPoint(0, -1, 0)
        elevation.SetHighPoint(0, 1, 0)
        elevation.Update()
        
        self.vtk_data = elevation.GetOutput()
        self.current_array = "Elevation"

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
        if not self.vtk_data:
            return {}
        
        # Convert to polydata if needed
        if self.vtk_data.IsA("vtkUnstructuredGrid"):
            surface_filter = vtk.vtkDataSetSurfaceFilter()
            surface_filter.SetInputData(self.vtk_data)
            surface_filter.Update()
            polydata = surface_filter.GetOutput()
        else:
            # For sphere or already polydata - apply elevation if no arrays available
            if not self.uploaded_file_path and self.current_array == "Elevation":
                elevation = vtk.vtkElevationFilter()
                elevation.SetInputData(self.vtk_data)
                elevation.SetLowPoint(0, -1, 0)
                elevation.SetHighPoint(0, 1, 0)
                elevation.Update()
                polydata = elevation.GetOutput()
            else:
                polydata = self.vtk_data

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
            # Default green color
            colors = [0.0, 1.0, 0.0] * num_points

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
                                    "🚀 VTK XDMF Dash WebGL Visualization",
                                    className="text-center mb-4",
                                ),
                                dbc.Alert(
                                    [
                                        html.H5(
                                            "📁 XDMF File Visualization",
                                            className="alert-heading",
                                        ),
                                        html.P(
                                            [
                                                "Upload XDMF files or use default sphere visualization",
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
                                    color="info",
                                    className="mb-4",
                                ),
                                
                                # File Upload Section
                                dbc.Card([
                                    dbc.CardHeader("📤 Upload XDMF File"),
                                    dbc.CardBody([
                                        dcc.Upload(
                                            id='upload-xdmf',
                                            children=html.Div([
                                                '📁 Drag and Drop or ',
                                                html.A('Select XDMF File')
                                            ]),
                                            style={
                                                'width': '100%',
                                                'height': '60px',
                                                'lineHeight': '60px',
                                                'borderWidth': '1px',
                                                'borderStyle': 'dashed',
                                                'borderRadius': '5px',
                                                'textAlign': 'center',
                                                'margin': '10px'
                                            },
                                            multiple=False,
                                            accept='.xdmf'
                                        ),
                                        html.Div(id='upload-status', className="mt-2"),
                                        html.Small(
                                            "Upload .xdmf files. Corresponding .h5 files must be in the same directory.",
                                            className="text-muted"
                                        ),
                                        html.Hr(),
                                        html.Label("Or try example files:"),
                                        dbc.ButtonGroup([
                                            dbc.Button("📦 Load Cube Example", id="load-cube-btn", color="info", size="sm"),
                                            dbc.Button("🔄 Load Cylinder Example", id="load-cylinder-btn", color="info", size="sm"),
                                        ], className="w-100 mt-2")
                                    ])
                                ], className="mb-4"),
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
                                                # Array Selection
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H6("🌈 Data Arrays"),
                                                                html.Label("Active Array:"),
                                                                dcc.Dropdown(
                                                                    id='array-dropdown',
                                                                    options=[],
                                                                    value=None,
                                                                    placeholder="Select data array..."
                                                                ),
                                                                html.Small(
                                                                    "Choose scalar field for coloring", 
                                                                    className="text-muted"
                                                                ),
                                                            ]
                                                        )
                                                    ],
                                                    className="mb-3",
                                                ),
                                                
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

        # File upload callback
        @self.app.callback(
            [Output('upload-status', 'children'),
             Output('array-dropdown', 'options'),
             Output('array-dropdown', 'value')],
            [Input('upload-xdmf', 'contents')],
            [State('upload-xdmf', 'filename')]
        )
        def handle_file_upload(contents, filename):
            """Handle XDMF file upload"""
            if contents is None:
                return "", [], None
            
            try:
                # Decode file content
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                
                # For demonstration, try to load from current directory first
                if filename and os.path.exists(filename):
                    print(f"📁 Loading XDMF file from current directory: {filename}")
                    success = self.load_xdmf_file(filename)
                else:
                    # Save to temporary file and modify XDMF to reference local H5 files
                    with tempfile.NamedTemporaryFile(mode='wb', suffix='.xdmf', delete=False) as tmp_file:
                        tmp_file.write(decoded)
                        tmp_file_path = tmp_file.name
                    
                    # Read the XDMF content and try to modify H5 paths to current directory
                    xdmf_content = decoded.decode('utf-8')
                    
                    # Extract H5 filename from XDMF content
                    import re
                    h5_matches = re.findall(r'([^/\s]+\.h5):', xdmf_content)
                    if h5_matches:
                        h5_filename = h5_matches[0]
                        if os.path.exists(h5_filename):
                            # Modify XDMF to use absolute path to H5 file
                            abs_h5_path = os.path.abspath(h5_filename)
                            modified_content = xdmf_content.replace(h5_filename + ':', abs_h5_path + ':')
                            
                            # Write modified XDMF
                            with open(tmp_file_path, 'w') as f:
                                f.write(modified_content)
                            
                            print(f"📁 Modified XDMF to reference: {abs_h5_path}")
                        else:
                            error_msg = dbc.Alert([
                                html.Strong("❌ H5 file not found!"), html.Br(),
                                f"Looking for: {h5_filename}", html.Br(),
                                "Please ensure the .h5 file is in the same directory as the application."
                            ], color="danger")
                            return error_msg, [], None
                    
                    # Try to load XDMF file
                    success = self.load_xdmf_file(tmp_file_path)
                
                if success:
                    # Create dropdown options for arrays
                    array_options = [{'label': arr, 'value': arr} for arr in self.available_arrays]
                    
                    status_msg = dbc.Alert([
                        html.Strong("✅ File loaded successfully!"), html.Br(),
                        f"📁 {filename}", html.Br(),
                        f"🔢 {self.vtk_data.GetNumberOfPoints():,} points, {self.vtk_data.GetNumberOfCells():,} cells", html.Br(),
                        f"📊 {len(self.available_arrays)} data arrays available"
                    ], color="success")
                    
                    return status_msg, array_options, self.current_array
                else:
                    error_msg = dbc.Alert([
                        html.Strong("❌ Failed to load file!"), html.Br(),
                        "Please check that the XDMF file format is correct and H5 files are available."
                    ], color="danger")
                    return error_msg, [], None
                    
            except Exception as e:
                error_msg = dbc.Alert([
                    html.Strong("❌ Upload error!"), html.Br(),
                    str(e)
                ], color="danger")
                return error_msg, [], None

        # Example file loading callback
        @self.app.callback(
            [Output('upload-status', 'children', allow_duplicate=True),
             Output('array-dropdown', 'options', allow_duplicate=True),
             Output('array-dropdown', 'value', allow_duplicate=True)],
            [Input('load-cube-btn', 'n_clicks'),
             Input('load-cylinder-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def load_example_files(cube_clicks, cylinder_clicks):
            """Load example XDMF files"""
            ctx = callback_context
            if not ctx.triggered:
                return "", [], None
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'load-cube-btn' and cube_clicks:
                filename = "cube_example.xdmf"
            elif button_id == 'load-cylinder-btn' and cylinder_clicks:
                filename = "cylinder_example.xdmf"
            else:
                return "", [], None
            
            if os.path.exists(filename):
                success = self.load_xdmf_file(filename)
                
                if success:
                    array_options = [{'label': arr, 'value': arr} for arr in self.available_arrays]
                    
                    status_msg = dbc.Alert([
                        html.Strong("✅ Example file loaded!"), html.Br(),
                        f"📁 {filename}", html.Br(),
                        f"🔢 {self.vtk_data.GetNumberOfPoints():,} points, {self.vtk_data.GetNumberOfCells():,} cells", html.Br(),
                        f"📊 {len(self.available_arrays)} data arrays available"
                    ], color="success")
                    
                    return status_msg, array_options, self.current_array
                else:
                    error_msg = dbc.Alert([
                        html.Strong("❌ Failed to load example file!"), html.Br(),
                        f"File: {filename}"
                    ], color="danger")
                    return error_msg, [], None
            else:
                error_msg = dbc.Alert([
                    html.Strong("❌ Example file not found!"), html.Br(),
                    f"Looking for: {filename}", html.Br(),
                    "Run 'python create_example_xdmf.py' to generate example files."
                ], color="warning")
                return error_msg, [], None

        # VTK geometry processing callback (includes initial load)
        @self.app.callback(
            Output("vtk-geometry-store", "data"),
            [
                Input("opacity-control", "value"),
                Input("wireframe-control", "value"),
                Input("resolution-control", "value"),
                Input("regenerate-btn", "n_clicks"),
                Input("array-dropdown", "value"),
                Input("trigger-initial-load", "children"),
            ],
            prevent_initial_call=False
        )
        def update_vtk_geometry(opacity, wireframe, resolution, regenerate_clicks, array_selection, trigger_initial):
            """Process VTK data and return geometry for WebGL"""
            # Update state
            self.current_opacity = opacity if opacity is not None else 1.0
            self.wireframe_mode = wireframe if wireframe is not None else False

            # Handle array selection change
            if array_selection and array_selection != self.current_array:
                self.apply_array_coloring(array_selection)

            # Regenerate VTK pipeline if needed (only for default sphere)
            ctx = callback_context
            if (
                ctx.triggered
                and "regenerate-btn" in ctx.triggered[0]["prop_id"]
                and not self.uploaded_file_path  # Only regenerate if using default sphere
            ):
                self.regenerate_vtk_pipeline(resolution if resolution is not None else 30)

            # Extract and return geometry data
            geometry_data = self.extract_geometry_data()

            print(
                f"🎨 VTK Update: opacity={self.current_opacity:.2f}, wireframe={self.wireframe_mode}"
            )
            print(f"   Array: {self.current_array}, vertices={geometry_data.get('vertex_count', 0)}")

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
                html.Br(),
                f"📊 Array: {self.current_array or 'Default'}",
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
        """Start the unified VTK XDMF Dash application"""
        print("🚀 Starting Unified VTK XDMF Dash WebGL Application")
        print("=" * 60)
        print(f"🌐 Application URL: http://{self.host}:{self.port}")
        print("✅ VTK processing: Integrated")
        print("✅ XDMF support: Available")
        print("✅ WebGL rendering: Three.js")
        print("✅ Communication: Direct Dash callbacks")
        print("❌ WebSockets: Eliminated")
        print("❌ Trame: Eliminated")
        print("=" * 60)
        print("🎯 Open browser and upload XDMF files!")

        self.app.run(host=self.host, port=self.port, debug=debug)


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8050
    debug = len(sys.argv) > 3 and sys.argv[3].lower() == "debug"

    app = VTKXDMFDashApp(host=host, port=port)
    app.run(debug=debug)
