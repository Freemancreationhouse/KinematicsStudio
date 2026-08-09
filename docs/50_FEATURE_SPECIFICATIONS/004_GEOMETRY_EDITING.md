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

## Task 2.3.2

Status: IN PROGRESS

Selection System

Implemented the Professional Selection System as an extension of the existing
SelectionManager and SelectionService. Selection remains UI-free, rendering
independent and non-mutating. Existing object selection behavior remains the
default.

Selection Modes

- Object
- Body
- Face
- Edge
- Vertex
- Loop
- Ring
- Shell
- Component
- Assembly

Selection Filters

- Bodies
- Faces
- Edges
- Vertices
- Sketches
- Construction Geometry
- Reference Geometry
- Assemblies
- Annotations
- Dimensions
- Constraints

Persistent Selection

Selections now record persistent target metadata using available topology,
feature, layer, material and entity identifiers. Persistent selections can be
resolved back against the active Workspace without duplicating geometry or
viewport data.

AI Integration

AI selection requests are routed through SelectionManager via SelectionService.
AI can request body, face, edge, vertex or feature-oriented selection contexts
without selecting rendered triangles or bypassing the shared selection system.

----------------------------------------------------

## Task 2.3.3

Status: IN PROGRESS

Transform Framework

Implemented the production Transform Framework as a passive engine package for
future Move, Rotate, Scale, Mirror, Align, Direct Modeling and AI editing
workflows. The framework defines transform sessions, contexts, operations,
transactions, targets, constraints, state, axes, planes, spaces and events
without applying geometry changes.

Architecture

The Transform Framework references existing Workspace services through
TransformContext. It resolves targets from the active SelectionManager, records
persistent target metadata, stores preview and transaction state, and requires
future concrete transform operations to return undoable commands executed by
the existing CommandManager. No viewport, renderer, UI, camera, shared scene,
geometry kernel or feature-history behavior was changed.

Responsibilities

- Represent World, Local, Parent and Custom transform spaces.
- Represent Reference Plane, Reference Axis, Pivot, Bounding Box, Selection
  Center, Object Origin, Feature Origin and Component Origin metadata.
- Track Incremental, Absolute and Preview transform state.
- Coordinate Commit, Cancel, Undo Transaction and Redo Transaction metadata
  through command-producing operations.
- Provide AI integration points for Move, Rotate, Scale, Mirror and Align
  requests without allowing AI to modify geometry directly.

Remaining Tasks

Future tasks may implement concrete Move, Rotate, Scale, Mirror, Align,
Professional Gizmo, Direct Modeling and feature editing tools on top of this
framework. Those implementations must continue to modify model data only
through commands, GeometryKernel validation and the existing Workspace source
of truth.

----------------------------------------

## Task 2.3.4

Status: IN PROGRESS

Professional Move Tool

Implemented the Professional Move Tool on top of the Transform Framework.
Move interaction now uses a MoveSession, MovePreview, MoveTransaction,
MoveOperation and undoable MoveCommand. Dragging updates a reversible preview,
release commits through CommandManager, Escape cancels preview state, and
Undo/Redo restore the moved selection through the existing command stack.

Capabilities

- Object, Body, Face, Edge, Vertex and Component move targets are represented
  through TransformTarget metadata.
- Selection center, object origin, feature origin, component origin, custom
  pivot, World, Local, Parent and Custom transform concepts are carried by
  TransformState and TransformContext.
- Mouse press, drag and release create preview and commit workflows.
- Numeric move input supports X, Y, Z, Delta X, Delta Y, Delta Z, Distance,
  Absolute Position and Relative Position preview updates before commit.
- AI integration can request move intent through MoveCommand without direct
  geometry mutation.

Architecture

The Move Tool remains a Tool-layer input collector. It never records a move by
mutating geometry directly. Preview state is temporary and restored before
MoveCommand executes. Committed moves go through CommandManager and record a
Transform.Move feature metadata entry through the existing FeatureManager and
FeatureHistory integration.

Remaining Work

Future tasks may add Rotate, Scale, Mirror, Align, Transform Gizmo, Direct
Modeling and feature-specific topology movement. Those tasks must preserve the
same Transform Framework and CommandManager execution path.

----------------------------------------------------

## Task 2.3.5

Status: IN PROGRESS

Professional Rotate Tool

Implemented the Professional Rotate Tool on top of the Transform Framework.
Rotate interaction now uses RotateSession, RotatePreview, RotateTransaction,
RotateOperation and undoable RotateCommand. Rotation preview remains temporary,
commits execute through CommandManager, Escape cancels preview state, and
Undo/Redo restore the rotated selection through the existing command stack.

Architecture

The Rotate Tool remains a Tool-layer input collector. It does not own geometry,
rendering, viewport state or command history. Preview state is restored before
RotateCommand executes. Committed rotations go through TransformTransaction and
record Transform.Rotate feature metadata through the existing FeatureManager
and FeatureHistory integration.

Capabilities

- Object, Body, Face, Edge, Vertex, Component, Assembly and Sketch rotate
  targets are represented through TransformTarget metadata.
- World, Local, Parent, Custom, Screen, Reference Edge, Reference Line,
  Reference Plane and Selection Normal concepts are carried through rotate
  context, axis metadata and TransformState.
- Mouse press, cursor preview, click confirmation and numeric angle input are
  supported through one RotateSession.
- Numeric input accepts degrees, radians, relative angle, absolute angle,
  clockwise and counter-clockwise values before commit.
- AI integration can request rotate intent through RotateCommand without direct
  geometry mutation.

Remaining Tasks

