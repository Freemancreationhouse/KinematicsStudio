# 001 — APPLICATION INTEGRATION

Status: IN PROGRESS

Sprint: Sprint 1

Priority: Critical

Owner: Freeman Creations House

---

# Objective

Transform Kinematics Studio from a collection of independent subsystems into one cohesive professional CAD application with a single runtime ownership model.

---

# Scope

This specification covers:

- Application Runtime
- Dependency Injection
- Workspace Lifecycle
- UI Integration
- Command Routing
- Selection Synchronization
- Property Synchronization
- Project Lifecycle
- Rendering Synchronization

No new CAD features are introduced during this sprint.

---

# Sprint Goal

When Sprint 1 is complete, the following workflow must work without errors:

Application Start

↓

Create Project

↓

Open Project

↓

Draw

↓

Select

↓

Modify

↓

Undo

↓

Redo

↓

Save

↓

Close

↓

Reopen

↓

Restore Complete State

---

# Architecture Rules

- One CADApplication
- One CADEngine
- One WorkspaceManager
- One Active Workspace
- One Active Scene
- One Selection Manager
- One Command Manager
- One Runtime State

UI widgets must never own business logic.

---

# Task Progress

## ✅ Task 1.1

Runtime Ownership Audit

Status:

COMPLETE

Summary:

- Audited runtime ownership.
- Identified ownership violations.
- Established integration roadmap.

---

## ✅ Task 1.2

Move CADApplication Ownership

Status:

COMPLETE

Summary:

- CADApplication moved from Canvas to MainWindow.
- Runtime dependency injection established.
- Shared runtime instance verified.

---

## ⏳ Task 1.3

Workspace Provider

Status:

COMPLETE

Objective:

Replace fixed Workspace references with a provider so every UI component always uses the active Workspace.

Summary:

- Replaced fixed UI Workspace references with runtime Workspace provider resolution.
- WorkspaceConnectionController now resolves the active Workspace and CommandManager dynamically.
- PropertyPanel now resolves the active Workspace through an attached provider.
- On-demand panels receive a provider instead of a concrete Workspace instance.

Files Modified:

- engine/services/workspace_provider.py
- ui_v2/main_window.py
- ui_v2/workspace_connection_controller.py
- ui_v2/property_panel.py
- ui_v2/panel_bootstrap.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- CADApplication remains the owner of the active runtime Workspace.
- UI components receive either CADApplication or WorkspaceProvider instead of a fixed Workspace.
- WorkspaceProvider delegates to app.workspace at access time so New, Open, Close and Recover project flows use the current active Workspace.
- Existing panel constructors remain compatible while no longer receiving a permanent Workspace instance.

Remaining Tasks:

- Task 1.5 â€” Command Routing Cleanup

---

## Task 1.4

Property Panel Routing

Status:

COMPLETE

Summary:

- PropertyPanel now emits edit requests instead of creating or executing commands.
- PropertyCommandService centralizes entity, layer, constraint and 3D transform command execution.
- WorkspaceConnectionController routes PropertyPanel edit requests to the application service layer.

Files Modified:

- engine/services/property_command_service.py
- ui_v2/property_panel.py
- ui_v2/workspace_connection_controller.py
- ui_v2/main_window.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- PropertyPanel remains a display and edit-request UI component only.
- Command construction and execution are centralized outside the UI.
- WorkspaceConnectionController is the routing boundary between UI edit requests and application services.

Remaining Tasks:

- Task 1.5 - Command Routing Cleanup
- Task 1.6 - Workspace Lifecycle

---

## Task 1.5

Ribbon Action Routing

Status:

COMPLETE

Summary:

- Ribbon now emits action identifiers instead of executing tools, commands, project operations or workspace logic.
- WorkspaceConnectionController now receives Ribbon actions and performs the routed application behavior.
- Existing project, import/export, view, panel, tool, AI and Machine/CAM ribbon actions are preserved through centralized routing.

Files Modified:

