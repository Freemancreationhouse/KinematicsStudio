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
