#!/usr/bin/env python3
"""
Create Example XDMF Files
=========================
Generate sample XDMF (XML + HDF5) files for testing the VTK Dash application.
Creates a simple unstructured grid with scalar data.
"""
import numpy as np
import h5py
import os

def create_simple_cube_xdmf():
    """Create a simple cube mesh with scalar data"""
    
    # Define a simple cube with 8 vertices
    vertices = np.array([
        [0.0, 0.0, 0.0],  # 0
        [1.0, 0.0, 0.0],  # 1  
        [1.0, 1.0, 0.0],  # 2
        [0.0, 1.0, 0.0],  # 3
        [0.0, 0.0, 1.0],  # 4
        [1.0, 0.0, 1.0],  # 5
        [1.0, 1.0, 1.0],  # 6
        [0.0, 1.0, 1.0],  # 7
    ], dtype=np.float64)
    
    # Define connectivity for 6 tetrahedral cells (decompose cube into tetrahedra)
    # Each tetrahedron has 4 vertices
    connectivity = np.array([
        [0, 1, 2, 4],  # tet 0
        [2, 4, 6, 1],  # tet 1
        [1, 2, 6, 5],  # tet 2
        [2, 3, 4, 6],  # tet 3
        [3, 4, 6, 7],  # tet 4
        [0, 2, 3, 4],  # tet 5
    ], dtype=np.int32)
    
    # Create scalar data (temperature field)
    temperature = np.array([
        20.0,   # vertex 0 - cold
        25.0,   # vertex 1
        30.0,   # vertex 2
        22.0,   # vertex 3
        80.0,   # vertex 4 - hot
        85.0,   # vertex 5 - hot
        90.0,   # vertex 6 - hottest
        75.0,   # vertex 7 - hot
    ], dtype=np.float64)
    
    # Create pressure data on cells
    pressure = np.array([
        101325.0,  # cell 0 - atmospheric
        101330.0,  # cell 1
        101320.0,  # cell 2
        101335.0,  # cell 3
        101340.0,  # cell 4
        101315.0,  # cell 5
    ], dtype=np.float64)
    
    return vertices, connectivity, temperature, pressure

def create_complex_mesh_xdmf():
    """Create a more complex mesh (cylinder-like structure)"""
    
    # Create a cylinder-like mesh
    n_theta = 8  # points around circumference
    n_z = 3      # points along height
    
    vertices = []
    theta_vals = np.linspace(0, 2*np.pi, n_theta, endpoint=False)
    z_vals = np.linspace(0, 2, n_z)
    
    # Generate vertices
    for z in z_vals:
        for theta in theta_vals:
            x = np.cos(theta)
            y = np.sin(theta)
            vertices.append([x, y, z])
    
    vertices = np.array(vertices, dtype=np.float64)
    
    # Create connectivity (hexahedral cells)
    connectivity = []
    for k in range(n_z - 1):
        for i in range(n_theta):
            # Create a quad between two layers
            i_next = (i + 1) % n_theta
            
            # Bottom layer indices
            v0 = k * n_theta + i
            v1 = k * n_theta + i_next
            
            # Top layer indices  
            v2 = (k + 1) * n_theta + i_next
            v3 = (k + 1) * n_theta + i
            
            # Create two triangles from the quad
            connectivity.extend([
                [v0, v1, v2],  # triangle 1
                [v0, v2, v3],  # triangle 2
            ])
    
    connectivity = np.array(connectivity, dtype=np.int32)
    
    # Create scalar data based on height and radius
    scalar_data = []
    for vertex in vertices:
        x, y, z = vertex
        radius = np.sqrt(x*x + y*y)
        # Combine height and radius effects
        value = z * 50 + radius * 30
        scalar_data.append(value)
    
    scalar_data = np.array(scalar_data, dtype=np.float64)
    
    # Cell data (average of vertex values)
    cell_data = []
    for cell in connectivity:
        avg_value = np.mean([scalar_data[i] for i in cell])
        cell_data.append(avg_value)
    
    cell_data = np.array(cell_data, dtype=np.float64)
    
    return vertices, connectivity, scalar_data, cell_data

