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

# Layer Architecture

Status:

IMPLEMENTED INTERNALLY

Layer System:

1. Workspace owns LayerManager
2. LayerManager creates default Layer 0
3. New entities are assigned to the current layer
4. Layer names are unique
5. Layers have stable IDs
6. Layers support visibility, lock, color, line type and line weight

Supports:

Ã¢Å“â€œ Workspace integration
Ã¢Å“â€œ Entity layer relationship
Ã¢Å“â€œ Current layer
Ã¢Å“â€œ Future Groups
Ã¢Å“â€œ Future Blocks
Ã¢Å“â€œ Future Dimensions
Ã¢Å“â€œ Future Text
Ã¢Å“â€œ Future BIM metadata

Not Implemented:

- None for internal layer architecture

---

# Layer Manager UI

Status:

IMPLEMENTED

Panel:

1. Dockable Layer Manager panel
2. Displays layer name
3. Displays current layer
4. Displays visibility
5. Displays lock
6. Displays color
7. Displays line type
8. Displays line weight

Toolbar:

Ã¢Å“â€œ New Layer
Ã¢Å“â€œ Delete Layer
Ã¢Å“â€œ Rename Layer
Ã¢Å“â€œ Set Current Layer

Rules:

Ã¢Å“â€œ Layer 0 cannot be deleted
Ã¢Å“â€œ Layer 0 cannot be renamed
Ã¢Å“â€œ Current layer affects future entities only
Ã¢Å“â€œ Hidden layers are not rendered
Ã¢Å“â€œ Hidden layers cannot be selected
Ã¢Å“â€œ Locked layers remain visible
Ã¢Å“â€œ Locked layers cannot be moved through normal tools
Ã¢Å“â€œ Hidden layers cannot be modified
Ã¢Å“â€œ Locked layers cannot be modified
Ã¢Å“â€œ New entities inherit current layer color
Ã¢Å“â€œ Existing entities display assigned layer color
Ã¢Å“â€œ Property Panel displays layer color

---

# Object Properties

Status:

IMPLEMENTED

Property Panel:

1. Displays entity type, layer, visibility and lock state
2. Displays Line start point, end point, length and angle
3. Displays Rectangle width and height
4. Displays Circle center, radius and diameter
5. Displays layer color, line type and line weight
6. Edits selected entity properties through the Command System
7. Supports Undo and Redo for property edits
8. Refreshes immediately when selection changes

Rules:

✓ Property Panel never bypasses the Command System
✓ Layer assignment stays synchronized with Workspace LayerManager
✓ Rendering updates after property changes

---

# Block Architecture

Status:

IMPLEMENTED INTERNALLY

Block System:

1. Workspace owns BlockManager
2. BlockManager owns BlockDefinition objects
3. Block definitions have unique IDs and unique names
4. Block definitions store an origin point
5. Block definitions own reusable entity collections
6. BlockReference entities point to definitions
7. BlockReference stores insertion point, rotation and scale transform
8. Nested blocks are supported by allowing definitions to contain references

Not Implemented:

- Block Manager UI
- Block insertion UI
- Explode

---

# Block Manager UI

Status:

IMPLEMENTED

Panel:

1. Dockable Block Manager panel
2. Displays Block Name
3. Displays Block ID
4. Displays Entity Count
5. Displays Nested Block Indicator
6. Displays Reference Count
7. Displays Origin
8. Handles empty BlockManager state

Toolbar:

✓ New Block button placeholder
✓ Delete Block button placeholder
✓ Rename Block button placeholder

Not Implemented:

- Insert Block
- Edit Block
- Explode Block

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
