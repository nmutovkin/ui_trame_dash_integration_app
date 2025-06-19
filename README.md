# VTK XDMF Dash WebGL Visualization

**Unified VTK visualization with XDMF file support using Dash + Three.js WebGL rendering in a single application.**

## 🚀 Overview

This application provides a complete solution for visualizing **XDMF (eXtensible Data Model and Format)** scientific data files using VTK processing and WebGL rendering. XDMF is widely used in computational science for storing large simulation datasets with XML metadata and HDF5 binary data.

## ✨ Key Features

- **📁 XDMF File Support**: Upload and visualize XDMF files via drag-and-drop interface
- **🌈 Multiple Data Arrays**: Visualize different scalar fields (temperature, pressure, velocity, etc.)
- **🎮 Interactive Controls**: Real-time opacity, wireframe, and array selection
- **🚀 Unified Architecture**: Single process - no WebSockets or complex setup
- **⚡ GPU Rendering**: Three.js WebGL with hardware acceleration
- **🔬 Scientific Ready**: Built for computational science workflows

## 🏗️ Architecture

### Unified Single-Process Design

```
┌─────────────────────────────────────────────────────────────┐
│                VTK XDMF Dash WebGL Application               │
├─────────────────────────────────────────────────────────────┤
│ Frontend (Browser)      │  Backend (Python Server)         │
│                        │                                   │
│ ┌─────────────────────┐ │ ┌───────────────────────────────┐ │
│ │   Dash Web UI       │ │ │      VTK Processing           │ │
│ │ ┌─────────────────┐ │ │ │ ┌───────────────────────────┐ │ │
│ │ │ File Upload     │ │ │ │ │  vtkXdmfReader()          │ │ │
│ │ │ Array Selection │ │ │ │ │  ├─ Load XDMF + H5       │ │ │
│ │ │ Material Ctrls  │ │ │ │ │  ├─ Extract Arrays       │ │ │
│ │ └─────────────────┘ │ │ │ │  └─ Apply Coloring       │ │ │
│ │                     │ │ │ │                           │ │ │
│ │ ┌─────────────────┐ │ │ │ │  Geometry Extraction     │ │ │
│ │ │  Three.js WebGL │ │ │ │ │  ├─ Vertices             │ │ │
│ │ │ ┌─────────────┐ │ │ │ │ │  ├─ Faces/Triangles      │ │ │
│ │ │ │ GPU Render  │ │ │ │ │ │  └─ Color Data           │ │ │
│ │ │ │ Mouse Ctrls │ │ │ │ │ └───────────────────────────┘ │ │
│ │ │ └─────────────┘ │ │ │ └───────────────────────────────┘ │ │
│ │ └─────────────────┘ │ │              │                    │ │
│ └─────────────────────┘ │              │ JSON Data          │ │
│          ▲              │              ▼                    │ │
│          └──────────────┼─ ┌───────────────────────────────┐ │ │
│                         │ │     Dash Callbacks            │ │ │
│                         │ │ ┌───────────────────────────┐ │ │ │
│                         │ │ │ File Upload Handler       │ │ │ │
│                         │ │ │ Array Selection Handler   │ │ │ │
│                         │ │ │ VTK Geometry Processor    │ │ │ │
│                         │ │ └───────────────────────────┘ │ │ │
│                         │ └───────────────────────────────┘ │ │
└─────────────────────────────────────────────────────────────┘
         │                                │
         │        Direct Callbacks       │
         │      (No WebSockets!)          │
         └────────────────────────────────┘
```

### Data Flow Pipeline

1. **File Upload** → Base64 decode → Temporary file → Path resolution
2. **VTK Processing** → vtkXdmfReader → Array detection → Surface extraction
3. **Geometry Extraction** → Vertices + Faces + Colors
4. **WebGL Rendering** → Three.js BufferGeometry → GPU visualization
5. **Interactive Updates** → Direct callbacks → Real-time changes

### Key Architecture Benefits

| Aspect | Previous (Distributed) | XDMF Unified |
|--------|----------------------|--------------|
| **Processes** | 2 (Trame + Dash) | 1 (Dash only) |
| **File Support** | Basic geometry | XDMF + scientific data |
| **Data Arrays** | Single field | Multiple point/cell arrays |
| **Communication** | WebSockets | Direct callbacks |
| **Dependencies** | Complex stack | VTK + Dash + h5py |
| **Deployment** | Multi-step setup | Single command |

**Eliminated Complexity:**
- ❌ **WebSockets**: Direct Python callbacks
- ❌ **Trame Framework**: VTK integrated directly
- ❌ **Multi-Process**: Single unified application
- ❌ **Port Management**: Only one port needed

## 📊 XDMF Format Support

