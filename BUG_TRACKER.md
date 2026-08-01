# KINEMATICS STUDIO

# BUG TRACKER

---

## BUG TEMPLATE

Bug ID:

Title:

Priority:

Critical / High / Medium / Low

Status:

Open

Assigned Sprint:

Module:

Description:

Steps to Reproduce:

Expected Behaviour:

Actual Behaviour:

Root Cause:

Fix:

Verification:

Closed In Version:

---

# ACTIVE BUGS

## BUG-001

Title:

Shared scene selection runtime error

Priority:

High

Status:

Fixed

Assigned Sprint:

Sprint 1

Module:

Shared Scene / UI Synchronization

Description:

Selecting a 3D object after the shared scene implementation could raise
TypeError: 'method' object is not iterable.

Steps to Reproduce:

Launch the application, create or load a 3D object, switch to the 3D viewport
and select the object.

Expected Behaviour:

The selected 3D object should update selection state, PropertyPanel and
StatusBar without an exception.

Actual Behaviour:

The UI synchronization path could pass a bound selection method into
selection display widgets. PropertyPanel attempted to iterate that method with
list(selected or []), causing TypeError: 'method' object is not iterable.

Root Cause:

Selection payload normalization did not defensively resolve callable selection
accessors before forwarding them to UI consumers after shared-scene selection
events.

Files Modified:

ui_v2/workspace_connection_controller.py
ui_v2/property_panel.py
ui_v2/status_bar.py
BUG_TRACKER.md
CHANGELOG.md

Fix:

Resolved callable selection payloads before they reach PropertyPanel and
StatusBar, and normalized the WorkspaceConnectionController fallback selection
path so a selected accessor method is called before being returned.

Verification:

Compiled the modified UI synchronization, PropertyPanel and StatusBar modules
successfully with the bundled Python runtime. Runtime GUI selection validation
requires the local PySide6 application environment.

Closed In Version:

0.1 Alpha

---

## BUG-006

Title:

Renderer3D analysis overlays passed Vector2 into Camera3D

Priority:

High

Status:

Fixed

Assigned Sprint:

Sprint 1

Module:

Renderer3D / Analysis Overlays

Description:

Renderer3D could crash while drawing analysis overlays when overlay data
contained 2D Vector2 points from shared-scene 2D entities.

Steps to Reproduce:

Enable analysis overlay display for shared-scene entities that include 2D
geometry, then render the 3D viewport.

Expected Behaviour:

2D overlay data should project into the 3D viewport as world-space points on
the XY plane.

Actual Behaviour:

Renderer3D._draw_analysis_overlays passed Vector2 points through _draw_line
to Camera3D.project, which expects Vector3-compatible points and accessed z.

Root Cause:

Analysis overlay rendering used raw entity point and segment data instead of
the renderer's 2D-to-3D projection adapters. Direct Camera3D.project callers
also did not normalize point dimensionality at the renderer boundary.

Files Modified:

engine/render/renderer3d.py
BUG_TRACKER.md
CHANGELOG.md

Fix:

Renderer3D now projects all points through a _project_point helper that
normalizes 2D and 3D point-like objects to Vector3, and analysis overlays use
the existing _entity_points3d and _entity_segments3d adapters before drawing.

Verification:

Compiled engine/render/renderer3d.py successfully with the bundled Python
runtime. Static trace confirms Camera3D.project is only called from
_project_point after Vector3 normalization.

Closed In Version:

0.1 Alpha

---

## BUG-005

Title:

Viewport cameras initialized away from active model

Priority:

High

Status:

Fixed

Assigned Sprint:

Sprint 1

Module:

Viewport Camera Synchronization / 3D Projection

Description:

The 3D viewport could open far away from the active model, switching between
2D and 3D did not preserve the active model center and CircleEntity projected
into 3D as a rectangular wire outline.

Steps to Reproduce:

Create or open a project, switch between 2D and 3D views, use primitive and
2D circle geometry, then invoke view fitting commands.

Expected Behaviour:

New blank projects should start centered at world origin. First 3D activation
should fit visible model extents. Switching views should preserve the active
camera target where possible. CircleEntity should project as a circular
wireframe in 3D.

Actual Behaviour:

View commands only targeted the 2D Canvas. The 3D camera was not fit on first
activation, and 2D circle projection in Renderer3D used only four quadrant
points, producing a rectangular outline.

Root Cause:

WorkspaceConnectionController did not route Home, Zoom Extents or Zoom
Selected across the active viewport, and Renderer3D used bounding fallback
points for CircleEntity projection rather than sampled circular wire points.

Files Modified:

ui_v2/workspace_connection_controller.py
ui_v2/canvas.py
ui_v2/ribbon.py
ui_v2/main_window.py
engine/render/renderer3d.py
BUG_TRACKER.md
CHANGELOG.md
PROJECT_STATUS.md

Fix:

