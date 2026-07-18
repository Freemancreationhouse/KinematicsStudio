import os
import tempfile

from engine.bim import Assembly, AssemblyMember, BIMInstance, BIMMaterial, MaterialAssignment, MaterialCategory
from engine.cad.application import CADApplication
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Material BIM")
category = workspace.bim_manager.add_material_category(MaterialCategory("Steel", "Steel materials", "#90a4ae"))
material = workspace.bim_manager.add_material(BIMMaterial("Structural Steel", category.id, "#78909c"))
mesh = MeshEntity(MeshData.box(0.3, 0.3, 4.0), name="Persisted Steel Column Mesh")
mesh.id = "persisted-steel-column-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Persisted Steel Column", entity=mesh)
workspace.bim_manager.add_instance(instance)
workspace.bim_manager.add_material_assignment(MaterialAssignment(instance.id, material.id, 1.0, "tonne"))
assembly = Assembly("Persisted Frame")
assembly.add_member(AssemblyMember(instance.id, "Column"))
workspace.bim_manager.add_assembly(assembly)
workspace.bim_manager.run_quantity_takeoff()
workspace.selection.select(instance)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_material_assembly_quantity.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_instance = project.instances[0]
    restored_material = project.materials[0]
    restored_assembly = project.assemblies[0]

    assert project.material_categories[0].name == "Steel"
    assert restored_material.name == "Structural Steel"
    assert restored_instance.entity is not None
    assert restored_instance.selected is True
    assert restored_workspace.bim_manager.material_for(restored_instance) is restored_material
    assert restored_workspace.bim_manager.assemblies_for(restored_instance) == [restored_assembly]
    assert project.quantity_items
    assert project.quantity_summary.by_material[restored_material.id] == 1.0

print("3d-bim-material-assembly-quantity-persistence-ok")
