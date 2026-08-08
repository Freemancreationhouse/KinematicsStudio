# EDITING PIPELINE ARCHITECTURE

Project

Kinematics Studio

Version

1.0

Status

LOCKED

---

# Purpose

This document defines the complete editing pipeline used throughout Kinematics Studio.

Every editing operation shall follow exactly the same execution path.

No editing operation may bypass any stage.

The editing pipeline guarantees:

- Data integrity
- Undo / Redo
- Feature History
- Shared Scene synchronization
- Multi-Viewport synchronization
- BIM compatibility
- CAM compatibility
- AI compatibility

---

# Design Philosophy

Editing is command-driven.

No UI component edits geometry directly.

Every modification passes through:

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

Validation

↓

History

↓

Workspace

↓

Shared Scene

↓

Viewport Synchronization

↓

Renderer

---

# Complete Pipeline

```
Mouse

↓

Keyboard

↓

Ribbon

↓

Shortcut

↓

AI

↓

API

↓

Tool
```

↓

```
Selection
```

↓

```
Editing Command
```

↓

```
Geometry Kernel
```

↓

```
Topology Update
```

↓

```
Geometry Validation
```

↓

```
Feature History
```

↓

```
Workspace Update
```

↓

```
Shared Scene Notification
```

↓

```
Viewport Synchronization
```

↓

```
Dirty Viewport Detection
```

↓

```
Renderer
```

---

# Stage 1

User Input

Supported sources

Mouse

Keyboard

Ribbon

Toolbar

Shortcut

Context Menu

AI Assistant

Automation

Plugin

No source may bypass the pipeline.

---

# Stage 2

Tool

Examples

Move Tool

Rotate Tool

Scale Tool

Extrude Tool

Fillet Tool

Chamfer Tool

Boolean Tool

Mirror Tool

Pattern Tool

The Tool only gathers user intent.

The Tool never edits geometry.

---

# Stage 3

Selection

SelectionManager resolves:

Object

Body

Face

Edge

Vertex

Loop

Shell

Selection produces references only.

Never geometry.

---

# Stage 4

Command

Every edit becomes a Command.

Examples

MoveCommand

RotateCommand

ScaleCommand

ExtrudeCommand

FilletCommand

ChamferCommand

MirrorCommand

BooleanCommand

Commands contain

Execute()

Undo()

Redo()

Commands own editing transactions.

---

# Stage 5

Geometry Kernel

The Geometry Kernel receives the command.

Responsibilities

Interpret request

Allocate geometry

Update topology

Generate features

Notify Workspace

The Geometry Kernel owns all geometry changes.

---

# Stage 6

Topology Update

Modify

Vertices

Edges

Loops

Faces

Shells

Bodies

Assemblies

Topology remains valid.

---

# Stage 7

Validation

Automatically validate

Zero-length edges

Duplicate vertices

Broken loops

Open solids

Invalid shells

Non-manifold edges

Degenerate faces

Broken references

Validation failure

↓

Rollback

↓

User notification

---

# Stage 8

Feature History

Successful edits generate Features.

Example

Sketch

↓

Extrude

↓

Fillet

↓

Pattern

↓

Mirror

Feature History stores parameters.

Never rendered meshes.

---

# Stage 9

Workspace

Workspace receives updated model.

Workspace owns

Geometry

Properties

Layers

Selection

Events

Workspace becomes the new source of truth.

---

# Stage 10

Shared Scene

Shared Scene observes Workspace.

Shared Scene updates:

Visible geometry

Bounding boxes

Selection

Display flags

No geometry duplication.

---

# Stage 11

Viewport Synchronization

Synchronize

Perspective

Top

Front

Right

Left

Back

Bottom

Synchronize only Workspace state.

Never synchronize cameras.

---

# Stage 12

Dirty Detection

Determine

Which viewport changed?

Which overlays changed?

Which entities changed?

Only dirty viewports redraw.

---

# Stage 13

Rendering

Renderer receives

Read-only geometry

Read-only topology

Read-only camera

Renderer never edits the model.

---

# Undo Pipeline

Undo follows

History

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

Viewports

↓

Renderer

Undo never restores screenshots.

Undo restores model state.

---

# Redo Pipeline

Redo follows the same path.

---

# Property Editing

Property Panel

↓

Command

↓

Geometry Kernel

↓

Workspace

↓

Shared Scene

↓

Renderer

---

# Layer Editing

Layer changes

↓

Workspace

↓

Shared Scene

↓

Viewports

↓

Renderer

---

# AI Editing

AI

↓

Editing Command

↓

Geometry Kernel

↓

Workspace

↓

Shared Scene

↓

Renderer

AI uses the same pipeline as the user.

---

# BIM Editing

Wall

↓

Edit Height

↓

Command

↓

Geometry Kernel

↓

Workspace

↓

Renderer

BIM never bypasses the kernel.

---

# CAM Editing

Geometry

↓

Workspace

↓

CAM references update

↓

Toolpaths rebuild

---

# Failure Recovery

If validation fails

Rollback

↓

Restore previous topology

↓

Restore previous Workspace

↓

Keep Feature History consistent

↓

Notify user

---

# Event Flow

Every successful edit emits

GeometryChanged

↓

TopologyChanged

↓

WorkspaceChanged

↓

SharedSceneChanged

↓

ViewportRefreshRequested

↓

RenderCompleted

---

# Transaction Rules

Every command executes inside one transaction.

If any stage fails

↓

Entire transaction rolls back.

No partial edits.

---

# Performance Rules

Batch multiple edits where possible.

Avoid duplicate events.

Avoid duplicate redraws.

Avoid duplicate validation.

Incremental updates only.

---

# Forbidden Operations

The following are prohibited

Renderer editing geometry

Viewport editing geometry

Tool editing topology

Widget editing model

Skipping validation

Skipping history

Skipping Workspace

Skipping Shared Scene

Skipping Command System

---

# Architecture Rules

Mandatory

One Editing Pipeline

One Geometry Kernel

One Workspace

One Shared Scene

One History

One Command System

Everything follows the same pipeline.

---

# Future Compatibility

Supports

Direct Modeling

Parametric Modeling

BIM

CAM

Simulation

Rendering

AI

Cloud Collaboration

Robotics

Digital Fabrication

without changing the editing architecture.

---

Approved

Kinematics Studio Architecture

Editing Pipeline v1.0

Status

LOCKED