from engine.bim import (
    Assembly,
    AssemblyMember,
    AssemblyMetadata,
    AssemblyType,
    BIMInstance,
    BIMMaterial,
    MaterialAssignment,
    MaterialCategory,
    MaterialLayer,
    MaterialLayerSet,
    MaterialMetadata,
    QuantityRule,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Material Assembly BIM")
material_category = workspace.bim_manager.add_material_category(MaterialCategory("Concrete", "Concrete materials", "#b0bec5"))
material = workspace.bim_manager.add_material(
    BIMMaterial(
        "Cast Concrete",
        material_category.id,
        "#9e9e9e",
        MaterialMetadata("Structural concrete", "Studio", "120", {"density": 2400}, {"finish": "matte"}, {"u": 0.3}, {"strength": "C30"}),
    )
)
layer_set = workspace.bim_manager.add_material_layer_set(
    MaterialLayerSet("Concrete Wall Layers", [MaterialLayer(material.id, 0.2, "Structure")])
)
assembly_type = workspace.bim_manager.add_assembly_type(AssemblyType("Wall Assembly Type", template=True))
mesh = MeshEntity(MeshData.box(2.0, 0.2, 3.0), name="Material Wall Mesh")
mesh.id = "material-wall-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Material Wall", entity=mesh)
workspace.bim_manager.add_instance(instance)
assignment = workspace.bim_manager.add_material_assignment(MaterialAssignment(instance.id, material.id, 6.0, "m3"))
assembly = Assembly("Wall Assembly", assembly_type.id, AssemblyMetadata("Reusable wall assembly"))
assembly.add_member(AssemblyMember(instance.id, "Wall Core"))
workspace.bim_manager.add_assembly(assembly)
workspace.bim_manager.add_quantity_rule(QuantityRule("Default Count", "Count"))
items = workspace.bim_manager.run_quantity_takeoff()

assert workspace.bim_manager.material_library.get_material("Cast Concrete") is material
assert workspace.bim_manager.material_library.statistics().materials == 1
assert layer_set.total_thickness == 0.2
assert instance.material_assignment_id == assignment.id
assert workspace.bim_manager.material_for(instance) is material
assert assembly.statistics.members == 1
assert workspace.bim_manager.assemblies_for(instance) == [assembly]
assert items
assert workspace.bim_manager.active_project.quantity_statistics.total_count >= 1.0
assert workspace.bim_manager.active_project.quantity_summary.by_material[material.id] == 6.0

print("3d-bim-material-assembly-quantity-manager-ok")
