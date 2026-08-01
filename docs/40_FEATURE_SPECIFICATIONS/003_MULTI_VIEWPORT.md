# 003 — MULTI VIEWPORT SYSTEM

Version: 1.0

Status: LOCKED

Sprint: 2

Epic: 2.2

Priority: CRITICAL

---

# PURPOSE

This document defines the complete Multi Viewport System for Kinematics Studio.

The viewport system is the primary interaction environment of the software.

Every modeling, drafting, editing, visualization and AI workflow operates through one or more synchronized viewports.

This specification defines viewport behavior, synchronization, layout management, interaction and future expansion.

---

# DESIGN GOALS

The viewport system must be:

Professional

Fast

Predictable

Scalable

Non-destructive

GPU efficient

Suitable for architecture, engineering and product design.

---

# PHILOSOPHY

A Viewport is NOT a Scene.

A Viewport is a Camera observing the Shared Scene.

There is always ONE Workspace.

There is always ONE Shared Scene.

Every viewport observes the same data.

Every viewport owns its own camera.

---

# ARCHITECTURE

Workspace

↓

Shared Scene

↓

Viewport Manager

↓

Viewport

↓

Camera

↓

Renderer

No viewport owns geometry.

No viewport duplicates geometry.

---

# SUPPORTED LAYOUTS

Single

Dual Horizontal

Dual Vertical

Triple

Quad

Custom

Floating Viewport

Fullscreen Viewport

---

# DEFAULT LAYOUT

Perspective

Top

Front

Right

Exactly four synchronized viewports.

---

# VIEW TYPES

Perspective

Top

Bottom

Front

Back

Left

Right

Isometric

Camera

Section

User View

Custom View

---

# CAMERA TYPES

Perspective

Orthographic

Parallel

Custom Projection

---

# CAMERA FEATURES

Independent cameras

Camera target

Camera pivot

Camera bookmarks

Named views

Camera animation

Camera reset

Home View

Zoom Extents

Zoom Selected

Previous View

Next View

---

# VIEW MODES

Wireframe

Hidden Line

Shaded

Rendered

Technical

X-Ray

Clay

Analysis

Presentation

Each viewport may use a different rendering mode.

---

# VIEWPORT TOOLBAR

Each viewport shall provide:

View Name

Projection

Render Mode

Grid Toggle

Axes Toggle

Origin Toggle

Section Toggle

Camera Menu

Viewport Menu

Fullscreen

Maximize

Restore

Screenshot

---

# VIEWCUBE

Support:

Top

Bottom

Front

Back

Left

Right

Corners

Edges

Animated transitions

Compass

---

# NAVIGATION BAR

Home

Fit

Zoom Extents

Zoom Selected

Orbit

Pan

Walk

Fly

Camera Settings

Projection

Bookmarks

---

# GRID SYSTEM

Infinite Grid

Major Grid

Minor Grid

Adaptive Grid

Grid Spacing

Grid Units

Grid Visibility

Snap Grid

Origin Marker

Axis Indicator

---

# WORLD ORIGIN

Every viewport shall display:

World Origin

World Axes

Orientation Indicator

Coordinate Display

---

# SYNCHRONIZATION

Shared:

Scene

Selection

Undo

Redo

Visibility

Layers

Commands

Properties

AI Context

Independent:

Camera

Projection

Render Mode

Grid

Viewport overlays

---

# USER INTERACTION

Click

Hover

Drag

Resize

Split

Merge

Swap

Duplicate

Close

Detach

Float

Fullscreen

---

# MULTI MONITOR

Support moving viewports to additional monitors.

Future implementation.

---

# PERFORMANCE

Independent redraw

GPU optimized

Frustum culling

Level of Detail

Dirty region updates

Viewport caching

Lazy refresh

Large scene support

---

# VIEWPORT MANAGER

Responsible for:

Viewport creation

Viewport destruction

Viewport synchronization

Layout management

Camera registry

Viewport registry

No geometry ownership.

---

# PERSISTENCE

Save:

Viewport layout

Camera positions

Projection modes

Render modes

Grid settings

Named views

Restore automatically when reopening projects.

---

# VIEWPORT STATES

Active

Inactive

Focused

Maximized

Fullscreen

Floating

Hidden

Docked

---

# VIEWPORT OVERLAYS

Grid

Axes

Selection

Dimensions

Constraints

Snap Preview

Measurement

Camera Target

Origin

Section Plane

Analysis

---

# SHORTCUTS

Space

Maximize active viewport

Ctrl + Space

Restore layout

F

Zoom Selected

H

Home View

G

Toggle Grid

A

Toggle Axes

---

# AI INTEGRATION

Future

AI can:

Create viewport layouts

Switch cameras

Navigate automatically

Create presentation layouts

Analyze visibility

Suggest viewpoints

---

