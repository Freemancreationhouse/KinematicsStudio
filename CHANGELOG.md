# Changelog

---

# Version 0.2.0

Release Date: July 2026

## Added

- Professional 2D CAD Workspace
- Interaction Engine
- Line Tool
- Rectangle Tool
- Circle Tool
- Select Tool
- Move Tool
- Undo / Redo System
- Professional Pan & Zoom
- Professional Snap System
- Property Panel
- Explorer Panel
- Status Bar
- Ribbon Interface
- Command Manager
- Workspace Entity Management

## Improved

- Rendering Pipeline
- Camera System
- Tool Manager
- View Navigation
- Entity Selection
- Command History
- Workspace Architecture

## Fixed

- Drawing Preview
- Entity Persistence
- Selection Stability
- Rendering Flicker
- Camera Navigation
- Command Execution

---

# Version 0.2.1

Maintenance Release

## Improved

- Marked legacy modules with deprecation comments
- Added Workspace query helpers
- Added Renderer viewport culling
- Optimized History updates to avoid full rebuilds during normal command changes
- Split long methods into private helper methods
- Improved public class docstrings

---

# Version 0.3.0

## Added

- Trim Tool
- TrimEntityCommand
- Line × Line trimming
- Line × Rectangle Edge trimming
- Rectangle Edge × Line trimming
- Extend Tool
- ExtendEntityCommand
- Line × Line extension
- Line × Rectangle Edge extension
- Rectangle Edge × Line extension
- Offset Tool
- OffsetEntityCommand
- Line Offset
- Rectangle Offset
- Rotate Tool
- RotateEntityCommand
- Line rotation
- Rectangle rotation
- Circle rotation
- Mirror Tool
- MirrorEntityCommand
- Line mirroring
- Rectangle mirroring
- Circle mirroring
- Scale Tool
- ScaleEntityCommand
- Line scaling
- Rectangle scaling
- Circle scaling
- Copy Tool
- CopyEntityCommand
- Line copying
- Rectangle copying
- Circle copying
- Rectangular Array Tool
- ArrayEntityCommand
- Line rectangular arrays
- Rectangle rectangular arrays
- Circle rectangular arrays
- Fillet Tool
- FilletEntityCommand
- Line × Line fillets
- Chamfer Tool
- ChamferEntityCommand
- Line × Line chamfers

## Improved

- Modify Ribbon Trim activation
- Trim preview and Status Bar feedback
- Trim integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Extend activation
- Extend preview and Status Bar feedback
- Extend integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Offset activation
- Offset preview and Status Bar feedback
- Offset integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Rotate activation
- Rotate preview and Status Bar feedback
- Rotate integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Mirror activation
- Mirror preview and Status Bar feedback
- Mirror integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Scale activation
- Scale preview and Status Bar feedback
- Scale integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Copy activation
- Copy preview and Status Bar feedback
- Copy integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Array activation
- Rectangular Array preview and Status Bar feedback
- Rectangular Array integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Fillet activation
- Fillet preview and Status Bar feedback
- Fillet integration with Snap, Undo, Redo, Workspace, and Renderer systems
- Modify Ribbon Chamfer activation
- Chamfer preview and Status Bar feedback
- Chamfer integration with Snap, Undo, Redo, Workspace, and Renderer systems

---

# Version 0.3.1

Geometry Foundation Maintenance

## Added

- Shared geometry tolerance constant
- Shared line and segment intersection helpers
- Shared rectangle edge and bounds helpers
- Shared point-to-segment distance helper
- Shared signed distance helper
- Shared degenerate geometry checks
- Shared rotate and mirror point transform helpers
- Focused geometry foundation test coverage

## Improved

- Trim, Extend, Offset, Rotate and Mirror now reuse shared geometry helpers
- Reduced duplicated geometry logic across Modify geometry modules
- Replaced exact floating-point comparisons with tolerance-aware checks where appropriate

---

# Release 0.3 - Sprint 6.1

Scale Tool Refinement

## Improved

- Scale Tool mouse input now uses base point, reference point and current cursor position
- Numeric scale input continues to override mouse-derived scaling
- Removed the fixed Scale Tool world-unit reference distance

