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
