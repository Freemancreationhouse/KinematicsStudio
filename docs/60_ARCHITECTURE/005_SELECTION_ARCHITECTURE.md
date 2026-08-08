# SELECTION ARCHITECTURE

Project

Kinematics Studio

Version

1.0

Status

LOCKED

---

# Purpose

This document defines the Selection Architecture used throughout Kinematics Studio.

Selection is a core system shared by every module.

The Selection System determines what the user, AI, commands and tools operate on.

Selection never owns geometry.

Selection references Geometry Kernel topology using persistent identifiers.

---

# Design Philosophy

Selection is independent from:

- Rendering
- Viewports
- Camera
- Editing Tools
- Geometry Storage

Selection references objects only.

The Geometry Kernel owns the actual model.

---

# Selection Pipeline

```
User / AI

↓

Mouse

↓

Picking System

↓

Selection Manager

↓

Selection Context

↓

Command

↓

Geometry Kernel
```

---

# Selection Levels

Kinematics Studio supports hierarchical selection.

Assembly

↓

Component

↓

Body

↓

Shell

↓

Face

↓

Loop

↓

Edge

↓

Vertex

Only one selection mode is active at a time.

---

# Object Selection

Selects complete objects.

Examples

Body

Sketch

Curve

Mesh

Solid

Surface

Used for

Move

Rotate

Scale

Mirror

Array

Pattern

Copy

Delete

---

# Body Selection

Selects an editable Body.

Supports

Boolean

Material

Mass Properties

Visibility

Isolation

Grouping

---

# Face Selection

Selects one or more Faces.

Supports

Extrude

Offset

Delete Face

Move Face

Replace Face

Split Face

Bridge Faces

Shell

Draft

Material Override

---

# Edge Selection

Selects one or more Edges.

Supports

Fillet

Chamfer

Offset Edge

Bridge Edge

Split Edge

Slide Edge

Delete Edge

---

# Vertex Selection

Selects Vertices.

Supports

Move

Merge

Delete

Insert

Slide

Snap

Topology Repair

---

# Loop Selection

Selects complete boundary loops.

Supports

Offset

Bridge

Fill

Hole Editing

Boundary Editing

---

# Shell Selection

Selects complete Shells.

Supports

Extract

Separate

Merge

Repair

Convert

---

# Component Selection

Future assembly editing.

Supports

Assembly Constraints

Configurations

Explosion

Replacement

Grouping

---

# Assembly Selection

Future multi-component editing.

Supports

Move Assembly

Copy Assembly

Mirror Assembly

Simulation

---

# Multi Selection

Supports

Single

Multiple

Window

Crossing

Polygon

Lasso

Paint

---

# Selection Filters

Users may filter selectable entities.

Supported Filters

Body

Face

Edge

Vertex

Sketch

Construction Geometry

Reference Geometry

Dimensions

Annotations

Constraints

Assemblies

---

# Smart Selection

Supports

Loop Selection

Ring Selection

Connected Faces

Connected Edges

Connected Bodies

Grow Selection

Shrink Selection

Select Similar

Select by Material

Select by Layer

Select by Type

---

# Selection Context

Selection automatically changes available commands.

Examples

Face Selected

↓

Extrude

Offset

Shell

Edge Selected

↓

Fillet

Chamfer

Vertex Selected

↓

Move Vertex

Merge Vertex

Split Vertex

---

# Selection Highlight

Supports

Hover Highlight

Pre-selection

Selection Highlight

Active Highlight

Locked Highlight

Suppressed Highlight

Hidden entities are never highlighted.

---

# Selection Priority

Picking order

Vertex

↓

Edge

↓

Face

↓

Body

↓

Assembly

Priority may be changed by user preference.

---

# Persistent Selection

Selections survive

Camera movement

Viewport switching

Layout switching

Workspace synchronization

Selections update automatically after rebuilds whenever possible.

---

# Selection and AI

AI may request

Select Face

Select Edge

Select Body

Select Feature

Selection requests always resolve through the Selection Manager.

---

# Selection and Feature History

Selections reference persistent topology IDs.

Feature rebuilds should preserve selections whenever topology remains valid.

---

# Selection and BIM

Future BIM supports

Wall

Door

Window

Roof

Column

Beam

Slab

Selections use the same Selection Manager.

---

# Selection and CAM

CAM operations reference

Faces

Edges

Bodies

Selections are shared with machining operations.

---

# Selection Performance

Selection must support

Large assemblies

Fast picking

Incremental updates

Cached hit testing

Viewport independence

---

# Thread Safety

Selection updates occur on the main application thread.

Long-running analysis may use background workers.

---

# Forbidden Practices

Selection must never

Own geometry

Modify geometry

Modify topology

Depend on rendering

Depend on viewport implementation

Duplicate model data

---

# Architecture Rules

Mandatory

One Selection Manager

One Selection Context

One Picking System

One Geometry Kernel

Selections reference topology only.

---

# Future Compatibility

Supports

Direct Modeling

Parametric CAD

BIM

CAM

Simulation

AI Editing

Digital Fabrication

Cloud Collaboration

without redesigning the Selection System.

---

Approved

Kinematics Studio Architecture

Selection Architecture v1.0

Status

LOCKED