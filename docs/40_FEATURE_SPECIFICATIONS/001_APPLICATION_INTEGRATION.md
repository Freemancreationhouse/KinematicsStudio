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

- Task 1.4 â€” Property Panel Routing
- Task 1.5 â€” Command Routing Cleanup

---

## Pending Tasks

- Task 1.4 — Property Panel Routing
- Task 1.5 — Command Routing Cleanup
- Task 1.6 — Workspace Lifecycle
- Task 1.7 — UI Synchronization
- Task 1.8 — Rendering Synchronization
- Task 1.9 — Project Lifecycle Verification
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
