from cad_to_dagmc import CadToDagmc

my_model = CadToDagmc()
my_model.add_stp_file("Vacuum.step", material_tags=["mat_v"], scale_factor=0.1)
my_model.add_stp_file("First_Wall.step", material_tags=["mat_w"], scale_factor=0.1)
my_model.add_stp_file("Plasma.step", material_tags=["mat_p"], scale_factor=0.1)
my_model.add_stp_file("Blanket_I.step", material_tags=["mat_b"], scale_factor=0.1)

my_model.export_dagmc_h5m_file(max_mesh_size=18, min_mesh_size=0.9) 