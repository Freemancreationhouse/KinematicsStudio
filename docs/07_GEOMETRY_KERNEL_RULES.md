# GEOMETRY KERNEL RULES

**Project:** Kinematics Studio

**Version:** 1.0

**Status:** LOCKED

---

# Purpose

This document defines the mandatory architectural rules governing the Geometry Kernel of Kinematics Studio.

The Geometry Kernel is the core computational engine responsible for creating, editing, validating, and maintaining all geometric and topological data.

Every editing operation must comply with these rules.

These rules supersede implementation convenience.

---

# Vision

The Geometry Kernel shall support a modern hybrid CAD platform combining:

- Direct Modeling
- Parametric Modeling
- BIM
- CAM
- Computational Design
- AI-Assisted Modeling
- Digital Fabrication

without redesigning the core architecture.

---

# Fundamental Principle

Geometry is never edited directly by UI tools.

UI components only request operations.

The Geometry Kernel performs all modifications.

```
User

↓

Tool

↓

Command

↓

Geometry Kernel

↓

Topology

↓

Workspace

↓

Shared Scene

↓

Viewport Synchronization

↓

Rendering
```

---

# Single Source of Truth

The Workspace owns the active model.

The Geometry Kernel modifies only the Workspace model.

No viewport, tool, renderer or widget may own geometry.

---

# Geometry Ownership

Geometry exists only once.

Forbidden:

- Duplicate meshes
- Duplicate solids
- Duplicate curves
- Duplicate topology

Viewports only visualize geometry.

---

# Topology Ownership

The Geometry Kernel owns all topology.

Topology includes:

- Vertex
- Edge
- Loop
- Face
- Body
- Assembly

Topology may never be modified outside the kernel.

---

# Rendering Independence

The renderer never edits geometry.

The renderer only visualizes geometry.

Forbidden:

- Editing vertices
- Editing edges
- Editing faces
- Creating topology

inside rendering code.

---

# Command Architecture

Every geometric modification must execute through the Command System.

Examples:

Move

Rotate

Scale

Extrude

Fillet

Chamfer

Boolean

Shell

Mirror

Pattern

Offset

Delete Face

Bridge

Loft

Sweep

Revolve

Every command must support:

- Execute
- Undo
- Redo

---

# Undo / Redo

Undo never restores screenshots.

Undo restores model state.

Every editing command must be reversible.

---

# Editing Pipeline

Editing always follows:

```
Selection

↓

Command

↓

Geometry Kernel

↓

Topology Update

↓

Workspace

↓

Shared Scene

↓

Viewport Refresh
```

No shortcuts permitted.

---

# Selection Rules

Selection never modifies geometry.

Selection only references topology.

Supported selection types:

Object

Body

Face

Edge

Vertex

Loop

Ring

Shell

Component

Assembly

Selection must remain independent of rendering.

---

# Direct Modeling

Supported operations include:

Move Face

Offset Face

Extrude Face

Delete Face

Replace Face

Bridge Faces

Split Face

Shell

Draft

Press Pull

Direct Modeling modifies topology.

---

# Parametric Modeling

Feature-based operations create editable history.

Examples:

Extrude Feature

Fillet Feature

Chamfer Feature

Shell Feature

Pattern Feature

Mirror Feature

Feature history must remain editable.

---

# Feature History

History stores operations.

History never stores rendered geometry.

Example:

Sketch

↓

Extrude

↓

Fillet

↓

Shell

↓

Pattern

↓

Mirror

Editing an earlier feature rebuilds downstream features.

---

# Sketch Independence

Sketches are independent geometric entities.

Deleting a sketch shall not automatically delete generated solids unless dependency rules require it.

---

# Constraint Independence

Constraints belong to the Constraint Engine.

The Geometry Kernel requests constraint solving but never performs constraint calculations itself.

---

# Rendering Independence

The Geometry Kernel contains no rendering code.

Forbidden:

Qt

OpenGL

Widgets

Viewport logic

Painter

Rendering consumes kernel output only.

---

# Viewport Independence

Viewports own:

Camera

Projection

Navigation

Display Settings

ViewCube

Navigation Bar

Viewports never own geometry.

---

# Shared Scene Rules

The Shared Scene observes the Workspace.

It never owns independent geometry.

---

# Tool Rules

Tools gather user intent only.

Examples:

Line Tool

Move Tool

Extrude Tool

Chamfer Tool

Fillet Tool

Tools never edit topology directly.

---

# Geometry Validation

After every operation the kernel validates:

Closed solids

Non-manifold edges

Duplicate vertices

Zero-length edges

Degenerate faces

Invalid topology

Invalid operations shall fail safely.

---

# Boolean Operations

Supported:

Union

Subtract

Intersect

Slice

Split Body

Booleans execute inside the Geometry Kernel.

---

# Topology Rules

A Body contains Faces.

Faces contain Loops.

Loops contain Edges.

Edges connect Vertices.

No object may bypass this hierarchy.

---

# Precision

Internal calculations shall use double precision.

Rendering may convert for display only.

---

# Units

Kernel units remain unit-independent.

Millimetres, metres, inches and feet are presentation settings.

Internal calculations remain consistent.

---

# AI Integration

AI may propose operations.

AI never edits geometry directly.

AI requests commands through the same Command System as the user.

---

# BIM Integration

Walls

Doors

Windows

Columns

Beams

Roofs

Stairs

are specialized parametric bodies.

They obey Geometry Kernel rules.

---

# CAM Integration

Toolpaths reference geometry.

CAM never owns geometry.

---

# Digital Fabrication

Laser

CNC

3D Printing

Robotics

consume Geometry Kernel data.

They never modify it.

---

# Performance

The kernel shall minimize:

Memory allocations

Geometry duplication

Topology rebuilding

Viewport refreshes

---

# Thread Safety

Long-running kernel operations shall support future background execution.

UI access from kernel code is prohibited.

---

# Extensibility

Future modules shall extend the kernel through services.

Never modify core kernel behavior without architectural review.

---

# Forbidden Practices

The following are prohibited:

Editing geometry inside UI code

Editing topology inside rendering

Duplicating model data

Viewport-owned geometry

Renderer-owned geometry

Tool-owned geometry

Direct mesh manipulation from widgets

Skipping Command System

Skipping Undo/Redo

Skipping Workspace

---

# Architecture Freeze

The following principles are permanently locked:

- One Workspace
- One Shared Scene
- One Geometry Kernel
- One Command System
- One Selection System
- One Rendering Pipeline
- Independent Viewports
- Independent Cameras
- Geometry modified only through the Geometry Kernel

Future development must extend these systems rather than replace them.

---

# Approved

Kinematics Studio Architecture

Geometry Kernel Version 1.0

Status: LOCKED