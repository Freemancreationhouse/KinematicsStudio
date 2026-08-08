# KINEMATICS STUDIO

# GEOMETRY EDITING SPECIFICATION

Status: ACTIVE

---

## Task 2.3.1

Status: IN PROGRESS

Framework Summary

Implemented the production Geometry Editing Framework foundation for future
CAD, BIM, CAM and AI editing workflows. The framework introduces domain-layer
services for geometry registration, validation, transactions, observer events,
topology metadata, editing sessions, feature metadata and feature history.
No concrete editing tools, geometry algorithms, mesh editing, topology
algorithms, rendering changes, viewport changes or UI redesigns were added.

Implemented Modules

- engine.geometry.GeometryKernel
- engine.geometry.GeometryFactory
- engine.geometry.GeometryContext
- engine.geometry.GeometryValidator
- engine.geometry.GeometryEvents
- engine.geometry.GeometryRegistry
- engine.geometry.GeometryTransaction
- engine.geometry.GeometryObserver
- engine.topology.TopologyManager
- engine.topology.Body
- engine.topology.Shell
- engine.topology.Face
- engine.topology.Loop
- engine.topology.Edge
- engine.topology.Vertex
- engine.topology.PersistentTopologyId
- engine.topology.TopologyEvents
- engine.editing.EditingManager
- engine.editing.EditingContext
- engine.editing.EditingSession
- engine.editing.EditingOperation
- engine.editing.EditingEvents
- engine.editing.EditingMode
- engine.features.Feature
- engine.features.FeatureManager
- engine.features.FeatureRegistry
- engine.features.FeatureMetadata
- engine.features.FeatureBuilder
- engine.history.HistoryManager
- engine.history.FeatureHistory
- engine.history.HistoryNode
- engine.history.HistoryEvents

Architecture Decisions

Geometry Editing extends the existing Workspace instead of replacing it.
Workspace now exposes passive geometry, topology, editing, feature and history
framework managers. Existing Shared Scene, Viewport System, Camera System,
Rendering Pipeline, ViewCube, Navigation Bar, View Synchronization, Selection
Manager, Command System, WorkspaceProvider and ProjectService behavior remains
unchanged.

The EditingManager does not mutate geometry directly. Future concrete editing
operations must produce undoable commands and execute through the existing
CommandManager. AI metadata is represented through FeatureMetadata and
GeometryContext design-intent references. AI cannot create meshes, edit
topology directly, bypass commands, bypass the GeometryKernel or bypass
FeatureHistory through this framework.

Remaining Tasks

Future tasks may implement Move, Rotate, Scale, Extrude, Fillet, Chamfer,
Booleans, Constraints, Direct Modeling, Feature Editing and Gizmo workflows on
top of this framework. Those tasks must continue to route permanent model
changes through the Command System and preserve Shared Scene ownership.

----------------------------------------
