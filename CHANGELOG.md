# KINEMATICS STUDIO

# CHANGELOG

All notable changes to this project are documented here.

---

# Version 0.1 Alpha

## Added

-

## Changed

- CADApplication ownership moved from Canvas to MainWindow.
- Runtime dependency injection introduced for CADApplication.
- Replaced fixed Workspace references with runtime Workspace provider.
- UI components now resolve the active Workspace dynamically.
- PropertyPanel no longer executes commands directly.
- Command execution centralized through application service/controller.
- Ribbon converted to presentation-only UI.
- Ribbon actions centralized through WorkspaceConnectionController.
- Project lifecycle centralized through application service.
- All project actions now routed through a single controller.
- Centralized UI synchronization pipeline.
- UI refreshes routed through synchronization service/events.
- Centralized Selection synchronization.
- All UI components observe one SelectionManager.
- Centralized viewport synchronization.
- 2D and 3D now observe one shared Scene.
- View switching no longer recreates runtime state.
- Replaced split 2D/3D entity storage with one shared Workspace scene graph.
- 2D entities now render in the 3D viewport through XY projection.
- 3D entities now render in 2D orthographic views through wire projection.
- 3D snapping now reads shared-scene entities without requiring duplicate 3D storage.

## Improved

-

## Fixed

- Fixed shared scene selection runtime error ('method' object is not iterable).
- Resolved SnapManager callable/iterable mismatch.

## Removed

-

---

Release Date:

Build:
