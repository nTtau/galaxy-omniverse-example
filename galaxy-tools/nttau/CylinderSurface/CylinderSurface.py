import gmsh
import os
import json
import argparse

# Parse arguments and load data from JSON
parser = argparse.ArgumentParser()
parser.add_argument('file_path')
args = parser.parse_args()
file_path = args.file_path

with open(file_path, 'r') as file:
    data = json.load(file)

cylinder_data = data['cylinder_data']
num_layers = cylinder_data['num_layers']
num_sides = cylinder_data['num_sides']
mesh_factor = cylinder_data['mesh_factor']

gmsh.initialize()
gmsh.model.add("model")

gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", mesh_factor)

step_files = ["plasma.step", "vacuum.step", "first_wall.step", "blanket_I.step", "5.step"]
for i, step_file in enumerate(step_files[:num_layers], start=1):
    gmsh.model.occ.importShapes(step_file)
gmsh.model.occ.synchronize()


for i in range(1, num_layers + 1):
    if i > 1:
        gmsh.model.occ.remove([(3, i)]) 
gmsh.model.occ.synchronize()

for i in range(2, num_layers + 1):
    for j in range(1, num_sides + 1):
        surface_tag = 2 * num_sides * (i - 1) + j
        gmsh.model.occ.remove([(2, surface_tag)]) 
gmsh.model.occ.synchronize()


for i in range(1, num_layers):
    loop_tag_1 = 2 * (num_layers - 1) + 2 * i
    loop_tag_2 = 2 * (num_layers - 1) + 2 * i + 1

    if i == 1:
        surface_outer_tags = [2 * num_sides - n for n in range(num_sides)]
        surface_inner_tags = [num_sides - n for n in range(num_sides)]
    else:
        surface_outer_tags = [2 * num_sides * i - n for n in range(num_sides)]
        surface_inner_tags = [2 * num_sides * (i - 1) - n for n in range(num_sides)]

    print(surface_outer_tags)
    print(surface_inner_tags)

    x = gmsh.model.geo.addSurfaceLoop(surface_outer_tags, tag=loop_tag_1)
    y = gmsh.model.geo.addSurfaceLoop(surface_inner_tags, tag=loop_tag_2)

    gmsh.model.occ.synchronize()

    print(f"Creating volume with surface loops: {loop_tag_1}, {loop_tag_2}")

    volumeTag = gmsh.model.geo.addVolume([x, y], tag=i+1)
    gmsh.model.geo.synchronize()
    gmsh.model.occ.synchronize()
    print(f"Volume created with tag: {i+1}")
    

    gmsh.model.occ.synchronize()

volumes = gmsh.model.getEntities(3)

# Print information about each volume
for volume in volumes:
    dim, tag = volume
    print(f"Volume with tag {tag}")
    

for i in range(1, num_layers + 1):
    top_surface_id = ((num_layers - 1) * 2 * num_sides) + (i * num_sides) + 1
    wall_surface_id = ((num_layers - 1) * 2 * num_sides) + (i * num_sides) + 2
    bottom_surface_id = ((num_layers - 1) * 2 * num_sides) + (i * num_sides) + 3
    
    if i==1:

        gmsh.model.addPhysicalGroup(2, [num_sides-1], tag=top_surface_id)
        gmsh.model.setPhysicalName(2, top_surface_id, f"cyl_{i}_top")
        
        gmsh.model.addPhysicalGroup(2, [num_sides-2], tag=wall_surface_id)
        gmsh.model.setPhysicalName(2, wall_surface_id, f"cyl_{i}_wall")
        
        gmsh.model.addPhysicalGroup(2, [num_sides], tag=bottom_surface_id)
        gmsh.model.setPhysicalName(2, bottom_surface_id, f"cyl_{i}_bottom")

        gmsh.model.occ.synchronize()

    if i>1:
        
        gmsh.model.addPhysicalGroup(2, [2*num_sides*(i-1)-1], tag=top_surface_id)
        gmsh.model.setPhysicalName(2, top_surface_id, f"cyl_{i}_top")
        
        gmsh.model.addPhysicalGroup(2, [2*num_sides*(i-1)-2], tag=wall_surface_id)
        gmsh.model.setPhysicalName(2, wall_surface_id, f"cyl_{i}_wall")
        
        gmsh.model.addPhysicalGroup(2, [2*num_sides*(i-1)], tag=bottom_surface_id)
        gmsh.model.setPhysicalName(2, bottom_surface_id, f"cyl_{i}_bottom")


gmsh.model.occ.synchronize()

for i in range(1, num_layers + 1):
    gmsh.model.addPhysicalGroup(3, [i], tag=i)
    gmsh.model.setPhysicalName(3, i, f"cyl_{i}_volume")

gmsh.model.occ.synchronize()

gmsh.model.mesh.generate(3)

gmsh.option.setNumber("Mesh.MshFileVersion",2.2)

gmsh.write("AutoSurfaceGMSH.msh")
