# Kinematics Studio V2 Architecture

Version: 2.0 (Frozen)

---

# Overview

Kinematics Studio is an AI-powered CAD/CAM/BIM platform.

The architecture is frozen.

All future development must extend the existing architecture instead of redesigning it.

---

# Core Architecture

```
Application
    │
    ▼
CAD Engine
    │
    ├── Workspace
    ├── Rendering
    ├── Input
    ├── Tool System
    ├── Command System
    ├── Entity System
    ├── AI Engine
    └── Machine Engine
```

---

# Entity Lifecycle

```
Mouse

↓

Tool

↓

Entity

↓

Workspace

↓

Renderer

↓

Canvas

↓

Screen
```

Entities are never rendered directly.

Every entity must exist inside the Workspace.

---

# Tool System

Each tool must inherit from Tool.

Responsibilities:

- Activate
- Mouse Press
- Mouse Move
- Mouse Release
- Escape
- Preview Drawing

Tools must never draw permanent geometry.

Only preview graphics.

Permanent geometry is created as Entities.

---

# Entity System

Every drawable object is an Entity.

Examples

- LineEntity
- RectangleEntity
- CircleEntity
- TextEntity

Future

- PolylineEntity
- ArcEntity
- SplineEntity
- ImageEntity
- MeshEntity

Responsibilities

- Store geometry
- Store style
- Draw itself
- Serialize

---

# Workspace

Workspace owns every Entity.

Responsibilities

- Add Entity
- Remove Entity
- Selection
- Layers
- Visibility
- Serialization

Renderer reads only from Workspace.

---

# Rendering Pipeline

```
Workspace

↓

Renderer

↓

Camera

↓

Canvas

↓

Qt Painter
```

Renderer never edits entities.

Renderer only displays them.

---

# Command System

Every editing operation is a Command.

Examples

- AddEntityCommand
- RemoveEntityCommand
- MoveEntityCommand
- UpdateEntityCommand

Responsibilities

- Execute
- Undo
- Redo

All editing operations must support Undo/Redo.

---

# Tool Manager

ToolManager owns all tools.

Responsibilities

- Register Tool
- Activate Tool
- Forward Mouse Events
- Forward Keyboard Events

Only one tool may be active.

---

# Input System

Mouse

↓

Input Manager

↓

Tool Manager

↓

Current Tool

---

# Property Panel

Never stores geometry.

Reads selected entity only.

Displays

- Position
- Size
- Radius
- Length
- Angle

---

# Explorer

Displays

Project

Workspace

Layers

Assets

History

---

# Status Bar

Displays

Current Tool

Coordinates

Selection Count

Snap Status

Machine Status

---

# AI Engine

Responsibilities

Text → CAD

Image → CAD

Image → 3D

Smart Sketch

Floor Plan

Rendering

The AI Engine communicates through the CAD Engine.

It must never manipulate the UI directly.

---

# Machine Engine

Responsibilities

GRBL

FluidNC

Klipper

Marlin

CNC

Laser

3D Printing

The Machine Engine consumes CAD data.

It never modifies CAD geometry.

---

# Future Modules

Architecture Workspace

Product Workspace

Fabrication Workspace

Simulation

Cloud

Plugin System

---

# Engineering Rules

Never redesign architecture.

Never rename folders.

Never rename classes.

Reuse existing systems.

Avoid duplicate code.

Prefer extension over replacement.

Every sprint must pass validation before completion.

Always maintain backward compatibility.
