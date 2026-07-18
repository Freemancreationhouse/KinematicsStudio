from engine.commands import (
    AddAssemblyComponentCommand,
    AddAssemblyConfigurationCommand,
    AddAssemblyMateCommand,
    AddAssemblyObjectCommand,
    AddExplodedViewCommand,
    AddProductPartCommand,
    CreateProductDocumentCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    Assembly,
    AssemblyComponent,
    AssemblyConfiguration,
    AssemblyDocument,
    AssemblyInstance,
    ExplodedStep,
    ExplodedView,
    Mate,
    MateDefinition,
    ProductPart,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Command Assembly Mesh")
workspace.add_3d_entity(mesh)

workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Assembly Product"))
part = ProductPart("Command Assembly Part", "Command Assembly Mesh")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

document = AssemblyDocument("Command Assembly Document")
workspace.command_manager.execute(AddAssemblyObjectCommand(workspace, document))
assembly = Assembly("Command Assembly", document.id)
workspace.command_manager.execute(AddAssemblyObjectCommand(workspace, assembly))
component = AssemblyComponent("Command Component", assembly.id, product_part_id=part.id)
workspace.command_manager.execute(AddAssemblyComponentCommand(workspace, component))
instance = AssemblyInstance("Command Instance", assembly.id, component.id)
workspace.command_manager.execute(AddAssemblyComponentCommand(workspace, instance))
mate = Mate("Command Mate", assembly.id, MateDefinition("Coincident", component.id, instance.id))
workspace.command_manager.execute(AddAssemblyMateCommand(workspace, mate))
exploded = ExplodedView("Command Exploded", assembly.id)
workspace.command_manager.execute(AddExplodedViewCommand(workspace, exploded))
step = ExplodedStep(exploded.id, instance.id)
workspace.command_manager.execute(AddExplodedViewCommand(workspace, step))
configuration = AssemblyConfiguration("Command Configuration", assembly.id)
workspace.command_manager.execute(AddAssemblyConfigurationCommand(workspace, configuration))

assert workspace.product_manager.assembly_documents == [document]
assert workspace.product_manager.assemblies == [assembly]
assert workspace.product_manager.assembly_components == [component]
assert workspace.product_manager.assembly_instances == [instance]
assert workspace.product_manager.mates == [mate]
assert workspace.product_manager.exploded_views == [exploded]
assert workspace.product_manager.exploded_steps == [step]
assert workspace.product_manager.assembly_configurations == [configuration]
assert assembly.component_ids == [component.id]
assert assembly.instance_ids == [instance.id]
assert assembly.mate_ids == [mate.id]
assert assembly.exploded_view_ids == [exploded.id]
assert assembly.configuration_ids == [configuration.id]

workspace.command_manager.undo()
assert workspace.product_manager.assembly_configurations == []
workspace.command_manager.undo()
assert workspace.product_manager.exploded_steps == []
workspace.command_manager.undo()
assert workspace.product_manager.exploded_views == []
workspace.command_manager.undo()
assert workspace.product_manager.mates == []
workspace.command_manager.undo()
assert workspace.product_manager.assembly_instances == []
workspace.command_manager.undo()
assert workspace.product_manager.assembly_components == []

print("3d-product-assembly-commands-ok")
