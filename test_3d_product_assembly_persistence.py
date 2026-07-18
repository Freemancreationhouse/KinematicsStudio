import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(4.0, 4.0, 4.0), name="Persisted Assembly Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Assembly Product")
part = manager.add_part(ProductPart("Persisted Assembly Part", "Persisted Assembly Mesh"))

document = manager.assembly_manager.create_document("Persisted Assembly Document")
assembly = manager.assembly_manager.create_assembly(document, "Persisted Assembly")
component = manager.assembly_manager.insert_part(assembly, part, "Persisted Component")
instance = manager.assembly_manager.create_instance(assembly, component, "Persisted Instance", Vector3(3.0, 0.0, 0.0))
occurrence = manager.assembly_manager.create_occurrence(assembly, component, "Persisted Occurrence", Vector3(0.0, 3.0, 0.0))
mate = manager.mate_manager.create_mate(assembly, "Distance", instance, occurrence, distance=3.0)
exploded = manager.exploded_view_manager.create_view(assembly, "Persisted Exploded")
manager.exploded_view_manager.add_step(exploded, instance, Vector3(6.0, 0.0, 0.0))
configuration = manager.configuration_manager.create_configuration(
    assembly,
    "Persisted Configuration",
    suppression_states={instance.id: False},
    visibility_states={occurrence.id: True},
)
manager.configuration_manager.set_active(configuration)
workspace.selection.select(mate)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "assembly_foundation.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.assembly_documents[0].name == "Persisted Assembly Document"
    assert restored.assemblies[0].name == "Persisted Assembly"
    assert restored.assembly_components[0].product_part_id == restored.parts[0].id
    assert restored.assembly_instances[0].type_name == "AssemblyInstance"
    assert restored.component_occurrences[0].type_name == "ComponentOccurrence"
    assert restored.mates[0].definition.mate_type == "Distance"
    assert restored.mates[0].definition.distance == 3.0
    assert restored.exploded_views[0].name == "Persisted Exploded"
    assert restored.exploded_steps[0].instance_id == restored.assembly_instances[0].id
    assert restored.assembly_configurations[0].active is True
    assert restored.assembly_statistics.assemblies == 1
    assert restored.occurrence_statistics.occurrences == 1
    assert restored.mate_statistics.mates == 1
    assert restored.exploded_statistics.steps == 1
    assert restored.configuration_statistics.active == 1
    assert restored.mates[0].selected is True

print("3d-product-assembly-persistence-ok")
