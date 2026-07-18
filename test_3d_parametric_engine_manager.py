from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ParametricContext, ProductPart, SolidBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Parametric Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
document = manager.create_document("Parametric Product")
part = manager.add_part(ProductPart("Parametric Part", "Parametric Mesh"))
body = manager.add_body_item(SolidBody("Parametric Body", part.id, mesh.name))

engine = manager.parametric_manager.create_engine("Primary Parametric Engine")
context = ParametricContext(
    product_document_id=document.id,
    product_part_id=part.id,
    body_id=body.id,
    mesh_entity_id=mesh.name,
    reference_ids=[part.id, body.id],
)
parametric_document = manager.parametric_manager.create_document(
    "Parametric Definition",
    engine,
    context,
    [part, body],
)
parametric_workspace = manager.parametric_manager.create_workspace(
    "Design Parametric Workspace",
    engine,
    parametric_document,
)
session = manager.parametric_manager.create_session(
    "Live Placeholder Session",
    engine,
    parametric_document,
    context,
    [part, body],
)
session.dirty_state.dirty = True
session.dirty_state.dirty_object_ids.append(part.id)

stats = manager.parametric_manager.statistics()

assert engine.document_ids == [parametric_document.id]
assert engine.workspace_ids == [parametric_workspace.id]
assert engine.session_ids == [session.id]
assert parametric_document.session_ids == [session.id]
assert parametric_document.reference_ids[:2] == [part.id, body.id]
assert manager.parametric_manager.active_engine() == engine
assert manager.parametric_manager.active_document() == parametric_document
assert manager.parametric_manager.active_session() == session
assert stats.engines == 1
assert stats.documents == 1
assert stats.workspaces == 1
assert stats.sessions == 1
assert stats.references >= 4
assert stats.dirty == 1
assert len(manager.dependency_edges) >= 4
assert len(workspace.scene3d.entities()) == 1
assert session.evaluation_state.status == "Not Evaluated"

print("3d-parametric-engine-manager-ok")
