import os
import tempfile

from engine.bim import BIMInstance, BIMRelationship, Connection, CutRelationship, HostObject, HostedObject, Opening
from engine.cad.application import CADApplication


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Batch G BIM")
wall = workspace.bim_manager.add_instance(BIMInstance("Persisted Wall"))
window = workspace.bim_manager.add_instance(BIMInstance("Persisted Window"))
column = workspace.bim_manager.add_instance(BIMInstance("Persisted Column"))
workspace.bim_manager.add_relationship_item(BIMRelationship(wall.id, window.id, "Host"))
workspace.bim_manager.add_relationship_item(HostObject(wall.id, [window.id]))
workspace.bim_manager.add_relationship_item(HostedObject(window.id, wall.id))
opening = workspace.bim_manager.add_relationship_item(Opening("Persisted Opening", wall.id, "", window.id))
workspace.bim_manager.add_relationship_item(CutRelationship(wall.id, opening.id, window.id))
workspace.bim_manager.add_connection_item(Connection(wall.id, column.id, "Column"))
workspace.selection.select(wall)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_batch_g.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_wall = project.instances[0]
    restored_window = project.instances[1]
    restored_column = project.instances[2]

    assert project.relationships[0].relationship_type == "Host"
    assert restored_workspace.bim_manager.hosted_objects_for(restored_wall) == [restored_window]
    assert restored_workspace.bim_manager.host_for(restored_window) is restored_wall
    assert restored_workspace.bim_manager.openings_for(restored_wall)[0].name == "Persisted Opening"
    assert restored_workspace.bim_manager.cut_relationships_for(restored_wall)[0].cutter_id == restored_window.id
    assert restored_workspace.bim_manager.connected_items(restored_wall) == [restored_column]
    assert restored_wall.selected is True

print("3d-bim-relationship-connectivity-persistence-ok")