**XDMF** (eXtensible Data Model and Format) combines:
- **XML file (.xdmf)**: Human-readable metadata describing structure
- **HDF5 file (.h5)**: Binary data arrays (geometry, field values)

**Supported Features:**
- ✅ **Unstructured Grids**: Tetrahedral, hexahedral, mixed elements
- ✅ **Point Data**: Scalar fields at mesh vertices  
- ✅ **Cell Data**: Scalar fields at mesh elements
- ✅ **Multiple Arrays**: Switch between different data fields
- ✅ **Automatic Surface Extraction**: UnstructuredGrid → PolyData

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone repository and setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Example Files
```bash
python create_example_xdmf.py
```

### 3. Launch Application
```bash
python launch_unified_app.py
```

### 4. Access & Use
1. **Open browser**: `http://localhost:8050`
2. **Load data**: Click "📦 Load Cube Example" or "🔄 Load Cylinder Example"
3. **Explore**: Select different arrays, adjust opacity, try wireframe mode
4. **Navigate**: Drag to orbit, scroll to zoom

## 🎮 User Interface

### **File Loading (3 Options)**
- **🟢 Example Buttons**: Instant loading of included test data
- **🟢 Directory Upload**: Drag XDMF files (with H5 in same folder)
- **🟡 Manual Upload**: Place files in app directory first

### **Visualization Controls**
- **Array Dropdown**: Select Point/Cell data fields
- **Opacity Slider**: Real-time transparency (0-100%)
- **Wireframe Toggle**: Solid vs wireframe rendering
- **Camera Reset**: Return to default view

### **Mouse Navigation**
- **Drag**: Orbit around object
- **Scroll**: Zoom in/out
- **GPU Accelerated**: Smooth WebGL rendering

## 📋 Example Data

### **🔶 Cube Example** (`cube_example.xdmf` + `cube_example.h5`)
- **Geometry**: 8 vertices, 6 tetrahedral cells
- **Point Data**: Temperature field (20°C - 90°C)
- **Cell Data**: Pressure variations
- **Use Case**: Simple mesh testing

### **🔄 Cylinder Example** (`cylinder_example.xdmf` + `cylinder_example.h5`)
- **Geometry**: 24 vertices, 32 triangular cells
- **Point Data**: Combined height and radius field
- **Cell Data**: Averaged values
- **Use Case**: Complex geometry testing

## 🛠️ Technical Implementation

### VTK Integration
```python
# XDMF File Loading
reader = vtk.vtkXdmfReader()
reader.SetFileName(file_path)
reader.Update()
output = reader.GetOutput()

# Array Detection
point_data = output.GetPointData()
cell_data = output.GetCellData()
for i in range(point_data.GetNumberOfArrays()):
    array_name = point_data.GetArrayName(i)
    available_arrays.append(f"Point: {array_name}")

# Surface Extraction (for UnstructuredGrid)
if vtk_data.IsA("vtkUnstructuredGrid"):
    surface_filter = vtk.vtkDataSetSurfaceFilter()
    surface_filter.SetInputData(vtk_data)
    surface_filter.Update()
    polydata = surface_filter.GetOutput()
```

### Three.js WebGL Rendering
```javascript
// Geometry Creation
const geometry = new THREE.BufferGeometry();
geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
geometry.setIndex(new THREE.BufferAttribute(indices, 1));

// Material with Vertex Colors
const material = new THREE.MeshLambertMaterial({
    vertexColors: true,
    opacity: geometryData.opacity,
    transparent: geometryData.opacity < 1.0,
    wireframe: geometryData.wireframe
});

// Mesh Creation and Scene Addition
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);
```

### Dash Callback Architecture
```python
# File Upload Handler
@app.callback(
    [Output('upload-status', 'children'),
     Output('array-dropdown', 'options'),
     Output('array-dropdown', 'value')],
    [Input('upload-xdmf', 'contents')],
    [State('upload-xdmf', 'filename')]
)
def handle_file_upload(contents, filename):
    # Process uploaded file, load with VTK, return status and array options

# VTK Geometry Processor
@app.callback(
    Output("vtk-geometry-store", "data"),
    [Input("opacity-control", "value"),
     Input("array-dropdown", "value"),
     Input("wireframe-control", "value")]
)
def update_vtk_geometry(opacity, array_selection, wireframe):
    # Apply array coloring, extract geometry data, return for WebGL rendering
```

## 🐛 Troubleshooting

### **✅ Success Indicators**
- Green alert: "✅ File loaded successfully!"
- Array dropdown populated with options
- Geometry statistics displayed
- 3D visualization appears in viewport

### **❌ Common Issues & Solutions**

**"H5 file not found" Error**
```bash
# Ensure files are in app directory
ls *.xdmf *.h5
# Should show: cube_example.xdmf, cube_example.h5, etc.
```

