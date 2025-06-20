#!/usr/bin/env python3
"""
Create Example XDMF Files
=========================
Generate sample XDMF (XML + HDF5) files for testing the VTK Dash application.
Creates simple unstructured grids with scalar data and large volume datasets for slicing demonstrations.
"""
import numpy as np
import h5py
import os
import vtk
import time

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

def create_large_volume_dataset(size=(100, 100, 100), save_xdmf=True):
    """Create a large 3D volume dataset for slicing demonstration
    
    Args:
        size: Tuple (nx, ny, nz) specifying dimensions
        save_xdmf: Whether to save as XDMF file
        
    Returns:
        VTK image data object or None if save_xdmf is True
    """
    print(f"🔄 Creating large volume dataset {size[0]}x{size[1]}x{size[2]}...")
    start_time = time.time()
    
    # Create structured volume using VTK
    image_data = vtk.vtkImageData()
    image_data.SetDimensions(*size)
    image_data.SetSpacing(1.0, 1.0, 1.0)
    image_data.SetOrigin(-size[0]//2, -size[1]//2, -size[2]//2)
    
    # Create complex scalar field
    scalar_array = vtk.vtkFloatArray()
    scalar_array.SetName("Density")
    scalar_array.SetNumberOfTuples(size[0] * size[1] * size[2])
    
    print("🔄 Generating scalar field...")
    for k in range(size[2]):
        for j in range(size[1]):
            for i in range(size[0]):
                x, y, z = i - size[0]//2, j - size[1]//2, k - size[2]//2
                
                # Complex function with multiple features
                r = np.sqrt(x*x + y*y + z*z)
                val = np.sin(r * 0.05) * np.cos(y*0.1) * np.exp(-z*z*0.001)
                val += np.sin(np.sqrt(x*x + y*y + z*z) * 0.05) * 5
                
                scalar_array.SetValue(k*size[0]*size[1] + j*size[0] + i, val)
    
    image_data.GetPointData().SetScalars(scalar_array)
    
    elapsed_time = time.time() - start_time
    print(f"✅ Created volume: {image_data.GetNumberOfPoints():,} points in {elapsed_time:.2f}s")
    
    if save_xdmf:
        # Extract data from VTK to NumPy arrays for XDMF
        points = image_data.GetPoints()
        num_points = points.GetNumberOfPoints()
        
        # Extract vertices
        vertices = np.zeros((num_points, 3), dtype=np.float64)
        for i in range(num_points):
            vertices[i] = points.GetPoint(i)
        
        # Extract scalar data
        vtk_scalars = image_data.GetPointData().GetScalars()
        scalars = np.array([vtk_scalars.GetValue(i) for i in range(num_points)], dtype=np.float64)
        
        # Create cell connectivity for structured grid
        # We'll create hexahedral cells
        nx, ny, nz = size
        connectivity = []
        
        # For large volumes, we'll create a reduced set of cells for XDMF
        # This is to keep file sizes manageable
        stride = max(1, min(nx, ny, nz) // 20)  # Adaptive stride based on size
        
        for k in range(0, nz-stride, stride):
            for j in range(0, ny-stride, stride):
                for i in range(0, nx-stride, stride):
                    # Get indices of the 8 corners of the hexahedron
                    idx000 = k*nx*ny + j*nx + i
                    idx100 = k*nx*ny + j*nx + (i+stride)
                    idx010 = k*nx*ny + (j+stride)*nx + i
                    idx110 = k*nx*ny + (j+stride)*nx + (i+stride)
                    
                    idx001 = (k+stride)*nx*ny + j*nx + i
                    idx101 = (k+stride)*nx*ny + j*nx + (i+stride)
                    idx011 = (k+stride)*nx*ny + (j+stride)*nx + i
                    idx111 = (k+stride)*nx*ny + (j+stride)*nx + (i+stride)
                    
                    # Ensure all indices are within bounds
                    if max(idx000, idx100, idx110, idx010, idx001, idx101, idx111, idx011) < len(scalars):
                        # Add hexahedron
                        connectivity.append([idx000, idx100, idx110, idx010, idx001, idx101, idx111, idx011])
        
        connectivity = np.array(connectivity, dtype=np.int32)
        
        # Create cell data (average of vertex values)
        cell_data = []
        for cell in connectivity:
            avg_value = np.mean([scalars[i] for i in cell])
            cell_data.append(avg_value)
        
        cell_data = np.array(cell_data, dtype=np.float64)
        
        # Save to XDMF
        write_xdmf_files("large_volume", vertices, connectivity, scalars, cell_data, 
                         "Density", "Average_Density")
        return None
    else:
        return image_data

def create_extra_large_volume_dataset(size=(150, 150, 150), save_xdmf=True):
    """Create an extra large 3D volume dataset for slicing demonstration
    
    Args:
        size: Tuple (nx, ny, nz) specifying dimensions
        save_xdmf: Whether to save as XDMF file
        
    Returns:
        VTK image data object or None if save_xdmf is True
    """
    print(f"🔄 Creating extra large volume dataset {size[0]}x{size[1]}x{size[2]}...")
    start_time = time.time()
    
    # Create structured volume using VTK
    image_data = vtk.vtkImageData()
    image_data.SetDimensions(*size)
    image_data.SetSpacing(1.0, 1.0, 1.0)
    image_data.SetOrigin(-size[0]//2, -size[1]//2, -size[2]//2)
    
    # Create complex scalar field
    scalar_array = vtk.vtkFloatArray()
    scalar_array.SetName("Temperature")
    scalar_array.SetNumberOfTuples(size[0] * size[1] * size[2])
    
    print("🔄 Generating scalar field...")
    for k in range(size[2]):
        for j in range(size[1]):
            for i in range(size[0]):
                x, y, z = i - size[0]//2, j - size[1]//2, k - size[2]//2
                
                # Complex function with multiple features - different from the regular volume
                r = np.sqrt(x*x + y*y + z*z)
                theta = np.arctan2(y, x)
                phi = np.arctan2(np.sqrt(x*x + y*y), z)
                
                # Create interesting patterns
                val = np.sin(r * 0.03) * np.cos(5 * theta) * np.sin(3 * phi)
                val += 0.5 * np.sin(x * 0.05) * np.sin(y * 0.05) * np.sin(z * 0.05)
                
                scalar_array.SetValue(k*size[0]*size[1] + j*size[0] + i, val)
    
    image_data.GetPointData().SetScalars(scalar_array)
    
    elapsed_time = time.time() - start_time
    print(f"✅ Created extra large volume: {image_data.GetNumberOfPoints():,} points in {elapsed_time:.2f}s")
    
    if save_xdmf:
        # Extract data from VTK to NumPy arrays for XDMF
        points = image_data.GetPoints()
        num_points = points.GetNumberOfPoints()
        
        # Extract vertices
        vertices = np.zeros((num_points, 3), dtype=np.float64)
        for i in range(num_points):
            vertices[i] = points.GetPoint(i)
        
        # Extract scalar data
        vtk_scalars = image_data.GetPointData().GetScalars()
        scalars = np.array([vtk_scalars.GetValue(i) for i in range(num_points)], dtype=np.float64)
        
        # Create cell connectivity for structured grid
        # We'll create hexahedral cells
        nx, ny, nz = size
        connectivity = []
        
        # For large volumes, we'll create a reduced set of cells for XDMF
        # This is to keep file sizes manageable
        stride = max(1, min(nx, ny, nz) // 20)  # Adaptive stride based on size
        
        for k in range(0, nz-stride, stride):
            for j in range(0, ny-stride, stride):
                for i in range(0, nx-stride, stride):
                    # Get indices of the 8 corners of the hexahedron
                    idx000 = k*nx*ny + j*nx + i
                    idx100 = k*nx*ny + j*nx + (i+stride)
                    idx010 = k*nx*ny + (j+stride)*nx + i
                    idx110 = k*nx*ny + (j+stride)*nx + (i+stride)
                    
                    idx001 = (k+stride)*nx*ny + j*nx + i
                    idx101 = (k+stride)*nx*ny + j*nx + (i+stride)
                    idx011 = (k+stride)*nx*ny + (j+stride)*nx + i
                    idx111 = (k+stride)*nx*ny + (j+stride)*nx + (i+stride)
                    
                    # Ensure all indices are within bounds
                    if max(idx000, idx100, idx110, idx010, idx001, idx101, idx111, idx011) < len(scalars):
                        # Add hexahedron
                        connectivity.append([idx000, idx100, idx110, idx010, idx001, idx101, idx111, idx011])
        
        connectivity = np.array(connectivity, dtype=np.int32)
        
        # Create cell data (average of vertex values)
        cell_data = []
        for cell in connectivity:
            avg_value = np.mean([scalars[i] for i in cell])
            cell_data.append(avg_value)
        
        cell_data = np.array(cell_data, dtype=np.float64)
        
        # Save to XDMF
        write_xdmf_files("extra_large_volume", vertices, connectivity, scalars, cell_data, 
                         "Temperature", "Average_Temperature")
        return None
    else:
        return image_data

def create_large_unstructured_dataset(num_points=50000, save_xdmf=True):
    """Create a large unstructured grid for slicing demonstration
    
    Args:
        num_points: Number of points to generate
        save_xdmf: Whether to save as XDMF file
        
    Returns:
        VTK unstructured grid object or None if save_xdmf is True
    """
    print(f"🔄 Creating large unstructured dataset with {num_points:,} points...")
    start_time = time.time()
    
    # Create unstructured grid using VTK
    points = vtk.vtkPoints()
    scalars = vtk.vtkFloatArray()
    scalars.SetName("Temperature")
    
    # Generate random points in 3D space
    np.random.seed(42)  # For reproducibility
    
    for i in range(num_points):
        x = np.random.uniform(-100, 100)
        y = np.random.uniform(-100, 100) 
        z = np.random.uniform(-100, 100)
        points.InsertNextPoint(x, y, z)
        
        # Complex scalar field
        temp = 100 * np.exp(-(x*x + y*y + z*z) / 10000) + np.random.normal(0, 5)
        scalars.InsertNextValue(temp)
    
    # Create unstructured grid
    grid = vtk.vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.GetPointData().SetScalars(scalars)
    
    elapsed_time = time.time() - start_time
    print(f"✅ Created unstructured grid: {grid.GetNumberOfPoints():,} points in {elapsed_time:.2f}s")
    
    if save_xdmf:
        # Extract data from VTK to NumPy arrays for XDMF
        num_points = points.GetNumberOfPoints()
        
        # Extract vertices
        vertices = np.zeros((num_points, 3), dtype=np.float64)
        for i in range(num_points):
            vertices[i] = points.GetPoint(i)
        
        # Extract scalar data
        vtk_scalars = grid.GetPointData().GetScalars()
        point_data = np.array([vtk_scalars.GetValue(i) for i in range(num_points)], dtype=np.float64)
        
        # For unstructured grid, we'll create a Delaunay triangulation for visualization
        delaunay = vtk.vtkDelaunay3D()
        delaunay.SetInputData(grid)
        delaunay.SetTolerance(0.01)  # Adjust tolerance for better triangulation
        delaunay.Update()
        
        # Extract the triangulation
        triangulated = delaunay.GetOutput()
        
        # Extract connectivity
        cells = triangulated.GetCells()
        cells.InitTraversal()
        
        connectivity = []
        id_list = vtk.vtkIdList()
        
        while cells.GetNextCell(id_list):
            if id_list.GetNumberOfIds() == 4:  # Tetrahedra
                connectivity.append([id_list.GetId(0), id_list.GetId(1), id_list.GetId(2), id_list.GetId(3)])
        
        connectivity = np.array(connectivity, dtype=np.int32)
        
        # Create cell data (average of vertex values)
        cell_data = []
        for cell in connectivity:
            avg_value = np.mean([point_data[i] for i in cell])
            cell_data.append(avg_value)
        
        cell_data = np.array(cell_data, dtype=np.float64)
        
        # Save to XDMF
        write_xdmf_files("large_unstructured", vertices, connectivity, point_data, cell_data, 
                         "Temperature", "Average_Temperature")
        return None
    else:
        return grid

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
    elif connectivity.shape[1] == 4:
        topology_type = "Tetrahedron" 
    elif connectivity.shape[1] == 8:
        topology_type = "Hexahedron"
    else:
        topology_type = "Mixed"
    
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
    print(f"   Vertices: {len(vertices):,}")
    print(f"   Cells: {len(connectivity):,}")
    print(f"   Point data range: {point_data.min():.2f} - {point_data.max():.2f}")
    print(f"   Cell data range: {cell_data.min():.2f} - {cell_data.max():.2f}")

def main():
    """Create example XDMF files with large datasets"""
    print("🏗️  Creating Large XDMF Datasets for VTK Dash App")
    print("=" * 50)
    
    # Create large volume dataset with 1M+ cells
    print("\n1. Creating very large volume dataset (1M+ cells) for slicing demonstration...")
    create_large_volume_dataset((100, 100, 100), save_xdmf=True)
    
    # Create extra large volume dataset with 3.4M+ cells
    print("\n2. Creating extra large volume dataset (3.4M+ cells) for slicing demonstration...")
    create_extra_large_volume_dataset((150, 150, 150), save_xdmf=True)
    
    # Create large unstructured dataset
    print("\n3. Creating large unstructured dataset for slicing demonstration...")
    create_large_unstructured_dataset(100000, save_xdmf=True)
    
    print("\n🎯 Large datasets created successfully!")
    print("\nFiles created:")
    for name in ["large_volume", "extra_large_volume", "large_unstructured"]:
        if os.path.exists(f"{name}.xdmf") and os.path.exists(f"{name}.h5"):
            print(f"  ✅ {name}.xdmf + {name}.h5")
        else:
            print(f"  ❌ {name} files missing")
    
    print("\n📝 Usage:")
    print("  Upload the .xdmf file to the VTK Dash app")
    print("  The corresponding .h5 file must be in the same directory")
    print("  For large datasets, enable slicing in the app")

if __name__ == "__main__":
    main() 