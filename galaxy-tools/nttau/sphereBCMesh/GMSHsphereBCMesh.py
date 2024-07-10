import gmsh
import argparse
import json
import os

def create_geometry_and_mesh(sphere_data, geometry):
    gmsh.initialize()
    gmsh.model.add("sphere_model")

    step_file = "reactor.step"
    num_layers = sphere_data['num_layers']
    mesh_factor = sphere_data['mesh_factor']
    cut_in_half = geometry['cut_in_half']
    hollow_core = geometry['hollow_core']

    gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", mesh_factor)
    gmsh.option.setNumber("Mesh.Algorithm", 1)  # Delaunay
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # 3D algorithm

    # Import STEP file
    gmsh.model.occ.importShapes(step_file)

    # Synchronize necessary due to use of OpenCASCADE
    gmsh.model.occ.synchronize()

    # Creating physical groups
    # Creating physical groups
    if hollow_core == False:
        for i in range(1, num_layers+1):
            volume_tag = i
            physical_tag = 30 + i  # Unique physical tag
            gmsh.model.addPhysicalGroup(3, [volume_tag], tag=physical_tag)
            gmsh.model.setPhysicalName(3, physical_tag, f"sph_{i}_volume")  # Use the physical_tag here
    else:
        for i in range(1, num_layers+1):
            volume_tag = i
            physical_tag = 30 + i  # Unique physical tag
            gmsh.model.addPhysicalGroup(3, [volume_tag], tag=physical_tag)
            gmsh.model.setPhysicalName(3, physical_tag, f"sph_{i}_volume")  # Use the physical_tag here

        
    if cut_in_half == True:
        for i in range(1, num_layers+1):
            sphere_tag = (i * 2) - 1
            plane_tag = i * 2
            if i <= 2:
                gmsh.model.addPhysicalGroup(2, [sphere_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_sphere")
                gmsh.model.addPhysicalGroup(2, [plane_tag], tag=plane_tag)
                gmsh.model.setPhysicalName(2, plane_tag, f"sph_{i}_plane")
            else:
                adjusted_tag = 3 * (i - 1)
                gmsh.model.addPhysicalGroup(2, [adjusted_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_sphere")
                gmsh.model.addPhysicalGroup(2, [adjusted_tag + 1], tag=plane_tag)
                gmsh.model.setPhysicalName(2, plane_tag, f"sph_{i}_plane")
    else:
        for i in range(1, num_layers+1):
            sphere_tag = i
            adjusted_tag_outer = (i * 2) - 2
            adjusted_tag_inner = (i * 2) - 1
            if i==1:
                gmsh.model.addPhysicalGroup(2, [sphere_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_outer")
            elif i==2:
                gmsh.model.addPhysicalGroup(2, [sphere_tag], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_outer")
                gmsh.model.addPhysicalGroup(2, [adjusted_tag_inner], tag=sphere_tag + 10)
                gmsh.model.setPhysicalName(2, sphere_tag + 10, f"sph_{i}_inner")
            else:
                gmsh.model.addPhysicalGroup(2, [adjusted_tag_outer], tag=sphere_tag)
                gmsh.model.setPhysicalName(2, sphere_tag, f"sph_{i}_outer")
                gmsh.model.addPhysicalGroup(2, [adjusted_tag_inner], tag=sphere_tag + 10)
                gmsh.model.setPhysicalName(2, sphere_tag + 10, f"sph_{i}_inner")




    # Generate mesh
    gmsh.model.mesh.generate(3)

    # Save mesh (optional, uncomment to save)
    gmsh.write("meshed_model.msh")

    gmsh.finalize()

# Main script
parser = argparse.ArgumentParser()
parser.add_argument('file_path')
args = parser.parse_args()
file_path = args.file_path

with open(file_path, 'r') as file:
    data = json.load(file)

sphere_data = data['sphere_data']
geometry = data['geometry']
create_geometry_and_mesh(sphere_data, geometry)


os.rename("meshed_model.msh", "outputfile.msh")