**"Example file not found" Warning**
```bash
python create_example_xdmf.py
```

**WebGL Not Rendering**
- Chrome: Check `chrome://gpu/`
- Firefox: Check `about:support` → Graphics
- Ensure hardware acceleration enabled

**Empty Array Dropdown**
- XDMF file may not contain scalar attributes
- Check source data for point/cell arrays

## 🔧 Customization

### Adding File Formats
```python
def load_file(self, file_path, file_type):
    if file_type == 'xdmf':
        reader = vtk.vtkXdmfReader()
    elif file_type == 'vtu':
        reader = vtk.vtkXMLUnstructuredGridReader()
    elif file_type == 'vtk':
        reader = vtk.vtkUnstructuredGridReader()
    # Add more formats...
```

### Custom Color Maps
```python
lut = vtk.vtkLookupTable()
lut.SetHueRange(0.0, 0.667)  # Red to Blue (reverse)
lut.SetSaturationRange(1.0, 1.0)
lut.Build()
```

### Enhanced WebGL
```javascript
const material = new THREE.MeshPhongMaterial({
    vertexColors: true,
    shininess: 100,
    transparent: true
});
```

## 📁 Project Structure

```
ui_playground/
├── vtk_dash_app.py              # Main unified application
├── launch_unified_app.py        # Simple launcher script
├── create_example_xdmf.py       # Example file generator
├── requirements.txt             # Python dependencies
├── README.md                    # This comprehensive guide
├── cube_example.xdmf/.h5        # Example tetrahedral mesh
├── cylinder_example.xdmf/.h5    # Example triangular mesh
└── venv/                        # Virtual environment
```

## 📈 Performance & Benefits

### **Performance Advantages**
- **Direct Communication**: Python callbacks vs WebSocket overhead
- **Memory Efficiency**: Shared VTK-Dash memory space
- **GPU Acceleration**: Browser WebGL rendering
- **Reduced Latency**: Eliminates network serialization

### **Development Benefits**  
- **Single Codebase**: Unified VTK and web interface
- **Standard Patterns**: Uses Dash callback conventions
- **Easy Debugging**: Single process, unified logging
- **Simple Deployment**: One command to start everything

### **Scaling Considerations**
- **File Size**: Large XDMF files may require processing time
- **Browser Limits**: WebGL geometry size limited by GPU memory
- **Processing**: VTK operations run synchronously in main thread

## 🎯 Use Cases

**Perfect For:**
- **Computational Scientists**: CFD, FEA simulation data visualization
- **Engineers**: Mesh analysis and field data exploration  
- **Researchers**: Interactive scientific data analysis
- **Students**: Learning XDMF format and VTK processing
- **Industry**: Product development and optimization workflows

**Data Types:**
- Finite Element Analysis results
- Computational Fluid Dynamics output
- Heat transfer simulations
- Structural analysis data
- Multi-physics simulation results

## 🚀 Advanced Usage

### **For Your Own Data**
1. **Export XDMF**: Use simulation software to create XDMF files
2. **Place Files**: Copy both `.xdmf` and `.h5` to application folder
3. **Load & Explore**: Use upload interface or example buttons

### **Future Enhancements**
- **Animation**: Time-series data visualization
- **Multi-file**: Load multiple XDMF files simultaneously  
- **Advanced Rendering**: Volume rendering, isosurfaces
- **Export**: Save images and geometry data
- **Cloud Integration**: Remote file loading

## 📞 Support

### **System Requirements**
- **Python**: 3.8+ with VTK 9.0+
- **Browser**: Modern browser with WebGL support
- **Hardware**: Graphics card recommended for large datasets

### **Command Line Options**
```bash
# Basic usage
python launch_unified_app.py

# Custom host/port
python launch_unified_app.py 0.0.0.0 8050

# Debug mode
python launch_unified_app.py 0.0.0.0 8050 debug
```

### **Getting Help**
1. Check browser console for WebGL errors
2. Enable debug mode for detailed logging
3. Verify file permissions and paths
4. Test with provided example files first

---

## 🏁 Success!

**Your VTK XDMF Dash WebGL application is ready for scientific data visualization!**

**Key Benefits Achieved:**
- ✅ **Single Application**: No complex multi-service setup
- ✅ **XDMF Support**: Native scientific data format
- ✅ **GPU Rendering**: Fast WebGL visualization  
- ✅ **Interactive**: Real-time parameter control
- ✅ **User Friendly**: Simple drag-and-drop interface
- ✅ **Extensible**: Foundation for advanced features

**Ready to use**: `python launch_unified_app.py` → `http://localhost:8050` → Click example buttons!

**Perfect for computational scientists, engineers, and researchers working with simulation data.** 🚀 