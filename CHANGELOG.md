# KINEMATICS STUDIO

# CHANGELOG

All notable changes to this project are documented here.

---

# Version 0.4 Alpha

## Added

- Geometry Editing Framework
- Geometry Kernel Framework
- Topology Framework
- Feature Framework
- History Framework
- AI CAD Framework
- Professional Selection System
- Selection Filters
- Selection Context
- Persistent Selection
- AI Selection Integration
- Transform Framework
- Transform Manager
- Transform Sessions
- Transform Transactions
- Transform Context
- Professional Move Tool
- Move Command
- Move Preview
- Move Transactions

## Changed

- Architecture Cleanup
- Package Refactor
- No functional changes.
- Professional Move Tool package refactor
- Architecture cleanup
- No functional changes

## Improved

-

## Fixed

-

## Removed

-

---

# Version 0.3 Alpha

## Added

- Viewport Manager
- Viewport Registry
- Viewport Events
- Viewport Framework
- Viewport Layout Manager
- Quad View
- Dual View
- Triple View
- Viewport Maximization
- Layout Persistence
- Independent Camera System
- Perspective Navigation
- Orthographic Navigation
- Zoom Extents
- Zoom Selected
- Home View
- Camera Persistence
- Professional ViewCube
- Compass
- Animated Camera Orientation
- Professional Navigation Bar
- Projection Toggle
- Grid Toggle
- Axes Toggle
- Origin Toggle
- Viewport Synchronization
- Dirty Refresh
- Workspace-wide View Updates
- Dirty Region Rendering
- Viewport Caching
- Frustum Culling
- Viewport Statistics
- Viewport Presets
- Workspace Profiles
- Preset Persistence

## Changed

-

## Improved

-

## Fixed

- Fixed Viewport Layout Manager widget lifetime handling so reusable viewport widgets are not deleted during layout changes.
- Fixed Quad View camera assignment so Perspective, Top, Front and Right viewports use independent cameras.
- Fixed Viewport Layout Manager Maximize, Restore, Split, Close, Reopen and Swap routing.
- Fixed stale viewport synchronization references after viewport destruction or invalid Qt wrapper detection.
- Fixed ViewportManager signal emission after QObject destruction during viewport layout shutdown.
- Fixed orthographic Front and Right viewport selection by routing auxiliary viewport clicks through camera rays and PickingManager3D.

## Removed

-

---

# Version 0.2 Alpha

## Added

- Professional Workspace UI
- Modern engineering layout
- Responsive docking
- Professional ribbon
- Professional Ribbon
- Context Tabs
- Ribbon Search
- Quick Access Toolbar
- Responsive Ribbon
- Professional viewport chrome
- Viewport overlays
- Navigation toolbar
- Viewport status indicators
- Application-wide Design System
- Reusable UI Styling
- Professional Component Library
- Consistent Engineering Theme
- Professional Docking System
- Workspace Presets
- Persistent Layouts
- Floating Panels
- Auto-hide Panels

## Changed

-

## Improved

-

## Fixed

-

## Removed

-

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
- Active CAD tool state now returns to Select after cancellation and single-shot command completion.

## Improved

-

## Fixed

- Fixed shared scene selection runtime error ('method' object is not iterable).
- Resolved SnapManager callable/iterable mismatch.
- Fixed 3D primitive ribbon actions not executing CreatePrimitiveCommand.
- Fixed 2D snap feedback crash when snapping to MeshEntity.
- Fixed viewport camera initialization, view fitting and CircleEntity 3D projection.
- Fixed Renderer3D analysis overlays passing Vector2 points into Camera3D projection.
- Fixed drawing tools remaining active after completion or Escape cancellation.

## Removed

-

---

Release Date:

Build:
