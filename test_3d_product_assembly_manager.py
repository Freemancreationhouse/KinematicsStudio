from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import MateGroup, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(3.0, 3.0, 3.0), name="Assembly Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Assembly Product")
part = manager.add_part(ProductPart("Assembly Part", "Assembly Mesh"))

document = manager.assembly_manager.create_document("Root Assembly Document")
assembly = manager.assembly_manager.create_assembly(document, "Root Assembly")
subassembly = manager.assembly_manager.create_assembly(document, "Sub Assembly")
manager.assembly_manager.open_assembly(assembly)

part_component = manager.assembly_manager.insert_part(assembly, part, "Inserted Part")
sub_component = manager.assembly_manager.insert_subassembly(assembly, subassembly, "Inserted Subassembly")
instance_a = manager.assembly_manager.create_instance(assembly, part_component, "Instance A", Vector3(1.0, 0.0, 0.0))
instance_b = manager.assembly_manager.create_instance(assembly, part_component, "Instance B", Vector3(2.0, 0.0, 0.0))
occurrence = manager.assembly_manager.create_occurrence(assembly, sub_component, "Sub Occurrence", Vector3(0.0, 1.0, 0.0))

for mate_type in (
    "Coincident",
    "Concentric",
    "Distance",
    "Angle",
    "Parallel",
    "Perpendicular",
    "Tangent",
    "Lock",
    "Limit",
    "Gear",
    "Cam",
):
    manager.mate_manager.create_mate(assembly, mate_type, instance_a, instance_b, distance=2.0, angle=45.0)

mate_group = MateGroup("Primary Mates", assembly.id, [mate.id for mate in manager.mates])
manager.mate_manager.add_item(mate_group)

exploded = manager.exploded_view_manager.create_view(assembly, "Service Exploded View")
step_a = manager.exploded_view_manager.add_step(exploded, instance_a, Vector3(5.0, 0.0, 0.0))
step_b = manager.exploded_view_manager.add_step(exploded, occurrence, Vector3(0.0, 5.0, 0.0))

configuration = manager.configuration_manager.create_configuration(
    assembly,
    "Suppressed Variant",
    suppression_states={instance_b.id: True},
    visibility_states={instance_a.id: True},
)
manager.configuration_manager.set_active(configuration)

assembly_stats = manager.assembly_manager.statistics()
occurrence_stats = manager.occurrence_manager.statistics()
mate_stats = manager.mate_manager.statistics()
exploded_stats = manager.exploded_view_manager.statistics()
configuration_stats = manager.configuration_manager.statistics()

assert assembly_stats.documents == 1
assert assembly_stats.assemblies == 2
assert assembly_stats.active == 1
assert assembly_stats.components == 2
assert assembly_stats.instances == 3
assert occurrence_stats.components == 2
assert occurrence_stats.instances == 2
assert occurrence_stats.occurrences == 1
assert mate_stats.mates == 11
assert mate_stats.groups == 1
assert exploded_stats.views == 1
assert exploded_stats.steps == 2
assert configuration_stats.configurations == 1
assert configuration_stats.active == 1
assert part_component.product_part_id == part.id
assert sub_component.subassembly_id == subassembly.id
assert instance_a.component_id == part_component.id
assert occurrence.component_id == sub_component.id
assert step_a.instance_id == instance_a.id
assert step_b.instance_id == occurrence.id
assert len(manager.components_for_assembly(assembly)) == 2
assert len(manager.instances_for_assembly(assembly)) == 3
assert len(manager.mates_for_assembly(assembly)) == 11
assert len(manager.exploded_views_for_assembly(assembly)) == 1
assert len(manager.configurations_for_assembly(assembly)) == 1
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 17

print("3d-product-assembly-manager-ok")