---

# Release 0.3 - Sprint 7-8

Copy Tool and Rectangular Array Tool

## Added

- Copy Tool using the shared geometry transform pipeline
- CopyEntityCommand for undoable copied entities
- Rectangular Array Tool using the shared copy geometry pipeline
- ArrayEntityCommand for undoable rectangular arrays

---

# Version 0.3.2

Geometry Maintenance 2

## Added

- Shared collinear segment detection helper
- Shared overlapping segment detection helper
- Shared segment classification helper
- Shared intersection classification helper
- Shared endpoint classification helper
- Focused geometry maintenance coverage for overlap, endpoint, tiny and huge geometry cases

## Improved

- Tolerance-aware handling for nearly parallel, coincident, shared-endpoint and degenerate segment cases
- Geometry API readiness for future Fillet and Chamfer tools

---

# Release 0.3 - Sprint 9-10

Professional Fillet Tool and Chamfer Tool

## Added

- Shared line-line corner geometry helper
- Fillet geometry module using Release 0.3.2 classification helpers
- Chamfer geometry module using Release 0.3.2 classification helpers
- Fillet Tool with numeric radius input and live preview
- Chamfer Tool with numeric distance input and live preview
- FilletEntityCommand and ChamferEntityCommand

## Improved

- Existing ArcEntity now renders fillet arcs

---

# Release 0.4 - Sprint 1

Professional Layer Architecture

## Added

- Internal Layer class with ID, name, visibility, lock, color, line type and line weight properties
- Internal LayerManager with Default Layer 0, unique layer names and current layer support
- Workspace layer ownership and current-layer assignment for newly stored entities
- Entity layer metadata using layer object, layer ID and layer name
- Layer-aware visible/selectable workspace queries

## Not Added

- Layer Manager UI

---

# Release 0.4 - Sprint 2

Professional Layer Manager

## Added

- Dockable Layer Manager panel in the V2 main window
- Layer table with current, name, visibility, lock, color, line type and line weight columns
- Toolbar actions for New Layer, Delete Layer, Rename Layer and Set Current Layer
- Layer 0 delete/rename protection
- Layer visibility and lock controls wired to workspace rendering and selection behavior

## Improved

- Move Tool now respects workspace layer lock/selectability rules
- Canvas selection sync now clears entities hidden or locked by layer state

---

# Release 0.4 - Sprint 5-7

Layer Visibility, Layer Lock and Layer Colors

## Improved

- Hidden layers are excluded from rendering, selection and modify workflows
- Locked layers remain visible but are excluded from selection, move and modify workflows
- Layer visibility and lock changes refresh canvas selection/rendering immediately
- Entity rendering now uses assigned layer color
- Layer color edits update existing entity display color
- New entities inherit current layer color
- Property Panel displays entity layer and layer color
- Layer Manager panel supports direct color, line type and line weight edits

---

# Release 0.4 - Sprint 10

Professional Object Properties

## Added

- Editable Property Panel fields for entity layer, visibility, lock state and geometry
- Command-driven property updates for Line, Rectangle and Circle entities
- Undo / Redo support for object property edits
- Property Panel editing for layer color, line type and line weight

## Improved

- Selection changes refresh object properties immediately
- Property edits refresh rendering, status and Layer Manager state through the existing UI pipeline

---

# Release 0.5 - Sprint 1

Professional Block Architecture

## Added

- Internal Block, BlockDefinition and BlockManager architecture
- BlockReference entity for placed definition references
- Workspace ownership of BlockManager
- Unique block IDs and names
- Block origin, definition entity collection and reference transform support
- Nested block-ready definition architecture

## Not Added

- Block Manager UI
- Block insertion UI
- Explode workflow

---

# Release 0.5 - Sprint 2

Professional Block Manager

## Added

- Dockable Block Manager panel in the V2 main window
- Block definition table with name, ID, entity count, nested block indicator, reference count and origin
- Toolbar buttons for New Block, Delete Block and Rename Block as deferred workflow placeholders
- Empty BlockManager state handling

## Not Added

- Insert Block workflow
- Edit Block workflow
- Explode Block workflow
