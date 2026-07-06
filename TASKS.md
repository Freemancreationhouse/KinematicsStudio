# Kinematics Studio V2

## Release 0.2 - Sprint 1: Interaction Engine

- [x] Tool Manager integration
- [x] Canvas mouse events
- [x] Workspace entity storage
- [x] Renderer pipeline
- [x] Stable rendering
- [x] Live preview

## Release 0.2 - Sprint 2: Drawing Tools

- [x] Line Tool
- [x] Rectangle Tool
- [x] Circle Tool

## Release 0.2 - Sprint 3: Editing

- [x] Select Tool
- [x] Move Tool
- [x] Undo
- [x] Redo

## Release 0.2 - Sprint 4: View

- [x] Pan
- [x] Zoom
- [x] Fit View
- [x] Crosshair

## Release 0.2 - Sprint 5: Snap System

- [x] Endpoint Snap
- [x] Midpoint Snap
- [x] Center Snap
- [x] Intersection Snap
- [x] Nearest Snap
- [x] Quadrant Snap
- [x] Grid Snap
- [x] Snap Visual Feedback

## Release 0.3 - Sprint 1: Trim Tool

- [x] Trim Tool activation
- [x] Cutting edge selection
- [x] Trim target selection
- [x] Live trim preview
- [x] TrimEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation

## Release 0.3 - Sprint 2: Extend Tool

- [x] Extend Tool activation
- [x] Boundary edge selection
- [x] Extend target selection
- [x] Live extend preview
- [x] ExtendEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation

## Release 0.3 - Sprint 3: Offset Tool

- [x] Offset Tool activation
- [x] Entity selection
- [x] Offset distance input
- [x] Live offset preview
- [x] OffsetEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Line Offset
- [x] Rectangle Offset

## Release 0.3 - Sprint 4: Rotate Tool

- [x] Rotate Tool activation
- [x] Single and multi-entity selection
- [x] Base point selection
- [x] Live rotation preview
- [x] Mouse angle input
- [x] Numeric angle input
- [x] RotateEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Rotate Line
- [x] Rotate Rectangle
- [x] Rotate Circle

## Release 0.3 - Sprint 5: Mirror Tool

- [x] Mirror Tool activation
- [x] Single and multi-entity selection
- [x] Two-point mirror line
- [x] Live mirrored preview
- [x] MirrorEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Mirror Line
- [x] Mirror Rectangle
- [x] Mirror Circle

## Release 0.3 - Sprint 6: Scale Tool

- [x] Scale Tool activation
- [x] Single and multi-entity selection
- [x] Base point selection
- [x] Mouse scale factor input
- [x] Numeric scale factor input
- [x] Live scaled preview
- [x] ScaleEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Scale Line
- [x] Scale Rectangle
- [x] Scale Circle

## Release 0.3 - Sprint 6.1: Scale Tool Refinement

- [x] Removed fixed reference distance
- [x] Base / reference / current mouse scaling
- [x] Numeric input overrides mouse scaling
- [x] Shared transform helper reuse
- [x] Scale preview preserved
- [x] Undo / Redo preserved
- [x] Snap support preserved

## Release 0.3 - Sprint 7: Copy Tool

- [x] Copy Tool activation
- [x] Single and multi-entity selection
- [x] Base point selection
- [x] Destination point selection
- [x] Live copied preview
- [x] CopyEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Copy Line
- [x] Copy Rectangle
- [x] Copy Circle

## Release 0.3 - Sprint 8: Rectangular Array Tool

- [x] Array Tool activation
- [x] Single and multi-entity selection
- [x] Rows
- [x] Columns
- [x] Row spacing
- [x] Column spacing
- [x] Live rectangular array preview
- [x] ArrayEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Line rectangular array
- [x] Rectangle rectangular array
- [x] Circle rectangular array

## Release 0.3.1 - Geometry Foundation Maintenance

- [x] Shared geometry tolerance
- [x] Shared line and segment intersection helpers
- [x] Shared rectangle edge helpers
- [x] Shared point-to-segment distance helper
- [x] Shared signed distance helper
- [x] Shared degenerate geometry checks
- [x] Shared transform helpers
- [x] Trim geometry helper reuse
- [x] Extend geometry helper reuse
- [x] Offset geometry helper reuse
- [x] Rotate geometry helper reuse
- [x] Mirror geometry helper reuse
- [x] Focused geometry foundation tests

## Release 0.3.2 - Geometry Maintenance 2

- [x] Collinear line detection helper
- [x] Overlapping segment detection helper
- [x] Segment classification helper
- [x] Intersection classification helper
- [x] Endpoint classification helper
- [x] Nearly parallel line tolerance handling
- [x] Coincident line tolerance handling
- [x] Shared endpoint handling
- [x] Degenerate segment handling
- [x] Future Fillet / Chamfer geometry API preparation
- [x] Focused collinear / overlap / endpoint tests
- [x] Modify geometry regression smoke validation

## Release 0.3 - Sprint 9: Fillet Tool

- [x] Fillet Tool activation
- [x] First line selection
- [x] Second line selection
- [x] Numeric radius input
- [x] Live fillet preview
- [x] FilletEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Line × Line Fillet
- [x] Existing ArcEntity rendering

## Release 0.3 - Sprint 10: Chamfer Tool

- [x] Chamfer Tool activation
- [x] First line selection
- [x] Second line selection
- [x] Numeric distance input
- [x] Live chamfer preview
- [x] ChamferEntityCommand
- [x] Undo / Redo
- [x] Object Snap support
- [x] Status Bar updates
- [x] Escape cancellation
- [x] Line × Line Chamfer
