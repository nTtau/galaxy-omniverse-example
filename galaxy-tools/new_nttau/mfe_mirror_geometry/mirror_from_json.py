import os
import argparse
from datetime import datetime
import cadquery as cq
from cq_utils import create_compound, export_step_from_list, save_bounding_box_to_csv
from files import load_json, save_json
import mirror_geometry as mg
import zipfile
# Parsing Arguments
parser = argparse.ArgumentParser(
    description="Create mirror geometry for configuration file.")
parser.add_argument('--input', type=str,
                    default='input/default.json', help='Path to input JSON file')
args = parser.parse_args()
settings = load_json(args.input)


# Initalise directories
output_directory = "out"
CUSTOMER_NAME = settings['customer_name']
current_date = datetime.now().strftime("%d-%m-%Y")
# final_path = os.path.join(base_dir, CUSTOMER_NAME, current_date)

# clear_directory(output_directory)


def zip_directory(directory_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=directory_path)
                zipf.write(file_path, arcname)




component_list = []


radial_build = settings['radial_build']
reactor_height = settings['reactor_height']


coil_R = settings['solenoid_coil_r']
heights = settings['solenoid_coil_z']
solenoid_dr = settings['solenoid_coil_dr']
solenoid_dz = settings['solenoid_coil_dz']

end_cell_radius = settings['end_cell_radius']
end_cell_height = settings['end_cell_height']

end_cell_coil_r = settings['end_cell_coil_r']
end_cell_coil_heights = settings['end_cell_coil_z']
end_cell_coil_dr = settings['end_cell_coil_dr']
end_cell_coil_dz = settings['end_cell_coil_dz']

expander_coil = settings['expander_coil']
component_names = settings['component_names']
# Novatron config

# Optional Parameters
nbi_cutter_height = settings.get('nbi_cutter_height', 0)
nbi_radius = settings.get('nbi_radius', None)
nbi_angle = settings.get('nbi_angle', 45)
output_directory = settings.get('output_directory', output_directory)

end_cell_shield = settings.get('end_cell_shield', False)

PF_coils = [mg.PfCoil(radius=coil_R, height=height, dz=dz, dr=dr)
            for coil_R, height, dz, dr in zip(coil_R, heights, solenoid_dz, solenoid_dr)]

end_cell = [mg.PfCoil(radius=end_cell_coil_r, height=height, dz=end_cell_coil_dz, dr=end_cell_coil_dr)
            for height in end_cell_coil_heights]

if expander_coil is not False:
    top_expander_coil = mg.PfCoil(
        radius=expander_coil[0], height=expander_coil[1], dz=expander_coil[2], dr=expander_coil[3])
    bottom_expander_coil = mg.PfCoil(
        radius=expander_coil[0], height=-expander_coil[1], dz=expander_coil[2], dr=expander_coil[3])
    PF_coils.append(top_expander_coil)
    PF_coils.append(bottom_expander_coil)

# PF_coils.extend(end_cell)

mg.export_pf_coils_to_csv(PF_coils)

radial_build_cad, height_to_ec = mg.generate_radial_build_layers(
    radial_build, reactor_height, end_cell_radius)
file_names = component_names
# Extract the plasma layer on it's own to combine with plasma and end cell
height_to_ec = reactor_height

coil_cad = mg.generate_coils(PF_coils)

end_cell_cad = mg.end_cell_cylinder(
    height_to_ec, end_cell_radius, end_cell_height)


if end_cell_shield is not False:
    ec_shield = mg.create_ec_shield(height_to_ec, end_cell_radius, end_cell_height,
                                    end_cell_shield)

height_to_expander = height_to_ec / 2 + (end_cell_height)
max_coil_R = max(coil_R)
expanders = mg.plasma_expander(
    height_to_expander, (max_coil_R), (max_coil_R), 1, end_cell_radius)

ec_shield = ec_shield.cut(expanders)

end_components = expanders.union(end_cell_cad)


component_list.extend(radial_build_cad)
component_list.append(end_components)
file_names.append("end_components")
component_list.append(ec_shield)
file_names.append("ec_shield")
if nbi_radius is not None:
    nbi_to_cut = mg.create_nbi_cutter(
        nbi_radius, nbi_cutter_height, 1, reactor_height, nbi_angle)
    if nbi_cutter_height > reactor_height/2:
        # Cut just the end cell bit (last part of array)
        component_list[-1] = component_list[-1].cut(nbi_to_cut)
    else:
        for i in range(len(component_list)):
            component_list[i] = component_list[i].cut(nbi_to_cut)

component_list.extend(coil_cad)


coil_compound = create_compound(coil_cad)
filepath = os.path.join(output_directory, "pf_coils.step")
cq.exporters.export(coil_compound, filepath)

radial_build_comp = create_compound(radial_build_cad)

save_bounding_box_to_csv(
    radial_build_comp, output_directory, "radial_build_bb.csv")
filepath = os.path.join(output_directory, "radial_build.step")
cq.exporters.export(radial_build_comp, filepath)


if len(file_names) < len(component_list):
    for i in range(len(component_list) - len(file_names)):
        file_names.append(f"component_{i}")
export_step_from_list(component_list, output_directory, file_names)

mirror_reactor = create_compound(component_list)
filepath = os.path.join(output_directory, "mirror_reactor.step")
cq.exporters.export(mirror_reactor, filepath)

run_date = datetime.now().strftime("%d-%m-%Y %H:%M")
settings['run_date'] = run_date
save_json(settings, output_directory, "settings.json")
print("saved to", output_directory)
zip_directory(output_directory, "mirror_output.zip")