#!/usr/bin/env python3
"""
VTK XDMF Dash WebGL Application with Advanced Slicing
====================================================
Unified VTK visualization using Dash + Three.js WebGL rendering with XDMF file support and advanced slicing capabilities.
Supports uploading and visualizing XDMF (XML + HDF5) files with efficient backend slicing for large datasets.

Features:
- XDMF file upload and parsing
- Advanced 3D slicing with customizable planes
- Real-time geometry extraction from uploaded data and slices
- Three.js WebGL rendering with GPU acceleration
- Interactive material controls (opacity, wireframe)
- Mouse controls (orbit, zoom)
- Multiple scalar field visualization
- Large dataset handling with backend slicing optimization
"""

import dash
import dash_bootstrap_components as dbc
import vtk
from dash import Input, Output, clientside_callback, dcc, html, State, callback_context
import base64
import os
import tempfile


class VTKXDMFDashApp:
    def __init__(self, host="0.0.0.0", port=8050):
        """
        Initialize unified VTK XDMF Dash Application with Slicing

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
                "https://unpkg.com/three@0.160.0/build/three.min.js",
                "https://unpkg.com/three@0.160.0/examples/js/controls/OrbitControls.js"
            ],
        )

        # VTK objects
        self.vtk_data = None
        self.original_data = None  # Keep original data for slicing
        self.mapper = vtk.vtkDataSetMapper()
        self.actor = vtk.vtkActor()
        self.reader = None

        # Slicing objects
        self.slice_plane = vtk.vtkPlane()
        self.cutter = vtk.vtkCutter()
        self.slice_filters = {}  # Multiple slice planes
        
        # State variables
        self.current_opacity = 1.0
        self.current_colormap = "elevation"
        self.wireframe_mode = False
        self.uploaded_file_path = None
        self.available_arrays = []
        self.current_array = None
        
        # Slicing state
        self.slicing_enabled = False
        self.slice_position = 0.0
        self.slice_normal = [1, 0, 0]  # X-axis normal
        self.multiple_slices = False
        self.num_slices = 5
        self.slice_spacing = 0.2
        
        # ✅ OPTIMIZATION: Geometry caching
        self._cached_geometry_data = None
        self._geometry_cache_hash = None

        self.setup_vtk_pipeline()
        self.setup_layout()
        self.setup_callbacks()

    def load_large_dataset(self, dataset_type="volume"):
        """Load large example datasets for slicing demonstration from XDMF files"""
        if dataset_type == "volume":
            file_path = "large_volume.xdmf"
            if os.path.exists(file_path) and os.path.exists("large_volume.h5"):
                success = self.load_xdmf_file(file_path)
                if success:
                    print(f"✅ Loaded large volume dataset: {self.vtk_data.GetNumberOfPoints():,} points")
                    # Automatically enable slicing for large datasets
                    self.slicing_enabled = True
                    self.slice_normal = [1, 0, 0]  # X-axis normal
                    self.slice_position = 0
                    return True
                else:
                    print("❌ Failed to load large volume dataset")
                    return False
            else:
                print("❌ Large volume dataset files not found. Run create_example_xdmf.py first")
                return False
                
        elif dataset_type == "extra_large_volume":
            file_path = "extra_large_volume.xdmf"
            if os.path.exists(file_path) and os.path.exists("extra_large_volume.h5"):
                success = self.load_xdmf_file(file_path)
                if success:
                    print(f"✅ Loaded extra large volume dataset: {self.vtk_data.GetNumberOfPoints():,} points")
                    # Automatically enable slicing for large datasets
                    self.slicing_enabled = True
                    self.slice_normal = [1, 0, 0]  # X-axis normal
                    self.slice_position = 0
                    return True
                else:
                    print("❌ Failed to load extra large volume dataset")
                    return False
            else:
                print("❌ Extra large volume dataset files not found. Run create_example_xdmf.py first")
                return False
                
        elif dataset_type == "unstructured":
            file_path = "large_unstructured.xdmf"
            if os.path.exists(file_path) and os.path.exists("large_unstructured.h5"):
                success = self.load_xdmf_file(file_path)
                if success:
                    print(f"✅ Loaded large unstructured dataset: {self.vtk_data.GetNumberOfPoints():,} points")
                    # Automatically enable slicing for large datasets
                    self.slicing_enabled = True
                    self.slice_normal = [1, 0, 0]  # X-axis normal
                    self.slice_position = 0
                    return True
                else:
                    print("❌ Failed to load large unstructured dataset")
                    return False
            else:
                print("❌ Large unstructured dataset files not found. Run create_example_xdmf.py first")
                return False
                
        return False

    def apply_slicing(self):
        """Apply VTK slicing operations to the current dataset"""
        if not self.original_data or not self.slicing_enabled:
            self.vtk_data = self.original_data
            return
            
        print(f"🔪 Applying slicing - Position: {self.slice_position}, Normal: {self.slice_normal}")
        
        # For structured data (vtkImageData), ensure we extract proper geometry
        if self.original_data.IsA("vtkImageData"):
            print("Slicing vtkImageData (structured volume)")
        
        if self.multiple_slices:
            # Multiple parallel slices
            all_slices = vtk.vtkAppendPolyData()
            slices_added = 0
            
            for i in range(self.num_slices):
                offset = (i - self.num_slices // 2) * self.slice_spacing
                
                # Create slice plane
                plane = vtk.vtkPlane()
                plane.SetNormal(self.slice_normal)
                
                # Adjust position based on normal direction
                if self.slice_normal[0] == 1:  # X-normal
                    plane.SetOrigin(self.slice_position + offset, 0, 0)
                elif self.slice_normal[1] == 1:  # Y-normal
                    plane.SetOrigin(0, self.slice_position + offset, 0)
                else:  # Z-normal
                    plane.SetOrigin(0, 0, self.slice_position + offset)
                
                # Create cutter
                cutter = vtk.vtkCutter()
                cutter.SetInputData(self.original_data)
                cutter.SetCutFunction(plane)
                cutter.Update()
                
                slice_output = cutter.GetOutput()
                if slice_output.GetNumberOfPoints() > 0:
                    all_slices.AddInputData(slice_output)
                    slices_added += 1
                    print(f"  Added slice {i+1} with {slice_output.GetNumberOfPoints():,} points")
            
            if slices_added > 0:
                all_slices.Update()
                self.vtk_data = all_slices.GetOutput()
                print(f"  Combined {slices_added} slices with total {self.vtk_data.GetNumberOfPoints():,} points")
            else:
                print("⚠️ No slices generated! Using original data")
                self.vtk_data = self.original_data
            
        else:
            # Single slice
            self.slice_plane.SetNormal(self.slice_normal)
            
            # Adjust position based on normal direction and dataset bounds
            bounds = self.original_data.GetBounds()
            center_x = (bounds[0] + bounds[1]) / 2
            center_y = (bounds[2] + bounds[3]) / 2
            center_z = (bounds[4] + bounds[5]) / 2
            
            print(f"Dataset bounds: X[{bounds[0]:.1f}, {bounds[1]:.1f}], Y[{bounds[2]:.1f}, {bounds[3]:.1f}], Z[{bounds[4]:.1f}, {bounds[5]:.1f}]")
            print(f"Dataset center: ({center_x:.1f}, {center_y:.1f}, {center_z:.1f})")
            
            # Scale slice position to dataset size
            if self.slice_normal[0] == 1:  # X-normal
                slice_x = center_x + self.slice_position * (bounds[1] - bounds[0]) / 100.0
                self.slice_plane.SetOrigin(slice_x, center_y, center_z)
                print(f"X-normal slice at x={slice_x:.1f}")
            elif self.slice_normal[1] == 1:  # Y-normal
                slice_y = center_y + self.slice_position * (bounds[3] - bounds[2]) / 100.0
                self.slice_plane.SetOrigin(center_x, slice_y, center_z)
                print(f"Y-normal slice at y={slice_y:.1f}")
            else:  # Z-normal
                slice_z = center_z + self.slice_position * (bounds[5] - bounds[4]) / 100.0
                self.slice_plane.SetOrigin(center_x, center_y, slice_z)
                print(f"Z-normal slice at z={slice_z:.1f}")
            
            self.cutter.SetInputData(self.original_data)
            self.cutter.SetCutFunction(self.slice_plane)
            self.cutter.Update()
            
            slice_output = self.cutter.GetOutput()
            if slice_output.GetNumberOfPoints() > 0:
                self.vtk_data = slice_output
                print(f"✅ Slice created with {slice_output.GetNumberOfPoints():,} points and {slice_output.GetNumberOfCells():,} cells")
            else:
                print("⚠️ No points in slice! Using original data")
                self.vtk_data = self.original_data
        
        # Update mapper
        self.mapper.SetInputData(self.vtk_data)

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
            
            print(f"XDMF file loaded: {output.GetClassName()} with {output.GetNumberOfPoints():,} points and {output.GetNumberOfCells():,} cells")
            
            # For image data, ensure we have proper visualization
            if output.IsA("vtkImageData"):
                print("Converting vtkImageData to vtkStructuredGrid for better visualization")
                # Convert to structured grid for better visualization
                converter = vtk.vtkImageDataToPointSet()
                converter.SetInputData(output)
                converter.Update()
                output = converter.GetOutput()
                print(f"Converted to {output.GetClassName()} with {output.GetNumberOfPoints():,} points")
            
            self.reader = reader
            self.original_data = output  # Keep original for slicing
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
        # Create sample polydata (sphere) - small default dataset
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetThetaResolution(30)
        sphere_source.SetPhiResolution(30)
        sphere_source.SetRadius(50)  # Make it larger to be visible
        sphere_source.Update()
        
        # Keep as PolyData (no need to convert to UnstructuredGrid)
        self.original_data = sphere_source.GetOutput()  # Keep original for slicing
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
        """Extract geometry data for WebGL rendering with lazy loading optimization"""
        if not self.vtk_data:
            print("⚠️ No VTK data available for extraction")
            return {}
        
        # ✅ OPTIMIZATION: Only extract if data changed
        current_hash = hash((
            id(self.vtk_data), 
            self.current_opacity, 
            self.wireframe_mode,
            self.current_array,
            self.slicing_enabled,
            self.slice_position,
            tuple(self.slice_normal),
            self.multiple_slices,
            self.num_slices
        ))
        
        if hasattr(self, '_geometry_cache_hash') and self._geometry_cache_hash == current_hash:
            print("🚀 Using cached geometry data (no recomputation needed)")
            return self._cached_geometry_data
        
        # Apply slicing before geometry extraction
        self.apply_slicing()
        
        print(f"🔄 Extracting geometry data... ({self.vtk_data.GetNumberOfPoints():,} points)")
        
        # Convert to polydata if needed
        if self.vtk_data.IsA("vtkUnstructuredGrid"):
            print("Converting vtkUnstructuredGrid to polydata")
            surface_filter = vtk.vtkDataSetSurfaceFilter()
            surface_filter.SetInputData(self.vtk_data)
            surface_filter.Update()
            polydata = surface_filter.GetOutput()
            print(f"Converted to polydata: {polydata.GetNumberOfPoints():,} points, {polydata.GetNumberOfCells():,} cells")
        elif self.vtk_data.IsA("vtkImageData"):
            print("Converting vtkImageData to polydata")
            # For image data, we need to extract the surface
            geometry_filter = vtk.vtkImageDataGeometryFilter()
            geometry_filter.SetInputData(self.vtk_data)
            geometry_filter.Update()
            polydata = geometry_filter.GetOutput()
            print(f"Converted to polydata: {polydata.GetNumberOfPoints():,} points, {polydata.GetNumberOfCells():,} cells")
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
            print(f"Using existing polydata: {polydata.GetNumberOfPoints():,} points, {polydata.GetNumberOfCells():,} cells")

        # Extract vertices
        points = polydata.GetPoints()
        num_points = points.GetNumberOfPoints()
        
        if num_points == 0:
            print("⚠️ No points in polydata after processing!")
            return {}
        
        # ✅ OPTIMIZATION: Use numpy for faster array operations
        try:
            import numpy as np
            # Fast numpy extraction
            vertices_np = np.array([points.GetPoint(i) for i in range(num_points)], dtype=np.float32)
            vertices = vertices_np.flatten().tolist()
        except ImportError:
            # Fallback to manual extraction
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
        
        if len(faces) == 0:
            print("⚠️ No faces found in polydata!")
            # Try to create faces from the points
            if num_points > 0:
                print("Creating a simple triangle to make something visible")
                faces = [0, 1, 2]  # Simple triangle with first 3 points

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

        geometry_data = {
            "vertices": vertices,
            "faces": faces,
            "colors": colors,
            "vertex_count": num_points,
            "face_count": len(faces) // 3,
            "opacity": self.current_opacity,
            "wireframe": self.wireframe_mode,
        }
        
        # ✅ Cache the result
        self._cached_geometry_data = geometry_data
        self._geometry_cache_hash = current_hash
        
        print(f"✅ Geometry extracted: {num_points:,} vertices, {len(faces)//3:,} faces")
        return geometry_data

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
                                            dbc.Button("📊 Load Large Volume (1M cells)", id="load-large-volume-btn", color="warning", size="sm"),
                                            dbc.Button("📊 Load Extra Large Volume (3.4M cells)", id="load-extra-large-volume-btn", color="danger", size="sm"),
                                            dbc.Button("📊 Load Large Unstructured (100K points)", id="load-unstructured-btn", color="info", size="sm"),
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
                                                                html.Div([
                                                                    html.Div(
                                                                        html.Canvas(
                                                                            id="webgl-canvas",
                                                                            style={
                                                                                "width": "100%",
                                                                                "height": "600px",
                                                                                "border": "2px solid #28a745",
                                                                                "border-radius": "8px",
                                                                                "background": "#1a1a2e",
                                                                                "cursor": "grab",
                                                                                "display": "block",
                                                                            },
                                                                        ),
                                                                        style={"width": "100%", "height": "600px"},
                                                                    ),
                                                                    html.Div(
                                                                        id="colorbar-container",
                                                                        style={
                                                                            "height": "40px",
                                                                            "width": "100%",
                                                                            "margin-top": "10px",
                                                                            "position": "relative",
                                                                            "background": "linear-gradient(to right, #0000ff, #00ffff, #00ff00, #ffff00, #ff0000)",
                                                                            "border-radius": "4px",
                                                                            "border": "1px solid #ccc",
                                                                        }
                                                                    ),
                                                                    html.Div(
                                                                        id="colorbar-labels",
                                                                        style={
                                                                            "display": "flex",
                                                                            "justify-content": "space-between",
                                                                            "margin-top": "5px",
                                                                        },
                                                                        children=[
                                                                            html.Span(id="colorbar-min", className="small"),
                                                                            html.Span(id="colorbar-title", className="small font-weight-bold"),
                                                                            html.Span(id="colorbar-max", className="small"),
                                                                        ]
                                                                    ),
                                                                ]),
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
                                                # Large Dataset Controls
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H6(
                                                                    "📊 Large Dataset Controls"
                                                                ),
                                                                html.Small(
                                                                    "Load large datasets and enable slicing for best performance",
                                                                    className="text-muted mb-3",
                                                                ),
                                                                dbc.ButtonGroup([
                                                                    dbc.Button(
                                                                        "📊 1M Cells",
                                                                        id="create-volume-btn",
                                                                        color="warning",
                                                                        size="sm",
                                                                    ),
                                                                    dbc.Button(
                                                                        "📊 3.4M Cells",
                                                                        id="create-extra-large-volume-btn",
                                                                        color="danger",
                                                                        size="sm",
                                                                    ),
                                                                ], className="w-100"),
                                                                html.Div(
                                                                    className="mt-2"
                                                                ),
                                                                dbc.ButtonGroup([
                                                                    dbc.Button(
                                                                        "📊 100K Unstructured",
                                                                        id="create-unstructured-btn",
                                                                        color="info",
                                                                        size="sm",
                                                                    ),
                                                                    dbc.Button(
                                                                        "🔄 Reset View",
                                                                        id="reset-view-btn",
                                                                        color="secondary",
                                                                        size="sm",
                                                                    ),
                                                                ], className="w-100 mt-2"),
                                                                html.Div(id="dataset-info", className="small text-muted mt-2"),
                                                            ]
                                                        )
                                                    ],
                                                    className="mb-3",
                                                ),
                                                
                                                # Slicing Controls
                                                dbc.Card(
                                                    [
                                                        dbc.CardBody(
                                                            [
                                                                html.H6(
                                                                    "🔪 3D Slicing Controls"
                                                                ),
                                                                dbc.Switch(
                                                                    id="slicing-enabled",
                                                                    label="Enable Slicing",
                                                                    value=False,
                                                                ),
                                                                html.Div(
                                                                    id="slicing-controls",
                                                                    children=[
                                                                        html.Label(
                                                                            "Slice Direction:", className="mt-3"
                                                                        ),
                                                                        dcc.Dropdown(
                                                                            id="slice-normal",
                                                                            options=[
                                                                                {"label": "X-Axis (YZ Plane)", "value": "x"},
                                                                                {"label": "Y-Axis (XZ Plane)", "value": "y"},
                                                                                {"label": "Z-Axis (XY Plane)", "value": "z"},
                                                                            ],
                                                                            value="x",
                                                                        ),
                                                                        html.Label(
                                                                            "Slice Position:", className="mt-3"
                                                                        ),
                                                                        dcc.Slider(
                                                                            id="slice-position",
                                                                            min=-50,
                                                                            max=50,
                                                                            step=1,
                                                                            value=0,
                                                                            marks={
                                                                                -50: "-50%",
                                                                                -25: "-25%",
                                                                                0: "center",
                                                                                25: "+25%",
                                                                                50: "+50%",
                                                                            },
                                                                            tooltip={
                                                                                "placement": "bottom",
                                                                                "always_visible": True,
                                                                            },
                                                                        ),
                                                                        html.Div(className="mt-3"),
                                                                        dbc.Switch(
                                                                            id="multiple-slices",
                                                                            label="Multiple Slices",
                                                                            value=False,
                                                                        ),
                                                                        html.Div(
                                                                            id="multiple-slice-controls",
                                                                            children=[
                                                                                html.Label(
                                                                                    "Number of Slices:", className="mt-2"
                                                                                ),
                                                                                dcc.Slider(
                                                                                    id="num-slices",
                                                                                    min=2,
                                                                                    max=10,
                                                                                    step=1,
                                                                                    value=5,
                                                                                    marks={i: str(i) for i in range(2, 11)},
                                                                                    tooltip={
                                                                                        "placement": "bottom",
                                                                                        "always_visible": True,
                                                                                    },
                                                                                ),
                                                                                html.Label(
                                                                                    "Slice Spacing:", className="mt-2"
                                                                                ),
                                                                                dcc.Slider(
                                                                                    id="slice-spacing",
                                                                                    min=1,
                                                                                    max=20,
                                                                                    step=1,
                                                                                    value=10,
                                                                                    marks={
                                                                                        1: "1",
                                                                                        10: "10",
                                                                                        20: "20",
                                                                                    },
                                                                                    tooltip={
                                                                                        "placement": "bottom",
                                                                                        "always_visible": True,
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={"display": "none"},
                                                                        ),
                                                                    ],
                                                                    style={"display": "none"},
                                                                ),
                                                                html.Small(
                                                                    "Slice large 3D datasets for efficient visualization",
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
            [Input('load-large-volume-btn', 'n_clicks'),
             Input('load-extra-large-volume-btn', 'n_clicks'),
             Input('load-unstructured-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def load_example_files(large_volume_clicks, extra_large_volume_clicks, unstructured_clicks):
            """Load large XDMF datasets"""
            ctx = callback_context
            if not ctx.triggered:
                return "", [], None
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'load-large-volume-btn' and large_volume_clicks:
                success = self.load_large_dataset("volume")
            elif button_id == 'load-extra-large-volume-btn' and extra_large_volume_clicks:
                success = self.load_large_dataset("extra_large_volume")
            elif button_id == 'load-unstructured-btn' and unstructured_clicks:
                success = self.load_large_dataset("unstructured")
            else:
                return "", [], None
            
            if success:
                array_options = [{'label': arr, 'value': arr} for arr in self.available_arrays]
                
                status_msg = dbc.Alert([
                    html.Strong("✅ Large dataset loaded!"), html.Br(),
                    f"📁 {self.uploaded_file_path}", html.Br(),
                    f"🔢 {self.vtk_data.GetNumberOfPoints():,} points, {self.vtk_data.GetNumberOfCells():,} cells", html.Br(),
                    f"📊 {len(self.available_arrays)} data arrays available", html.Br(),
                    html.Strong("⚠️ Enable slicing for better performance!")
                ], color="success")
                
                return status_msg, array_options, self.current_array
            else:
                error_msg = dbc.Alert([
                    html.Strong("❌ Failed to load dataset!"), html.Br(),
                    "Run 'python create_example_xdmf.py' to generate large datasets first."
                ], color="danger")
                return error_msg, [], None

        # VTK geometry processing callback (includes initial load)
        @self.app.callback(
            Output("vtk-geometry-store", "data"),
            [
                Input("opacity-control", "value"),
                Input("wireframe-control", "value"),
                Input("create-volume-btn", "n_clicks"),
                Input("create-extra-large-volume-btn", "n_clicks"),
                Input("create-unstructured-btn", "n_clicks"),
                Input("array-dropdown", "value"),
                Input("slicing-enabled", "value"),
                Input("slice-position", "value"),
                Input("slice-normal", "value"),
                Input("multiple-slices", "value"),
                Input("num-slices", "value"),
                Input("slice-spacing", "value"),
                Input("trigger-initial-load", "children"),
            ],
            prevent_initial_call=False
        )
        def update_vtk_geometry(opacity, wireframe, volume_clicks, extra_large_volume_clicks, unstructured_clicks,
                               array_selection, slicing_enabled, slice_position, slice_normal, 
                               multiple_slices, num_slices, slice_spacing, trigger_initial):
            """Process VTK data and return geometry for WebGL"""
            # Update state
            self.current_opacity = opacity if opacity is not None else 1.0
            self.wireframe_mode = wireframe if wireframe is not None else False

            # Update slicing parameters (only if UI controls were changed)
            ctx = callback_context
            if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] != "create-volume-btn" and \
               ctx.triggered[0]['prop_id'].split('.')[0] != "create-extra-large-volume-btn" and \
               ctx.triggered[0]['prop_id'].split('.')[0] != "create-unstructured-btn":
                self.slicing_enabled = slicing_enabled or False
                self.slice_position = slice_position or 0
                self.multiple_slices = multiple_slices or False
                self.num_slices = num_slices or 5
                self.slice_spacing = (slice_spacing or 10) / 10.0  # Convert to proper scale
                
                # Convert slice normal from string to vector
                if slice_normal == "x":
                    self.slice_normal = [1, 0, 0]
                elif slice_normal == "y":
                    self.slice_normal = [0, 1, 0]
                else:  # z
                    self.slice_normal = [0, 0, 1]

            # Handle array selection change
            if array_selection and array_selection != self.current_array:
                self.apply_array_coloring(array_selection)

            # Check trigger source for special actions
            if ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if trigger_id == "create-volume-btn":
                    success = self.load_large_dataset("volume")
                    if success:
                        print("📊 Loaded large volume dataset (1M cells) for slicing demonstration")
                    else:
                        print("❌ Failed to load large volume dataset. Run create_example_xdmf.py first")
                elif trigger_id == "create-extra-large-volume-btn":
                    success = self.load_large_dataset("extra_large_volume")
                    if success:
                        print("📊 Loaded extra large volume dataset (3.4M cells) for slicing demonstration")
                    else:
                        print("❌ Failed to load extra large volume dataset. Run create_example_xdmf.py first")
                elif trigger_id == "create-unstructured-btn":
                    success = self.load_large_dataset("unstructured")
                    if success:
                        print("📊 Loaded large unstructured dataset (100K points) for slicing demonstration")
                    else:
                        print("❌ Failed to load large unstructured dataset. Run create_example_xdmf.py first")

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
                f"🔪 Slicing: {'On' if self.slicing_enabled else 'Off'}",
                html.Br(),
                f"📊 Array: {self.current_array or 'Default'}",
            ]
            
            # Add slicing details if enabled
            if self.slicing_enabled:
                status.extend([
                    html.Br(),
                    f"📍 Position: {self.slice_position}",
                    html.Br(),
                    f"📐 Direction: {self.slice_normal}",
                    html.Br(),
                    f"🔢 Multi-slice: {'Yes' if self.multiple_slices else 'No'}",
                ])
                if self.multiple_slices:
                    status.extend([
                        html.Br(),
                        f"🔢 Count: {self.num_slices}",
                    ])

            import datetime

            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            return status, f"Last update: {timestamp}"

        # Slicing UI visibility callbacks
        @self.app.callback(
            Output("slicing-controls", "style"),
            [Input("slicing-enabled", "value")]
        )
        def toggle_slicing_controls(slicing_enabled):
            """Show/hide slicing controls based on enable switch"""
            if slicing_enabled:
                return {"display": "block"}
            else:
                return {"display": "none"}

        @self.app.callback(
            Output("multiple-slice-controls", "style"),
            [Input("multiple-slices", "value")]
        )
        def toggle_multiple_slice_controls(multiple_slices):
            """Show/hide multiple slice controls"""
            if multiple_slices:
                return {"display": "block"}
            else:
                return {"display": "none"}

        # Colorbar update callback
        @self.app.callback(
            [Output("colorbar-min", "children"),
             Output("colorbar-max", "children"),
             Output("colorbar-title", "children")],
            [Input("array-dropdown", "value")]
        )
        def update_colorbar_labels(array_selection):
            """Update colorbar labels based on selected array"""
            if not array_selection or not self.vtk_data:
                return "Min", "Max", "Scalar Field"
            
            # Get array name from selection
            if array_selection.startswith("Point: "):
                array_name = array_selection[7:]
                array_data = self.vtk_data.GetPointData().GetArray(array_name)
            elif array_selection.startswith("Cell: "):
                array_name = array_selection[6:]
                array_data = self.vtk_data.GetCellData().GetArray(array_name)
            else:
                array_name = array_selection
                array_data = None
                
            if array_data:
                # Get range of data
                data_range = array_data.GetRange()
                return f"{data_range[0]:.2f}", f"{data_range[1]:.2f}", array_name
            else:
                return "Min", "Max", array_name

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
                    window.camera.position.set(0, 0, 200);
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
                        window.scene.background = new THREE.Color(0x1a1a2e);
                        
                        // Camera setup with better defaults for scientific visualization
                        const width = canvas.clientWidth;
                        const height = canvas.clientHeight;
                        const aspect = width / height;
                        window.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 10000);
                        window.camera.position.set(0, 0, 200);
                        window.camera.lookAt(0, 0, 0);
                        
                        // Renderer setup
                        window.renderer = new THREE.WebGLRenderer({ 
                            canvas: canvas, 
                            antialias: true,
                            preserveDrawingBuffer: true
                        });
                        window.renderer.setSize(width, height);
                        window.renderer.setPixelRatio(window.devicePixelRatio);
                        
                        // Handle window resizing
                        window.addEventListener('resize', function() {
                            const newWidth = canvas.clientWidth;
                            const newHeight = canvas.clientHeight;
                            window.camera.aspect = newWidth / newHeight;
                            window.camera.updateProjectionMatrix();
                            window.renderer.setSize(newWidth, newHeight);
                        });
                        
                        // Lighting
                        const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
                        directionalLight1.position.set(1, 1, 1);
                        window.scene.add(directionalLight1);
                        
                        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
                        directionalLight2.position.set(-1, -1, -1);
                        window.scene.add(directionalLight2);
                        
                        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
                        window.scene.add(ambientLight);
                        
                        // Add a subtle grid for reference
                        const gridHelper = new THREE.GridHelper(200, 20, 0x444444, 0x222222);
                        gridHelper.material.opacity = 0.5;
                        gridHelper.material.transparent = true;
                        window.scene.add(gridHelper);
                        
                        // Add subtle axes helper
                        const axesHelper = new THREE.AxesHelper(50);
                        axesHelper.material.opacity = 0.7;
                        axesHelper.material.transparent = true;
                        window.scene.add(axesHelper);
                        
                        // Setup mouse controls (OrbitControls)
                        setupMouseControls(canvas, window.camera);
                        
                        // No test cube needed
                        
                        // Animation loop
                        function animate() {
                            requestAnimationFrame(animate);
                            if (window.vtkMesh) {
                                // Don't rotate automatically
                                // window.vtkMesh.rotation.y += 0.005;
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
                    // Use OrbitControls if available
                    if (typeof THREE.OrbitControls !== 'undefined') {
                        window.controls = new THREE.OrbitControls(camera, canvas);
                        window.controls.enableDamping = true;
                        window.controls.dampingFactor = 0.25;
                        window.controls.screenSpacePanning = false;
                        window.controls.maxPolarAngle = Math.PI;
                        window.controls.update();
                        console.log('OrbitControls initialized');
                        return;
                    }
                    
                    // Fallback to manual controls
                    let isMouseDown = false;
                    let mouseX = 0, mouseY = 0;
                    
                    canvas.addEventListener('mousedown', (event) => {
                        isMouseDown = true;
                        mouseX = event.clientX;
                        mouseY = event.clientY;
                        canvas.style.cursor = 'grabbing';
                    });
                    
                    canvas.addEventListener('mouseup', () => {
                        isMouseDown = false;
                        canvas.style.cursor = 'grab';
                    });
                    
                    canvas.addEventListener('mouseleave', () => {
                        isMouseDown = false;
                        canvas.style.cursor = 'grab';
                    });
                    
                    canvas.addEventListener('mousemove', (event) => {
                        if (!isMouseDown) return;
                        
                        const deltaX = event.clientX - mouseX;
                        const deltaY = event.clientY - mouseY;
                        
                        const rotationSpeed = 0.005;
                        camera.position.x = camera.position.x * Math.cos(rotationSpeed * deltaX) - camera.position.z * Math.sin(rotationSpeed * deltaX);
                        camera.position.z = camera.position.z * Math.cos(rotationSpeed * deltaX) + camera.position.x * Math.sin(rotationSpeed * deltaX);
                        
                        camera.position.y += deltaY * rotationSpeed * 5;
                        
                        camera.lookAt(0, 0, 0);
                        
                        mouseX = event.clientX;
                        mouseY = event.clientY;
                    });
                    
                    canvas.addEventListener('wheel', (event) => {
                        event.preventDefault();
                        const zoomFactor = event.deltaY > 0 ? 1.1 : 0.9;
                        const distance = camera.position.length();
                        if ((distance > 10 || zoomFactor > 1) && (distance < 1000 || zoomFactor < 1)) {
                            camera.position.multiplyScalar(zoomFactor);
                        }
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
                            const indices = new Uint32Array(geometryData.faces);
                            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
                            console.log('Added indices:', indices.length);
                        } else {
                            console.warn('No faces provided, creating points visualization');
                            // If no faces, create a point cloud instead
                            const pointMaterial = new THREE.PointsMaterial({
                                size: 3,
                                vertexColors: geometryData.colors && geometryData.colors.length > 0,
                                color: 0x00ff00,
                                opacity: geometryData.opacity || 1.0,
                                transparent: (geometryData.opacity || 1.0) < 1.0,
                            });
                            
                            window.vtkMesh = new THREE.Points(geometry, pointMaterial);
                            window.scene.add(window.vtkMesh);
                            
                            console.log('Point cloud created instead of mesh');
                            return;
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
                        
                        // Adjust camera to fit the geometry
                        if (geometry.boundingSphere && window.camera) {
                            const radius = geometry.boundingSphere.radius;
                            const center = geometry.boundingSphere.center;
                            
                            console.log('Adjusting camera to fit geometry:', {
                                radius: radius,
                                center: center
                            });
                            
                            // Position camera to see the entire object
                            window.camera.position.set(
                                center.x + radius * 2,
                                center.y + radius * 2,
                                center.z + radius * 2
                            );
                            window.camera.lookAt(center.x, center.y, center.z);
                        }
                        
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
                Input("reset-view-btn", "n_clicks"),
            ],
        )

        # Dataset info update callback
        @self.app.callback(
            Output("dataset-info", "children"),
            [Input("vtk-geometry-store", "data")]
        )
        def update_dataset_info(geometry_data):
            """Update dataset information"""
            if not geometry_data or not self.vtk_data:
                return ""
            
            # Get dataset information
            points = self.vtk_data.GetNumberOfPoints()
            cells = self.vtk_data.GetNumberOfCells()
            
            if points > 1000000:
                points_str = f"{points/1000000:.1f}M"
            else:
                points_str = f"{points/1000:.1f}K"
                
            if cells > 1000000:
                cells_str = f"{cells/1000000:.1f}M"
            else:
                cells_str = f"{cells/1000:.1f}K"
            
            return [
                f"Dataset: {points_str} points, {cells_str} cells",
                html.Br(),
                f"Slicing: {'Enabled' if self.slicing_enabled else 'Disabled'}"
            ]

        # Update slicing controls when dataset changes
        @self.app.callback(
            Output("slicing-enabled", "value"),
            [Input("create-volume-btn", "n_clicks"),
             Input("create-extra-large-volume-btn", "n_clicks"),
             Input("create-unstructured-btn", "n_clicks")],
            prevent_initial_call=True
        )
        def update_slicing_state(volume_clicks, extra_large_volume_clicks, unstructured_clicks):
            """Update slicing state when large datasets are loaded"""
            # For large datasets, we automatically enable slicing
            return True



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