- ui_v2/ribbon.py
- ui_v2/workspace_connection_controller.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- Ribbon remains a presentation-only widget.
- Tool selections are emitted through toolSelected and routed by WorkspaceConnectionController.
- General ribbon commands are emitted through actionTriggered and routed by WorkspaceConnectionController.

Remaining Tasks:

- Task 1.6 - Workspace Lifecycle
- Task 1.7 - UI Synchronization

---

## Task 1.6

Project Lifecycle Management

Status:

COMPLETE

Summary:

- Project lifecycle operations are centralized through ProjectService.
- WorkspaceConnectionController routes New, Open, Save, Save As, Close, Recover and autosave requests through ProjectService.
- ProjectService now supports template project creation, recovery, autosave coordination and lifecycle callbacks for runtime synchronization.
- Legacy ProjectRibbon lifecycle actions now use ProjectService instead of calling CADApplication directly.

Files Modified:

- engine/services/project_service.py
- ui_v2/main_window.py
- ui_v2/workspace_connection_controller.py
- ui_v2/ribbon_project.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- CADApplication remains the owner of actual workspace creation, replacement and persistence mechanics.
- ProjectService is the single application-service facade for project lifecycle requests from UI controllers.
- UI components and controllers no longer call CADApplication lifecycle methods directly.
- Project lifecycle synchronization is exposed through UI-free service callbacks.

Remaining Tasks:

- Task 1.7 - UI Synchronization
- Task 1.8 - Selection Synchronization

---

## Task 1.7

UI Synchronization

Status:

COMPLETE

Summary:

- WorkspaceConnectionController now owns a centralized synchronize_ui(event_name) pipeline.
- UI refreshes are grouped into logical events including ProjectOpened, ProjectClosed, WorkspaceChanged, SelectionChanged, ActiveToolChanged, DocumentModified, PropertyChanged and PanelChanged.
- Project lifecycle, selection, tool, property and command-history handlers now route refreshes through synchronization events.
- Canvas and Viewport3D no longer refresh PropertyPanel directly.

Files Modified:

- ui_v2/workspace_connection_controller.py
- ui_v2/canvas.py
- ui_v2/viewport3d.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- WorkspaceConnectionController remains the single UI synchronization controller.
- UI refresh surfaces are selected by event type instead of scattered direct refresh calls.
- Viewport-local painting and coordinate feedback remain inside viewport widgets, while cross-widget synchronization is centralized.

Remaining Tasks:

- Task 1.8 - Selection Synchronization

---

## Task 1.8

Selection Synchronization

Status:

COMPLETE

Summary:

- SelectionManager now publishes selection changes through a UI-free on_change notification.
- SelectionService is provider-aware and acts as the centralized selection mutation/read API for active shell components.
- Canvas and Viewport3D route selection mutations through SelectionService.
- WorkspaceConnectionController observes the current SelectionManager through SelectionService and routes selection changes through synchronize_ui("SelectionChanged").

Files Modified:

- engine/workspace/selection_manager.py
- engine/services/selection_service.py
- ui_v2/main_window.py
- ui_v2/canvas.py
- ui_v2/viewport3d.py
- ui_v2/workspace_connection_controller.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- SelectionManager remains the single source of truth for selected entities.
- SelectionService is the centralized application-service interface for selection reads and mutations.
- UI widgets observe selection through WorkspaceConnectionController synchronization events instead of refreshing unrelated UI directly.
- Existing direct SelectionManager mutations from commands and legacy panels still synchronize because SelectionManager now emits one core change notification.

Remaining Tasks:

- Task 1.9 - Viewport Synchronization
- Task 1.10 - Sprint Validation

---


## Task 1.9

Viewport Synchronization

Status:

COMPLETE

Summary:

- Added a centralized ViewportSynchronizationService for synchronized 2D and 3D viewport refreshes.
- Canvas and Viewport3D continue to observe the same active CADApplication workspace instead of owning scenes.
- WorkspaceConnectionController now routes scene, entity, selection, camera and view changes through one viewport synchronization pipeline.
- View switching uses WorkspaceViewportArea without recreating geometry or runtime state.

