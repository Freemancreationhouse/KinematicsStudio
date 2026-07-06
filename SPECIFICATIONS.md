# Kinematics Studio V2
## Tool Specifications

Version: 1.0

Geometry Foundation:

Status:

MAINTAINED IN 0.3.2

Shared helpers:

✓ GEOMETRY_EPSILON
✓ Line intersection
✓ Segment intersection
✓ Rectangle edge extraction
✓ Point-to-segment distance
✓ Signed distance to line
✓ Degenerate geometry checks
✓ Common transform helpers

âœ“ Collinear segment detection
âœ“ Overlapping segment detection
âœ“ Segment classification
âœ“ Intersection classification
âœ“ Endpoint classification

---

# General Rules

Every tool must:

- Support Undo
- Support Redo
- Support Snap
- Support Selection
- Show Live Preview (where applicable)
- Update Property Panel
- Update Status Bar
- Create Commands
- Work inside Workspace
- Use Renderer only for display
- Never bypass Command System

---

# Line Tool

Activation:
Ribbon → Draw → Line

Workflow:

1. Activate Line Tool
2. First click
3. Live Preview
4. Second click
5. Create LineEntity
6. Store in Workspace

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview

---

# Rectangle Tool

Activation:
Ribbon → Draw → Rectangle

Workflow:

1. First corner
2. Live Preview
3. Second corner
4. RectangleEntity

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview

---

# Circle Tool

Activation:
Ribbon → Draw → Circle

Workflow:

1. Center
2. Live Preview
3. Radius
4. CircleEntity

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview

---

# Select Tool

Activation:
Ribbon → Modify → Select

Supports:

Single Selection

Ctrl + Click

Window Selection

Crossing Selection

Property Updates

Status Updates

---

# Move Tool

Activation:
Ribbon → Modify → Move

Workflow:

Select

Base Point

Second Point

Live Preview

MoveEntityCommand

Supports:

Undo

Redo

Snap

Multi-selection

---

# Trim Tool

Status:

IMPLEMENTED

Workflow:

1. Select cutting edge
2. Preview target trim
3. Confirm trim
4. Create TrimEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Line × Line
✓ Line × Rectangle Edge
✓ Rectangle Edge × Line

---

# Extend Tool

Status:

IMPLEMENTED

Workflow:

1. Select boundary edge
2. Preview target extension
3. Confirm extension
4. Create ExtendEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Line × Line
✓ Line × Rectangle Edge
✓ Rectangle Edge × Line

---

# Offset Tool

Status:

IMPLEMENTED

Workflow:

1. Select entity
2. Move cursor or type offset distance
3. Preview offset result
4. Confirm offset
5. Create OffsetEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Line Offset
✓ Rectangle Offset
✓ Polyline-ready geometry pipeline
✓ Circle-ready geometry pipeline

---

# Rotate Tool

Status:

IMPLEMENTED

Workflow:

1. Select one or more entities
2. Select base point
3. Move cursor or type angle
4. Preview rotated result
5. Confirm rotation
6. Create RotateEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Numeric angle input
✓ Line rotation
✓ Rectangle rotation
✓ Circle rotation
✓ Future entity rotation pipeline

---

# Mirror Tool

Status:

IMPLEMENTED

Workflow:

1. Select one or more entities
2. Select first mirror-line point
3. Select second mirror-line point
4. Preview mirrored result
5. Confirm mirror
6. Create MirrorEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Line mirroring
✓ Rectangle mirroring
✓ Circle mirroring
✓ Future entity mirror pipeline

---

# Scale Tool

Status:

IMPLEMENTED

Workflow:

1. Select one or more entities
2. Select base point
3. Select reference point
4. Move cursor or type scale factor
5. Preview scaled result
6. Confirm scale
7. Create ScaleEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Numeric scale input
✓ Line scaling
✓ Rectangle scaling
✓ Circle scaling
✓ Shared geometry transform pipeline

---

# Copy Tool

Status:

IMPLEMENTED

Workflow:

1. Select one or more entities
2. Select base point
3. Select destination point
4. Preview copied result
5. Confirm copy
6. Create CopyEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Multi-selection
✓ Line copying
✓ Rectangle copying
✓ Circle copying
✓ Shared geometry transform pipeline

---

# Array Tool

Status:

IMPLEMENTED

Workflow:

1. Select one or more entities
2. Select base point
3. Set rows and columns
4. Move cursor to define row and column spacing
5. Preview rectangular array result
6. Confirm array
7. Create ArrayEntityCommand

Supports:

✓ Undo
✓ Redo
✓ Snap
✓ Preview
✓ Multi-selection
✓ Rows
✓ Columns
✓ Row spacing
✓ Column spacing
✓ Line rectangular arrays
✓ Rectangle rectangular arrays
✓ Circle rectangular arrays
✓ Future polar array pipeline

---

# Fillet Tool

Status:

IMPLEMENTED

Workflow:

1. Select first line
2. Select second line
3. Type radius
4. Preview fillet result
5. Press Enter or click to confirm
6. Create FilletEntityCommand

Supports:

âœ“ Undo
âœ“ Redo
âœ“ Snap
âœ“ Preview
âœ“ Numeric radius input
âœ“ Line Ã— Line Fillet
âœ“ Shared geometry classification pipeline

---

# Chamfer Tool

Status:

IMPLEMENTED

Workflow:

1. Select first line
2. Select second line
3. Type distance
4. Preview chamfer result
5. Press Enter or click to confirm
6. Create ChamferEntityCommand

Supports:

âœ“ Undo
âœ“ Redo
âœ“ Snap
âœ“ Preview
âœ“ Numeric distance input
âœ“ Line Ã— Line Chamfer
âœ“ Shared geometry classification pipeline