def write_xdmf_files(name, vertices, connectivity, point_data, cell_data, point_data_name="Temperature", cell_data_name="Pressure"):
    """Write XDMF XML file and HDF5 data file"""
    
    h5_filename = f"{name}.h5"
    xdmf_filename = f"{name}.xdmf"
    
    # Write HDF5 data file
    with h5py.File(h5_filename, 'w') as h5f:
        # Geometry data
        h5f.create_dataset('vertices', data=vertices)
        h5f.create_dataset('connectivity', data=connectivity)
        
        # Attribute data
        h5f.create_dataset('point_data', data=point_data)
        h5f.create_dataset('cell_data', data=cell_data)
    
    # Determine topology type
    if connectivity.shape[1] == 3:
        topology_type = "Triangle"
        topology_value = "5"  # VTK cell type for triangle
    elif connectivity.shape[1] == 4:
        topology_type = "Tetrahedron" 
        topology_value = "10"  # VTK cell type for tetrahedron
    else:
        topology_type = "Mixed"
        topology_value = "70"
    
    # Write XDMF XML file
    xdmf_content = f'''<?xml version="1.0" ?>
<!DOCTYPE Xdmf SYSTEM "Xdmf.dtd" []>
<Xdmf Version="3.0">
  <Domain>
    <Grid Name="{name}" GridType="Uniform">
      <Topology TopologyType="{topology_type}" NumberOfElements="{len(connectivity)}">
        <DataItem Dimensions="{len(connectivity)} {connectivity.shape[1]}" 
                  NumberType="Int" Format="HDF">
          {h5_filename}:/connectivity
        </DataItem>
      </Topology>
      
      <Geometry GeometryType="XYZ">
        <DataItem Dimensions="{len(vertices)} 3" 
                  NumberType="Float" Precision="8" Format="HDF">
          {h5_filename}:/vertices
        </DataItem>
      </Geometry>
      
      <!-- Point-based attribute -->
      <Attribute Name="{point_data_name}" AttributeType="Scalar" Center="Node">
        <DataItem Dimensions="{len(point_data)}" 
                  NumberType="Float" Precision="8" Format="HDF">
          {h5_filename}:/point_data
        </DataItem>
      </Attribute>
      
      <!-- Cell-based attribute -->
      <Attribute Name="{cell_data_name}" AttributeType="Scalar" Center="Cell">
        <DataItem Dimensions="{len(cell_data)}" 
                  NumberType="Float" Precision="8" Format="HDF">
          {h5_filename}:/cell_data
        </DataItem>
      </Attribute>
      
    </Grid>
  </Domain>
</Xdmf>'''
    
    with open(xdmf_filename, 'w') as f:
        f.write(xdmf_content)
    
    print(f"✅ Created {xdmf_filename} and {h5_filename}")
    print(f"   Vertices: {len(vertices)}")
    print(f"   Cells: {len(connectivity)}")
    print(f"   Point data range: {point_data.min():.2f} - {point_data.max():.2f}")
    print(f"   Cell data range: {cell_data.min():.2f} - {cell_data.max():.2f}")

def main():
    """Create example XDMF files"""
    print("🏗️  Creating Example XDMF Files for VTK Dash App")
    print("=" * 50)
    
    # Create simple cube example
    print("\n1. Creating simple cube mesh...")
    vertices, connectivity, temperature, pressure = create_simple_cube_xdmf()
    write_xdmf_files("cube_example", vertices, connectivity, temperature, pressure, 
                     "Temperature", "Pressure")
    
    # Create complex mesh example
    print("\n2. Creating cylinder mesh...")
    vertices, connectivity, scalar_data, cell_data = create_complex_mesh_xdmf()
    write_xdmf_files("cylinder_example", vertices, connectivity, scalar_data, cell_data,
                     "Field_Value", "Cell_Average")
    
    print("\n🎯 Example files created successfully!")
    print("\nFiles created:")
    for name in ["cube_example", "cylinder_example"]:
        if os.path.exists(f"{name}.xdmf") and os.path.exists(f"{name}.h5"):
            print(f"  ✅ {name}.xdmf + {name}.h5")
        else:
            print(f"  ❌ {name} files missing")
    
    print("\n📝 Usage:")
    print("  Upload the .xdmf file to the VTK Dash app")
    print("  The corresponding .h5 file must be in the same directory")

if __name__ == "__main__":
    main() 