Added centralized Home, Zoom Extents and Zoom Selected routing for active 2D
and 3D viewports; reset blank project cameras to world-origin home; preserved
camera target when switching between 2D and 3D; and changed Renderer3D circle
projection to sampled circular wire points without modifying CircleEntity
geometry.

Verification:

Compiled WorkspaceConnectionController, Canvas, Ribbon, MainWindow and
Renderer3D successfully with the bundled Python runtime. Static trace confirms
view actions route to camera home/extents/selection handlers and CircleEntity
projection now emits circular sample points.

Closed In Version:

0.1 Alpha

---

## BUG-004

Title:

2D renderer snap feedback crashed on MeshEntity

Priority:

High

Status:

Fixed

Assigned Sprint:

Sprint 1

Module:

2D Renderer / Snap Feedback

Description:

After switching from 3D back to 2D, snap feedback could crash when the snapped
entity was a MeshEntity.

Steps to Reproduce:

Create a 3D primitive, switch to 2D and move the cursor so snap feedback
references the MeshEntity.

Expected Behaviour:

2D snap feedback should preserve existing 2D highlighting and safely handle
3D entities through their projected representation.

Actual Behaviour:

Renderer.draw_snap_feedback called snap_result.entity.draw(painter) for every
snapped entity. MeshEntity is an Entity3D and does not implement draw(QPainter).

Root Cause:

The 2D renderer assumed every snap target was a 2D drawable entity. Shared
scene snapping can now return 3D MeshEntity targets.

Files Modified:

engine/render/renderer.py
BUG_TRACKER.md
CHANGELOG.md

Fix:

Renderer.draw_snap_feedback now preserves direct draw(QPainter) feedback for
2D entities and uses the existing projected 3D wireframe path for MeshEntity
and other 3D snap targets.

Verification:

Compiled engine/render/renderer.py successfully with the bundled Python
runtime. Static trace confirms MeshEntity snap feedback no longer calls a
missing draw(QPainter) method.

Closed In Version:

0.1 Alpha

---

## BUG-003

Title:

3D primitive ribbon actions did not create entities

Priority:

High

Status:

Fixed

Assigned Sprint:

Sprint 1

Module:

WorkspaceConnectionController / 3D Primitive Commands

Description:

The Cube, Box, Sphere and Cone ribbon buttons activated their tools but did
not create 3D geometry.

Steps to Reproduce:

Launch the application and click the Cube, Box, Sphere or Cone primitive
button from the 3D ribbon.

Expected Behaviour:

The ribbon action should execute the existing primitive command pipeline and
create a selected 3D entity in the shared Workspace scene.

Actual Behaviour:

The action stopped at ToolManager activation. Viewport3D does not route
primitive placement through ToolManager mouse events, so no command executed
and no entity was added to the Workspace.

Root Cause:

WorkspaceConnectionController treated 3D primitive ribbon actions as passive
tool selections only. The existing CreatePrimitiveCommand path was present
but never invoked by the ribbon action route.

Files Modified:

ui_v2/workspace_connection_controller.py
BUG_TRACKER.md
CHANGELOG.md
docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
PROJECT_STATUS.md
SPRINT_BACKLOG.md

Fix:

WorkspaceConnectionController now recognizes registered 3D primitive tool IDs
and executes CreatePrimitiveCommand through the active Workspace command
manager, then synchronizes entity, selection, status and property UI state.

Verification:

Compiled WorkspaceConnectionController, CreatePrimitiveCommand and primitive
tool modules successfully with the bundled Python runtime. Static trace
confirms ribbon primitive IDs now route to CreatePrimitiveCommand and
Workspace.add_3d_entity through the command manager.

Closed In Version:

0.1 Alpha

---

## BUG-002

Title:

SnapManager callable point accessor runtime error

Priority:

High

Status:

Fixed

Assigned Sprint:

Sprint 1

Module:

SnapManager

Description:

Moving the mouse while snapping against shared-scene entities could raise
TypeError: 'method' object is not iterable.

Steps to Reproduce:

Launch the application, create or load entities that expose points as a
method, enable snapping and move the mouse over the drawing area.

Expected Behaviour:

SnapManager should resolve snap candidates from both iterable point
collections and callable point accessors.

Actual Behaviour:

SnapManager passed entity.points directly into curve candidate helpers.
For entities where points is a method, _curve_candidates attempted to iterate
the method object.

Root Cause:

SnapManager assumed point-like entity attributes were always iterable. Shared
scene entities include 3D entities whose points are exposed through callable
methods.

Files Modified:

engine/snap/snap_manager.py
BUG_TRACKER.md
CHANGELOG.md

Fix:

Added local SnapManager point normalization so points and control_points are
called when callable, preserved when already iterable and converted into 2D
snap vertices before curve and intersection candidate generation.

Verification:

Compiled engine/snap/snap_manager.py successfully with the bundled Python
runtime. Static audit confirms SnapManager no longer passes entity.points or
entity.control_points directly into iterable curve helpers.

Closed In Version:

0.1 Alpha
