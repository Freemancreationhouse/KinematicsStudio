from engine.geometry import Vector3
from engine.product import GlobalParameter, ProductPart, SketchLine, SketchPlane, SketchProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Feature Framework Product", "mm", 3)
part = manager.add_part(ProductPart("Feature Framework Part", "feature-framework-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Feature Framework Plane"))
sketch = manager.sketch_manager.create_sketch("Feature Framework Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Feature Framework Line", sketch.id, Vector3(), Vector3(12.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Feature Framework Profile", sketch.id, [line.id]))
parameter = manager.parameter_manager.add_item(GlobalParameter("feature_depth", 12.0))

parametric_engine = manager.parametric_manager.create_engine("Feature Framework Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Feature Framework Execution Engine", parametric_engine)
live_solver = manager.parametric_manager.create_solver("Feature Framework Live Solver", parametric_engine)
sketch_solver = manager.parametric_manager.create_sketch_solver(
    "Feature Framework Sketch Solver",
    parametric_engine,
    execution_engine,
    live_solver,
)
dependency_graph = manager.dependency_manager.create_graph("Feature Framework Dependency Graph")

extrude = manager.feature_manager.create_feature("Extrude", part, profile, None, name="Metadata Extrude")
shell = manager.feature_manager.create_feature("Shell", part, profile, None, name="Metadata Shell")
manager.dependency_manager.add_edge(parameter, extrude, "ParameterToFeature", graph=dependency_graph)
manager.dependency_manager.add_edge(extrude, shell, "FeatureOrder", graph=dependency_graph)

session = manager.feature_manager.create_execution_session(
    extrude,
    parametric_engine,
    execution_engine,
    live_solver,
    sketch_solver,
    dependency_graph,
)
manager.feature_manager.execute_timeline_metadata(part, session)
rollback_history = manager.feature_manager.rollback_to(extrude)
manager.feature_manager.suppress(shell, True)

assert session is not None
assert session.metadata.execution_engine_id == execution_engine.id
assert session.context.live_solver_id == live_solver.id
assert extrude.execution_state.execution_status == "Completed"
assert extrude.result.status == "Execution Metadata Ready"
assert extrude.result.updated is False
assert shell.feature_type == "Shell"
assert shell.suppressed is True
assert shell.execution_state.suppressed is True
assert rollback_history.rollback_index == 0
assert shell.execution_state.rolled_back is True
assert manager.feature_manager.ordering_for(part).rollback_feature_id == extrude.id
assert manager.feature_manager.cache_for(extrude).values["geometry"] == "deferred"
assert len(manager.feature_execution_sessions) == 1
assert manager.feature_statistics.execution_sessions == 1
assert len(workspace.scene3d.entities()) == 0
assert len(manager.bodies) == 0
assert part.mesh_entity_id == "feature-framework-mesh"

print("3d-parametric-feature-framework-manager-ok")
