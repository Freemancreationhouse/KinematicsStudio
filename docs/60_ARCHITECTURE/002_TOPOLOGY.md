# TOPOLOGY ARCHITECTURE

Project

Kinematics Studio

Version

1.0

Status

LOCKED

---

# Purpose

This document defines the topological architecture used throughout Kinematics Studio.

Topology describes how geometric entities are connected.

Geometry defines shape.

Topology defines relationships.

The Geometry Kernel owns all topology.

No other system may create or modify topology directly.

---

# Design Philosophy

Kinematics Studio uses a Boundary Representation (B-Rep) topology model.

Topology is independent from rendering.

Topology is independent from UI.

Topology is independent from camera systems.

Topology is independent from viewports.

---

# Topology Hierarchy

Every model follows this hierarchy.

```
Assembly

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
```

Each level owns the next level.

No level may bypass another.

---

# Vertex

A Vertex represents one topological point.

Contains

- Unique ID
- Position
- Connected Edges
- Connected Faces
- Metadata

A Vertex never stores rendering data.

---

# Edge

An Edge connects two Vertices.

Contains

- Start Vertex
- End Vertex
- Underlying Geometry
- Adjacent Faces
- Metadata

Examples

Straight Edge

Arc Edge

Spline Edge

Circle Edge

---

# Loop

A Loop is an ordered collection of Edges.

Loops define boundaries.

Examples

Outer Boundary

Inner Boundary

Hole

Every Face owns at least one Loop.

---

# Face

A Face represents one bounded surface.

Contains

- Surface Geometry
- Outer Loop
- Inner Loops
- Adjacent Faces
- Surface Normal
- Material Reference

Examples

Plane

Cylinder

Cone

Sphere

NURBS Surface

---

# Shell

A Shell is a connected set of Faces.

Examples

Closed Solid

Open Surface

Multiple Shells may exist in one Body.

---

# Body

A Body represents one editable solid.

Contains

- Shells
- Material
- Feature History Reference
- Metadata
- User Properties

Bodies are the primary editing objects.

---

# Assembly

An Assembly contains Bodies.

Future support:

Components

Subassemblies

Instances

Constraints

---

# Ownership Rules

Assembly owns Bodies.

Bodies own Shells.

Shells own Faces.

Faces own Loops.

Loops own Edges.

Edges own Vertices.

Ownership never reverses.

---

# Adjacency Rules

Topology maintains relationships.

Examples

Vertex

↓

Connected Edges

Edge

↓

Adjacent Faces

Face

↓

Neighbour Faces

Body

↓

Contained Shells

These relationships must remain valid after every edit.

---

# Geometry Relationship

Topology references Geometry.

Geometry never references Topology.

Example

Edge

↓

Line Geometry

or

↓

Arc Geometry

or

↓

Spline Geometry

The same geometry type may be reused by different topology.

---

# Editing Rules

Editing operations modify topology.

Examples

Extrude

Creates

New Faces

New Edges

New Vertices

Fillet

Replaces

Sharp Edge

↓

Blend Faces

Chamfer

Replaces

Sharp Edge

↓

Chamfer Face

---

# Euler Operations

Topology modifications shall be based on Euler Operators.

Examples

Make Vertex

Kill Vertex

Make Edge

Kill Edge

Make Face

Kill Face

Split Edge

Split Face

Merge Face

Bridge Faces

Euler operations maintain valid topology.

---

# Topology Validation

After every operation validate:

No orphan vertices

No orphan edges

No invalid loops

No duplicate edges

No zero-length edges

No non-manifold edges

No dangling faces

No broken references

No invalid shells

---

# Non-Manifold Rules

The kernel shall detect:

Shared edge by more than two faces

Broken shell

Disconnected topology

Duplicate boundaries

Invalid body

Invalid topology shall fail safely.

---

# Open vs Closed Bodies

Closed Body

Every Edge belongs to exactly two Faces.

Open Body

Edges may belong to one Face only.

Both are supported.

---

# Face Orientation

Every Face stores a normal.

Normals must remain consistent.

Incorrect orientation shall trigger validation.

---

# Loop Orientation

Outer Loops

Counter-clockwise

Inner Loops

Clockwise

Orientation defines inside and outside.

---

# Topological Naming

Every object receives a persistent identifier.

Examples

Vertex_001

Edge_204

Face_018

Body_005

Persistent IDs support:

Feature History

Undo

Redo

AI

CAM

BIM

---

# Persistent References

Editing operations shall preserve references whenever possible.

Example

Changing a Fillet should not invalidate unrelated Face IDs.

Persistent references are required for:

Dimensions

Constraints

CAM

Feature History

Selections

---

# Selection Mapping

Selection uses topology.

Supported:

Body

Face

Edge

Vertex

Loop

Shell

Selections never reference rendered triangles.

---

# Rendering Relationship

Renderer receives tessellated geometry only.

Renderer never edits topology.

Topology never depends on rendering.

---

# Feature History Relationship

Feature History references topology.

Topology updates Feature History.

History never stores rendered meshes.

---

# AI Relationship

AI queries topology.

AI modifies topology only through Commands.

AI never edits vertices directly.

---

# BIM Relationship

Future BIM objects inherit Body.

Walls

Columns

Doors

Windows

Roofs

Stairs

retain valid topology.

---

# CAM Relationship

CAM references Faces and Edges.

Toolpaths update automatically when topology changes.

---

# Digital Fabrication

Laser

CNC

3D Printing

consume tessellated geometry generated from topology.

Fabrication never edits topology.

---

# Performance

Topology shall support:

Incremental updates

Partial rebuilds

Fast adjacency queries

Minimal duplication

Large assemblies

---

# Thread Safety

Topology updates occur through the Geometry Kernel.

Future background execution must preserve consistency.

---

# Forbidden Practices

The following are prohibited:

Editing topology in UI code

Editing topology in rendering

Editing topology in Viewports

Editing topology in Tools

Duplicating topology

Topology owned by Renderer

Topology owned by Viewports

Skipping validation

---

# Architecture Rules

Mandatory

One Topology System

One Geometry Kernel

One Workspace

One Shared Scene

Topology modified only by the Geometry Kernel.

---

# Future Compatibility

This architecture supports:

Direct Modeling

Parametric CAD

BIM

CAM

Simulation

Generative Design

AI Editing

Cloud Collaboration

Digital Fabrication

without redesigning topology.

---

Approved

Kinematics Studio Architecture

Topology Architecture v1.0

Status

LOCKED