# FUTURE FEATURES

Stereo View

VR

AR

Cloud Rendering

Collaborative Viewports

Presentation Mode

Animation Timeline

Viewport Recording

---

# ENGINEERING RULES

A viewport never owns entities.

A viewport never owns commands.

A viewport never owns the scene.

All viewports observe the same Workspace.

---

# ACCEPTANCE CRITERIA

✓ One Shared Scene

✓ Independent Cameras

✓ Shared Selection

✓ Shared Commands

✓ Shared Undo

✓ Shared Redo

✓ Professional Layout Switching

✓ Stable Performance

✓ Layout Persistence

✓ Camera Persistence

✓ GPU Efficient

---

# OUT OF SCOPE

BIM

AI Navigation

Rendering Engine Rewrite

Animation

VR

CAM

These belong to later epics.

---

# DEFINITION OF DONE

The Multi Viewport System is complete only when:

All supported layouts work.

Camera synchronization behaves correctly.

Shared Scene remains authoritative.

Performance remains stable.

No duplicated geometry exists.

The viewport experience feels comparable to professional CAD software.

---

Status

LOCKED

No future viewport implementation may violate this specification without updating this document first.

---

## Task 2.2.1

Status: COMPLETE

Summary

Implemented the first release-quality Multi Viewport Framework infrastructure.
The existing Canvas and Viewport3D remain preserved and are now registered with
a central ViewportManager as Top and Perspective viewport records. The
framework supports active viewport tracking, focused viewport tracking, layout
mode tracking and event broadcasting while preserving one shared Workspace and
one shared Scene.

ViewportManager

ViewportManager owns the UI-side viewport registry, active viewport id, focused
viewport id, layout mode and event broadcast signals. It can create viewports
through injected factories, register externally owned viewports, destroy or
close viewport records, rename viewports, track focus and expose current
workspace and scene through the injected provider without owning engineering
data.

Viewport Registry

Each registered viewport has a unique id, viewport type, widget, camera,
renderer, overlay manager, toolbar, dock container and workspace provider
reference. Supported framework viewport types include Perspective, Top, Front,
Right, Left, Back, Bottom, User, Camera and Section. Supported framework layout
modes include Single, Dual Horizontal, Dual Vertical, Quad and Custom.

Focus Management

Only one viewport is active at a time. Mouse press or focus on a registered
viewport updates the focused viewport and active viewport through the manager.
ViewportCreated, ViewportDestroyed, ViewportFocused, ViewportActivated,
LayoutChanged, ViewportRenamed and ViewportClosed events are emitted for
future synchronization.

Architecture Decisions

This task implements infrastructure only. It does not implement ViewCube,
Camera Sync, Navigation Bar, Bookmarks, Viewport Presets or rendering
improvements. Workspace, Shared Scene, Rendering Pipeline, Camera Mathematics,
Selection System, Command System, ToolManager, ProjectService,
WorkspaceProvider, Data Model and AI Architecture were not modified.

Remaining Tasks

Task 2.2.2 should implement the next visible multi-viewport workflow on top of
the manager without duplicating scene ownership or renderer logic.

----------------------------------------

## Task 2.2.2

Status: IN PROGRESS

Summary

Implemented the professional Viewport Layout Manager on top of the existing
WorkspaceViewportArea and ViewportManager infrastructure. The layout layer now
supports Single View, Dual Horizontal, Dual Vertical, Triple View and Quad View
without changing shared scene ownership, renderer ownership, camera
mathematics, selection, command routing or ToolManager behavior.

Layout Manager

ViewportLayoutManager composes existing and auxiliary shared-scene viewport
widgets inside splitter-based layouts. It creates, resizes, rearranges,
persists and restores viewport pane arrangements while preserving the existing
Canvas and Viewport3D instances. Layout close operations remove panes from the
visible arrangement without destroying injected viewport widgets or duplicating
engineering data.

Built-in Layouts

Single View shows the active viewport. Dual Horizontal and Dual Vertical show
Top and Perspective views. Triple View shows Top, Front and Perspective views.
Quad View defaults to Top, Front, Right and Perspective views as required by
the multi-viewport specification.

Focus Management

Clicking a pane activates that viewport through the existing ViewportManager.
The active viewport is highlighted in the viewport chrome and reflected through
the existing status-bar synchronization path. Double-clicking a viewport title
maximizes it; double-clicking the maximized title restores the previous layout.

Architecture Decisions

This task is layout management only. It does not implement ViewCube, camera
synchronization, navigation bar, camera bookmarks, renderer changes,
performance optimizations or new CAD behavior. Every viewport continues to
reference one shared Workspace and one shared Scene.

Remaining Tasks

Future multi-viewport tasks should add navigation affordances and camera
synchronization on top of this layout layer without changing shared scene
ownership.

----------------------------------------
