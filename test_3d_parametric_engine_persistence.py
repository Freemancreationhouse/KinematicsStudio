import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ParametricContext, ProductPart, SolidBody


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(3.0, 2.0, 1.0), name="Persisted Parametric Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
product_document = manager.create_document("Persisted Parametric Product")
part = manager.add_part(ProductPart("Persisted Parametric Part", "Persisted Parametric Mesh"))
body = manager.add_body_item(SolidBody("Persisted Parametric Body", part.id, mesh.name))
engine = manager.parametric_manager.create_engine("Persisted Parametric Engine")
context = ParametricContext(
    product_document_id=product_document.id,
    product_part_id=part.id,
    body_id=body.id,
    mesh_entity_id=mesh.name,
    reference_ids=[part.id, body.id],
)
parametric_document = manager.parametric_manager.create_document(
    "Persisted Parametric Document",
    engine,
    context,
    [part, body],
)
parametric_workspace = manager.parametric_manager.create_workspace(
    "Persisted Parametric Workspace",
    engine,
    parametric_document,
)
session = manager.parametric_manager.create_session(
    "Persisted Parametric Session",
    engine,
    parametric_document,
    context,
    [part],
)
session.freeze_state.frozen = True
workspace.selection.select(session)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "parametric_engine.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.parametric_engines[0].name == "Persisted Parametric Engine"
    assert restored.parametric_documents[0].name == "Persisted Parametric Document"
    assert restored.parametric_documents[0].context.product_part_id == restored.parts[0].id
    assert restored.parametric_workspaces[0].document_id == restored.parametric_documents[0].id
    assert restored.parametric_sessions[0].name == "Persisted Parametric Session"
    assert restored.parametric_sessions[0].freeze_state.frozen is True
    assert restored.parametric_sessions[0].selected is True
    assert restored.parametric_statistics.sessions == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-engine-persistence-ok")