Files Modified:

- ui_v2/viewport_synchronization_service.py
- ui_v2/main_window.py
- ui_v2/workspace_connection_controller.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- CADEngine remains the owner of the active Workspace and camera instances.
- Canvas and Viewport3D remain render-only viewport widgets that resolve model state through the shared CADApplication.
- ViewportSynchronizationService owns no scene, geometry, renderer or camera; it coordinates repaint requests for injected viewports.

Remaining Tasks:

- Task 1.10 - Sprint Validation

---

## Task 1.9A

Shared Scene Graph

Status:

COMPLETE

Summary:

- Implemented one shared workspace entity store for both 2D and 3D views.
- Scene3D now acts as a compatibility facade over Workspace.entities instead of owning a separate entity list.
- Canvas and Viewport3D render from the same active Workspace model through the existing CADApplication runtime.
- 3D renderer projects 2D entities onto the XY plane, and the 2D renderer draws 3D wire geometry in orthographic projection.
- DeleteCommand now removes and restores entities through the active Workspace when invoked from engine-backed 3D workflows.
- Project persistence filters shared entities so 2D and 3D entities are not duplicated in saved project data.

Files Modified:

- engine/scene3d.py
- engine/workspace/workspace.py
- engine/render/renderer.py
- engine/render/renderer3d.py
- engine/snap/snap_manager3d.py
- engine/entities/entity.py
- engine/entities/entity3d.py
- engine/storage/project.py
- engine/commands/delete_command.py
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md
- CHANGELOG.md

Architecture Decisions:

- Workspace.entities is the single authoritative entity store.
- Workspace.scene and Workspace.scene3d reference the same shared-scene facade for compatibility.
- Viewports and renderers remain read-only consumers of the active Workspace model.
- No entity copying, mirroring or duplicate scene ownership was introduced.

Remaining Tasks:

- Task 1.10 - Sprint Validation

---

## Bug Fix - 3D Primitive Ribbon Command Routing

Status: COMPLETE

Summary:

- Cube, Box, Sphere, Cone and related primitive ribbon buttons now execute the existing CreatePrimitiveCommand path.
- WorkspaceConnectionController remains the sole ribbon action routing location.
- Primitive creation now flows through CommandManager, Workspace.add_3d_entity, the shared scene, selection synchronization and UI refresh.
- Rendering, shared-scene ownership and viewport synchronization implementations were not changed.

Files Modified:

- ui_v2/workspace_connection_controller.py
- BUG_TRACKER.md
- CHANGELOG.md
- docs/40_FEATURE_SPECIFICATIONS/001_APPLICATION_INTEGRATION.md
- PROJECT_STATUS.md
- SPRINT_BACKLOG.md

Architecture Decisions:

- 3D primitive ribbon actions are command-producing actions, not passive Viewport3D placement tools.
- CreatePrimitiveCommand remains the single primitive entity creation path for ribbon-triggered primitive creation.
- WorkspaceConnectionController owns the routing from primitive tool IDs to command execution.

Remaining Tasks:

- Task 1.10 - Sprint Validation

---

## Pending Tasks

- Task 1.10 — Sprint Validation

---

# Files Modified

(To be updated after each completed task.)

---

# Architecture Decisions

(To be appended after each completed task.)

---

# Known Issues

(To be updated from BUG_TRACKER.md.)

---

# Validation Checklist

- [ ] Single CADApplication
- [ ] Single Runtime State
- [ ] Shared Workspace
- [ ] Shared Selection
- [ ] Shared Command Manager
- [ ] Shared Scene
- [ ] Shared Renderer
- [ ] Shared Property Updates
- [ ] Shared Status Updates
- [ ] Save / Load Verified

---

# Completion Criteria

Sprint 1 is complete only when all validation items are complete and the application behaves as a single integrated CAD system.
