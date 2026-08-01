# 002 — PROFESSIONAL WORKSPACE UI

Status: LOCKED

Sprint: Sprint 2

Epic: 2.1

Priority: Critical

---

# Objective

Create a professional engineering workspace comparable to Rhino, Revit, Fusion 360 and 3ds Max.

The workspace must feel premium, fast, clean and distraction-free.

---

# Design Principles

- Function first
- Minimal visual noise
- Maximum workspace area
- Dockable interface
- Consistent spacing
- Dark engineering theme
- Professional typography
- Keyboard-first workflow

---

# Layout

Top

- Title Bar
- Quick Access Toolbar
- Ribbon
- Workspace Tabs

Center

- Viewport Area

Left

- Project Explorer
- Layers
- Blocks
- Assets

Right

- Properties
- AI Assistant
- Inspector

Bottom

- Command Line
- Status Bar

---

# Requirements

- Dockable panels
- Resizable panels
- Hide/Show panels
- Ribbon tabs
- Modern icons
- Responsive layout

---

# Acceptance

- Professional appearance
- Responsive resizing
- No overlapping UI
- Stable docking

---

## Task 2.1.1

Status: IN PROGRESS

Summary

Professional workspace shell redesign introduced a darker engineering visual
system, in-application title region, Quick Access Toolbar, professional ribbon
tabs, collapsed side dock rails, viewport title controls and preserved the
existing lazy panel and controller routing architecture.

Files Modified

ui_v2/ribbon.py
ui_v2/workspace_shell.py
ui_v2/main_window.py
docs/40_FEATURE_SPECIFICATIONS/002_WORKSPACE_UI.md
PROJECT_STATUS.md
SPRINT_BACKLOG.md
CHANGELOG.md

Architecture Decisions

Sprint 1 runtime architecture remains frozen. Workspace, Scene, Rendering,
Selection, Command System, ToolManager, WorkspaceProvider, ProjectService and
Shared Scene were not modified. Side dock access routes through existing
WorkspaceConnectionController panel actions so panels remain lazily created by
WorkspacePanelManager.

Remaining Tasks

Manual PySide6 launch validation and final Sprint 2 acceptance testing.

----------------------------------------

## Task 2.1.2

Status: IN PROGRESS

Summary

The ribbon system was redesigned as a compact, high-density engineering ribbon
following the locked Sprint 2 design language. The ribbon now includes
professional command groups, Home/Draw/Modify/View/Create/Analyze/Render/
Machine/AI/Settings tabs, a persistent Quick Access Toolbar, command search,
responsive compact behavior and context tabs for selected mesh and curve
entities.

Files Modified

ui_v2/ribbon.py
docs/40_FEATURE_SPECIFICATIONS/002_WORKSPACE_UI.md
PROJECT_STATUS.md
SPRINT_BACKLOG.md
CHANGELOG.md

Architecture Decisions

The ribbon remains a UI layer component and reuses existing actionTriggered
and toolSelected signals. Search activates existing routed commands and tools
without introducing a new command system. Sprint 1 runtime systems were not
modified.

Remaining Tasks

Manual PySide6 launch validation, visual spacing review and responsive ribbon
validation on target displays.

----------------------------------------

## Task 2.1.3

Status: IN PROGRESS

Summary

Professional viewport chrome was added around the existing injected viewport
area. The viewport now presents a compact engineering title bar, Perspective
and User View labels, orientation labels, navigation controls, view mode
selector, world origin, snap, grid, axis, units, camera target, selection mode
and coordinate indicators using the locked dark engineering design language.

Files Modified

ui_v2/workspace_shell.py
docs/40_FEATURE_SPECIFICATIONS/002_WORKSPACE_UI.md
PROJECT_STATUS.md
SPRINT_BACKLOG.md
CHANGELOG.md

Architecture Decisions

Sprint 1 runtime architecture remains frozen. Workspace, Scene, Rendering,
Selection, Commands, ToolManager, WorkspaceProvider, ProjectService and Shared
Scene were not modified. The viewport chrome is presentation-only and wraps the
existing WorkspaceViewportArea without changing renderer, camera, navigation or
selection behavior.

Remaining Tasks

Manual PySide6 launch validation, target-display visual review and final
viewport interaction acceptance testing.

----------------------------------------