Future tasks may add Scale, Mirror, Align, Dynamic Input HUD, Transform Gizmo,
Direct Modeling and feature-specific topology rotation. Those tasks must
preserve the same Transform Framework and CommandManager execution path.

----------------------------------------------------

## Task 2.3.6

Status: IN PROGRESS

Professional Scale Tool

Implemented the Professional Scale Tool on top of the Transform Framework.
Scale interaction now uses ScaleSession, ScalePreview, ScaleTransaction,
ScaleOperation and undoable ScaleCommand. Scale preview remains temporary,
commits execute through CommandManager, Escape cancels preview state, and
Undo/Redo restore the scaled selection through the existing command stack.

Architecture

The Scale Tool remains a Tool-layer input collector. It does not own geometry,
rendering, viewport state or command history. Preview state is restored before
ScaleCommand executes. Committed scales go through TransformTransaction and
record Transform.Scale feature metadata through the existing FeatureManager
and FeatureHistory integration.

Capabilities

- Object, Body, Face, Edge, Vertex, Component, Assembly and Sketch scale
  targets are represented through TransformTarget metadata.
- Uniform scale, non-uniform scale, X, Y, Z, XY, XZ, YZ, origin, selection
  center, custom pivot and bounding-box-center concepts are carried through
  scale context, mode metadata and TransformState.
- Mouse press, pivot/reference selection, cursor preview, click confirmation
  and numeric scale input are supported through one ScaleSession.
- Numeric input accepts scale factor, percentage, absolute-size-style factors
  and relative scale values before commit.
- AI integration can request scale intent through ScaleCommand without direct
  geometry mutation.

Remaining Tasks

Future tasks may add Copy, Dynamic Input HUD, Transform Gizmo, Mirror, Align,
Direct Modeling and feature-specific topology scaling. Those tasks must
preserve the same Transform Framework and CommandManager execution path.

----------------------------------------

## Task 2.3.7

Status: IN PROGRESS

Professional Snapping Engine

Implemented the Professional CAD Snapping Engine as a reusable engine-layer
package for current and future editing tools. The engine resolves snap targets
from Workspace and Shared Scene state, exposes snap result and marker metadata,
supports sessions, filters, priority ordering, grid/origin targets and AI-safe
snap requests without modifying geometry, rendering, viewports or commands.

Architecture

The Snapping Engine is UI-free and non-mutating. SnappingManager owns snapping
settings, configurable priority, filters, cache, session state and events.
SnappingContext reads existing Workspace services without owning them.
SnappingResult and SnappingMarker provide tool and renderer-facing metadata
without redesigning the rendering pipeline.

Capabilities

- Endpoint, Midpoint, Center, Intersection, Nearest, Quadrant, Tangent,
  Perpendicular, Parallel, Grid, Origin, Construction, Reference, Body Center,
  Bounding Box Center and Selection Center target types are represented.
- Configurable snap priority is exposed through SnappingPriority and
  SnappingManager.set_priority().
- Geometry, Construction, Reference, Grid, Bodies, Faces, Edges, Vertices,
  Sketches, Dimensions and Annotations filters are represented through
  SnappingFilter.
- Single, Multi, Temporary Override, Persistent and Smart snapping modes are
  represented through SnappingSettings.
- AI integration can request endpoint, midpoint, face center, grid and origin
  snapping through SnappingManager without direct geometry edits.

Remaining Tasks

Future tasks may route individual editing tools to this engine, expose dynamic
input HUD overrides, add transform gizmo snapping, add constraint-aware snaps
and extend visual marker rendering. Those tasks must preserve Workspace,
Shared Scene, Command System and rendering ownership.

----------------------------------------------------

## Task 2.3.8

Status: IN PROGRESS

Professional Dynamic Input (HUD)

Implemented the Professional Dynamic Input foundation as a reusable engine-layer
package for current and future editing tools. The system provides one shared
numeric input manager, session lifecycle, cursor overlay presentation model,
field definitions, safe expression parsing, unit parsing and AI-safe request
metadata without modifying locked tool, snapping, viewport, rendering or command
architecture.

Architecture

DynamicInputManager is the authoritative entry point for sessions, expression
evaluation, unit conversion, field routing and AI integration requests.
DynamicInputSession owns the active HUD state for one tool interaction.
DynamicInputOverlay is a viewport-independent presentation model that UI
presenters can render beside the cursor without becoming geometry or command
owners. DynamicInputParser delegates safe arithmetic expressions and unit-aware
normalization to dedicated parsers.

Capabilities

- Tool-specific HUD fields are represented for ΔX, ΔY, ΔZ, Distance, Angle,
  Scale, Radius, Offset, Copies, Rows, Columns, Spacing, Coordinate Space,
  Snap Target and Units.
- Keyboard workflow supports field activation, Tab and Shift+Tab traversal,
  Enter commit, Escape cancel and arrow-key numeric nudging.
- Unit-aware input supports mm, cm, m, km, in, ft, deg and ° suffixes.
- Expression input supports arithmetic such as 1000/2, 25*4, 300+25,
  500-125 and (1000+250)/2 through a safe AST parser.
- Cursor overlay metadata supports multi-viewport routing, HiDPI scale
  factors, dark/light theme metadata and live field snapshots.
- AI integration can request dynamic input sessions, expression evaluation,
  numeric input and unit conversion through DynamicInputManager without direct
  geometry mutation.

Remaining Tasks

Future tasks may connect Move, Rotate, Scale, Copy, Offset, Extrude, Fillet,
Chamfer, Mirror, Pattern, Array and Transform Gizmo tools to this shared HUD.
Those integrations must preserve Workspace, Shared Scene, Snapping Engine,
Transform Framework, Command System and rendering ownership.

----------------------------------------------------
