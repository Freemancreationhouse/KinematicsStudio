# Kinematics Studio V2 Architecture

Version: 2.0 (Frozen)

---

# Overview

Kinematics Studio is an AI-powered CAD / CAM / BIM / Digital Fabrication platform.

The architecture is frozen.

Future work must extend the existing architecture.

Do not redesign.

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
        ├── Geometry Layer
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

Geometry

↓

Command

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

Workspace owns every Entity.

---

# Geometry Layer

The Geometry Layer contains every reusable mathematical algorithm.

Modules include:

- primitives.py
- transforms.py
- tolerance.py

Future geometry modules may be added here.

All geometry calculations must go through this layer.

Tools must never implement geometry calculations directly.

---

# Tool System

Responsibilities

- Activate
- Mouse Press
- Mouse Move
- Mouse Release
- Escape
- Live Preview

Tools never create permanent geometry directly.

Permanent changes always go through Commands.

---

# Command System

Every editing operation is represented by a Command.

Examples

- AddEntityCommand
- MoveEntityCommand
- TrimEntityCommand
- ExtendEntityCommand
- OffsetEntityCommand
- RotateEntityCommand
- MirrorEntityCommand
- ScaleEntityCommand

Responsibilities

- Execute
- Undo
- Redo

---

# Workspace

Workspace owns:

- Entities
- Selection
- Visibility
- Layers
- Command Manager

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

Renderer never edits geometry.

Renderer only displays.

---

# Input Pipeline

```
Mouse

↓

Canvas

↓

Tool Manager

↓

Current Tool

↓

Geometry Layer

↓

Command

↓

Workspace

↓

Renderer
```

---

# Tool Manager

Responsibilities

- Register tools
- Activate tools
- Forward mouse events
- Forward keyboard events

Only one tool is active.

---

# Property Panel

Displays information from the selected entities.

Examples

- Position
- Length
- Radius
- Angle
- Scale
- Rotation

Never modifies geometry directly.

---

# Explorer

Displays

- Project
- Workspace
- Layers
- Assets
- History

---

# Status Bar

Displays

- Current Tool
- Coordinates
- Snap Mode
- Selection Count
- Machine Status

---

# AI Engine

Responsibilities

- Text → CAD
- Image → CAD
- Image → 3D
- Smart Sketch
- Rendering Assistance

AI must communicate through:

Geometry

↓

Commands

↓

Workspace

Never modify UI directly.

---

# Machine Engine

Responsibilities

- CNC
- Laser
- 3D Printing
- GRBL
- FluidNC
- Klipper
- Marlin

Machine Engine consumes CAD data.

It never edits CAD geometry.

---

# Geometry Rules

All reusable mathematics belongs inside:

- engine.geometry.primitives
- engine.geometry.transforms
- engine.geometry.tolerance

Never duplicate geometry logic inside:

- Tools
- Commands
- Renderer
- Workspace

If new mathematics is required:

Add it to the Geometry Layer.

Reuse it everywhere.

---

# Future Modules

Architecture Workspace

Product Workspace

Fabrication Workspace

Simulation Workspace

Cloud

Plugin System

Image → 3D

Text → CAD

AI Studio

---

# Engineering Principles

Reuse existing systems.

Avoid duplicate code.

Keep backward compatibility.

Keep the architecture frozen.

Improve implementation quality.

Never redesign the architecture.