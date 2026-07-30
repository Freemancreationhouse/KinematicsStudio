# Kinematics Studio V2 UI Design System

## 1. Purpose

Kinematics Studio V2 is a professional engineering application for CAD, BIM, CAM, simulation, visualization, and coordination workflows. Its interface must feel like production engineering software: precise, dense where necessary, calm under complexity, and optimized around continuous interaction with geometry.

The UI standard is viewport first.

The viewport is the product. Every ribbon, panel, toolbar, command surface, menu, and status element exists to support model creation, editing, analysis, review, and fabrication without competing with the working view.

This design system is not based on websites, dashboards, admin panels, marketing pages, or consumer productivity apps. It is a desktop engineering UI standard comparable in intent and seriousness to Autodesk Revit, Rhino, Fusion 360, 3ds Max, SketchUp, and other professional modeling environments.

## 2. Core Design Principles

### 2.1 Viewport First

The central drawing and modeling viewport must dominate the application.

Default target:

- Viewport and model interaction area: 75–80% of usable window space.
- Supporting UI: 20–25% of usable window space.
- Panels must be collapsible, dockable, or on-demand.
- Manager panels must never crowd the startup workspace.
- The user should feel they are working in the model, not managing panels.

### 2.2 Engineering Density

The UI may be information-rich, but it must remain structured.

Professional users expect:

- compact controls;
- predictable command placement;
- persistent state indicators;
- fast access to tools;
- minimum animation noise;
- explicit status feedback;
- clear object, layer, snap, and command state.

### 2.3 Command Confidence

Every visible action must communicate what it does and whether it is available.

Controls must clearly express:

- default state;
- hover state;
- active state;
- selected state;
- disabled state;
- warning/error state;
- command-in-progress state.

### 2.4 Stable Muscle Memory

Tool locations should not shift casually.

Ribbon tabs may collapse adaptively, but primary tool locations must remain predictable. Workspace switching must preserve user orientation. Shortcuts and command names must remain stable.

### 2.5 Professional Restraint

The interface should feel technical and refined, not decorative.

Use:

- crisp geometry;
- measured contrast;
- restrained color accents;
- clean icons;
- subtle elevation;
- purposeful typography;
- minimal transitions.

Avoid:

- large marketing-style cards in the workspace;
- oversized rounded panels;
- dashboard-style metric blocks as primary UI;
- web-app spacing;
- bright gradients;
- decorative animation;
- playful iconography.

## 3. Window Layout

### 3.1 Default Application Structure

The default application window uses a permanent shell:

```text
┌──────────────────────────────────────────────────────────────┐
│ Menu Bar                                                     │
├──────────────────────────────────────────────────────────────┤
│ Ribbon                                                       │
├──────┬───────────────────────────────────────────────┬───────┤
│ Left │                                               │ Right │
│ Tool │              Viewport / Drawing Area          │ Side  │
│ Bar  │                                               │ Bar   │
├──────┴───────────────────────────────────────────────┴───────┤
│ Command Line                                                 │
├──────────────────────────────────────────────────────────────┤
│ Status Bar                                                   │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Startup Visible UI

Only these are visible at startup:

- Menu Bar
- Ribbon
- Left Toolbar
- Canvas / Viewport
- Right Sidebar
- Bottom Command Line
- Status Bar

The following must not appear as visible startup panels:

- Layer Manager
- Block Manager
- Pattern Manager
- Dimension Manager
- Group Manager
- Constraint Manager
- Selection Sets
- Reference Browser
- Reference Layers
- Coordination
- Clash Manager
- Clash Dashboard
- BCF Topic Browser
- Any diagnostics or manager-heavy panels

These panels remain available through menus, command palette, workspace actions, and panel manager commands.

### 3.3 Layout Proportions

Default desktop proportions:

- Left Toolbar: 64–72 px.
- Right Sidebar: 300 px initial width.
- Right Sidebar minimum: 260 px.
- Right Sidebar maximum: 420 px.
- Ribbon: compact professional height; never visually dominates the model.
- Command Line: one compact command band.
- Status Bar: one compact status band.

The viewport must naturally expand when the window grows.

### 3.4 Window Chrome

The main application title should show:

- application name;
- active project name;
- dirty state indicator;
- optional workspace name.

Recommended title format:

```text
Kinematics Studio — ProjectName.ksproj *
```

The dirty state marker appears only when unsaved changes exist.

## 4. Menu Bar

### 4.1 Menu Principles

The menu bar provides complete command access and predictable desktop behavior.

Menus must be:

- stable;
- hierarchical;
- keyboard navigable;
- aligned with desktop engineering software conventions;
- not overloaded with experimental commands.

### 4.2 Top-Level Menus

Required menu hierarchy:

```text
File
Edit
View
Insert
Modify
Draw
Tools
Workspaces
Panels
Analyze
Fabrication
Window
Help
```

### 4.3 File Menu

```text
File
├─ New Project
├─ Open Project
├─ Open Recent
├─ Save
├─ Save As
├─ Import
├─ Export
├─ Project Settings
├─ Recover Project
├─ Close Project
└─ Exit
```

### 4.4 Edit Menu

```text
Edit
├─ Undo
├─ Redo
├─ Cut
├─ Copy
├─ Paste
├─ Duplicate
├─ Delete
├─ Select All
├─ Deselect All
└─ Preferences
```

### 4.5 View Menu

```text
View
├─ 2D View
├─ 3D View
├─ Fit View
├─ Zoom Extents
├─ Pan
├─ Orbit
├─ Display Mode
│  ├─ Wireframe
│  ├─ Hidden Line
│  ├─ Shaded
│  └─ Rendered
├─ Grid
├─ Axes
├─ Snaps
├─ Focus Mode
├─ Presentation Mode
└─ Reset Workspace Layout
```

### 4.6 Panels Menu

```text
Panels
├─ Project
│  ├─ Explorer
│  └─ Project Manager
├─ CAD
│  ├─ Layer Manager
│  ├─ Dimension Manager
│  ├─ Pattern Manager
│  ├─ Block Manager
│  └─ Group Manager
├─ Selection
│  └─ Selection Sets
├─ Constraints
│  └─ Constraint Manager
├─ References
│  ├─ Reference Browser
│  └─ Reference Layers
├─ Coordination
│  └─ Coordination
├─ BIM Coordination
│  ├─ Clash Manager
│  ├─ Clash Dashboard
│  └─ BCF Topic Browser
└─ Diagnostics
```

### 4.7 Window Menu

```text
Window
├─ Workspace Presets
├─ Save Current Layout
├─ Restore Default Layout
├─ Close Floating Panels
└─ Bring All Panels to Front
```

## 5. Ribbon

### 5.1 Ribbon Role

The ribbon is the primary command discovery surface. It is not the only command surface. Expert users should be able to use shortcuts, command line, context menus, and command palette without relying on the ribbon.

### 5.2 Ribbon Tabs

Required ribbon tabs:

```text
Project
Draw
Modify
3D
BIM
Analyze
Fabrication
AI
View
Manage
```

Current tabs may be mapped into this structure over time.

### 5.3 Project Tab

Groups:

```text
Project
├─ New
├─ Open
├─ Save
├─ Import
├─ Export
├─ Templates
└─ Recovery
```

### 5.4 Draw Tab

Groups:

```text
Draw
├─ Basic Geometry
│  ├─ Line
│  ├─ Polyline
│  ├─ Rectangle
│  └─ Circle
├─ Curves
│  ├─ Arc
│  ├─ Ellipse
│  ├─ Spline
│  └─ Polygon
├─ Annotation
│  ├─ Text
│  ├─ Leader
│  └─ Dimensions
└─ Fills
   └─ Hatch
```

### 5.5 Modify Tab

Groups:

```text
Modify
├─ Transform
│  ├─ Move
│  ├─ Rotate
│  ├─ Scale
│  └─ Mirror
├─ Edit
│  ├─ Trim
│  ├─ Extend
│  ├─ Offset
│  └─ Delete
├─ Duplicate
│  ├─ Copy
│  └─ Array
└─ Corners
   ├─ Fillet
   └─ Chamfer
```

### 5.6 3D Tab

Groups:

```text
3D
├─ Primitives
│  ├─ Box
│  ├─ Cylinder
│  ├─ Sphere
│  ├─ Cone
│  ├─ Torus
│  └─ Plane
├─ Solids
│  ├─ Extrude
│  ├─ Revolve
│  ├─ Sweep
│  └─ Loft
├─ Boolean
│  ├─ Union
│  ├─ Subtract
│  └─ Intersect
└─ Inspection
```

### 5.7 BIM Tab

Groups:

```text
BIM
├─ Model
├─ References
├─ Coordination
├─ Clash Detection
├─ Issues
├─ Reviews
└─ BCF
```

### 5.8 Analyze Tab

Groups:

```text
Analyze
├─ Measurement
├─ Sections
├─ Simulation
├─ Structural
├─ Thermal
├─ CFD
└─ Reports
```

### 5.9 Fabrication Tab

Groups:

```text
Fabrication
├─ Machine Setup
├─ Jobs
├─ Toolpaths
├─ Simulation
├─ Post Processing
└─ Export
```

### 5.10 AI Tab

Groups:

```text
AI
├─ Context
├─ Prompt
├─ Task Queue
├─ Recommendations
├─ History
└─ Diagnostics
```

### 5.11 Ribbon Icon Sizes

Use three command sizes:

- Large command: 32 px icon, label below.
- Medium command: 24 px icon, label right or below depending group density.
- Small command: 16 px icon, compact row.

Primary creation and modification tools use large or medium icons.

Secondary commands use small icons.

### 5.12 Ribbon Spacing

Recommended spacing:

- Group outer padding: 8 px horizontal, 6 px vertical.
- Button spacing: 4 px.
- Group divider: 1 px line with low contrast.
- Tab padding: 12–16 px horizontal.
- Minimum command hit target: 32 px height.

### 5.13 Ribbon Collapsed Behavior

The ribbon supports:

- full mode;
- compact mode;
- collapsed tab-only mode;
- temporary expansion on tab click.

Collapsed ribbon must preserve keyboard access.

### 5.14 Adaptive Resizing

When space is limited:

1. Hide secondary text labels.
2. Collapse low-priority groups into group menus.
3. Switch large buttons to medium.
4. Switch medium buttons to small.
5. Preserve primary groups for the active workspace.

Primary commands must remain accessible without horizontal scrolling whenever possible.

## 6. Left Toolbar

### 6.1 Role

The left toolbar is a permanent, pinned, vertical action surface for fast workspace control.

It is not a layer manager, object tree, or property panel.

### 6.2 Dimensions

- Width: 64–72 px.
- Icon target: 24 px.
- Button target: 48–56 px height.
- Toolbar remains pinned by default.

### 6.3 Button Style

The left toolbar is icon-only by default.

Each button must provide:

- tooltip;
- active state;
- disabled state;
- hover feedback;
- keyboard accessibility;
- optional expandable flyout.

### 6.4 Required Actions

```text
Select
Draw
Modify
View 2D
View 3D
Panels
Command Palette
Focus Mode
```

### 6.5 Expandable Behavior

The toolbar may expand temporarily to show labels:

- on explicit user action;
- by keyboard command;
- not automatically on accidental hover.

Expanded width target:

- 180–220 px.

The expanded state must never permanently reduce viewport space unless pinned by the user.

## 7. Right Sidebar

### 7.1 Role

The right sidebar is a permanent property and inspection area.

Default content:

```text
Properties
```

The sidebar should not host every manager panel at startup.

### 7.2 Structure

The right sidebar is tabbed and collapsible.

Required tabs:

```text
Properties
Selection
Object
Material
Metadata
```

Tabs may be hidden when empty, but Properties remains the default.

### 7.3 Dimensions

- Initial width: 300 px.
- Minimum width: 260 px.
- Maximum width: 420 px.
- Collapsed width: 36–44 px.

### 7.4 Property Layout

Properties are grouped into sections:

```text
General
Geometry
Transform
Layer
Appearance
Constraints
Metadata
Diagnostics
```

Each section supports:

- expand/collapse;
- inline editing;
- validation state;
- read-only state;
- mixed-value display for multi-selection.

### 7.5 Docking

The right sidebar can:

- collapse;
- resize;
- float;
- dock right;
- optionally dock left for user preference.

It must return to the default right position via Reset Workspace Layout.

## 8. Bottom Command Line

### 8.1 Role

The command line is a professional command input surface inspired by AutoCAD-style workflows.

It supports:

- typed commands;
- command prompts;
- numeric input;
- coordinate input;
- option keywords;
- command history;
- error messages;
- command completion.

### 8.2 Layout

Default command line:

```text
Command: [ input field                                      ]
```

Expanded command history:

```text
Command History
├─ LINE
├─ Specify first point:
├─ Specify next point:
└─ Command complete.
Command: [ input field                                      ]
```

### 8.3 Behavior

The command line must:

- stay above the status bar;
- remain compact by default;
- expand only when requested or during multi-step command input;
- support Enter, Escape, Tab, arrow history, and command autocomplete;
- never block viewport interaction unless a command requires input.

### 8.4 Command Feedback

Command feedback uses severity states:

- normal;
- prompt;
- success;
- warning;
- error.

Errors must be readable but not disruptive.

## 9. Status Bar

### 9.1 Role

The status bar gives continuous model, command, and environment state.

It must be compact, stable, and always visible except in presentation mode.

### 9.2 Required Status Items

```text
Grid
Snap
Ortho
Polar
Object Snap
Coordinates
Units
Selection Count
Active Layer
Active Tool
Undo/Redo State
FPS
Machine State
Project Dirty State
```

### 9.3 Status Item Behavior

Status items may be:

- read-only indicators;
- toggles;
- menu buttons;
- warnings.

Clickable toggles:

```text
Grid
Snap
Ortho
Polar
Object Snap
Units
```

### 9.4 Coordinates

Coordinate format:

```text
X: 0000.000  Y: 0000.000  Z: 0000.000
```

2D workspaces may hide Z or show Z as 0.000.

### 9.5 Units

Units display must be concise:

```text
mm
cm
m
in
ft
deg
```

Unit changes should be accessible from the status bar menu.

## 10. Theme

### 10.1 Default Theme

The default theme is dark professional.

It should feel like a production modeling environment, not a high-contrast code editor and not a website dashboard.

### 10.2 Color Tokens

Core colors:

```text
Application Background       #101318
Viewport Background          #1b1f26
Panel Background             #181c22
Panel Header                 #202631
Ribbon Background            #1a1f27
Toolbar Background           #15181d
Border Subtle                #2a2f38
Border Strong                #3a4350
Text Primary                 #e6eaf0
Text Secondary               #aeb7c4
Text Muted                   #6f7a88
Accent Blue                  #3f8cff
Accent Blue Active           #2563eb
Warning                      #d9a441
Error                        #d85c5c
Success                      #5fbf7a
Selection                    #2f6fed
Hover                        #26303c
Disabled Background          #181b21
Disabled Text                #666d78
```

### 10.3 Viewport Colors

Viewport visual system:

```text
Background                   #1b1f26
Grid Major                   #3a4350
Grid Minor                   #2a303a
Axis X                       #d85c5c
Axis Y                       #5fbf7a
Axis Z                       #5c9dd8
Selection Outline            #ffcc4d
Hover Outline                #7db7ff
Construction Geometry        #8a94a6
Locked Object                #5d6673
Hidden Preview               #4b5563
```

### 10.4 Typography

Primary UI font:

- Segoe UI on Windows.
- SF Pro on macOS.
- Noto Sans fallback.

Recommended sizes:

```text
Menu Bar                     12 px
Ribbon Tab                   12 px
Ribbon Button                11 px
Panel Header                 12 px, semibold
Property Label               11 px
Property Value               11 px
Command Line                 12 px monospace-capable
Status Bar                   11 px
Dialog Title                 14 px, semibold
```

Command line may use:

- Cascadia Mono;
- Consolas;
- JetBrains Mono;
- platform monospace fallback.

### 10.5 Icon Style

Icons must be:

- technical;
- geometric;
- line-based;
- consistent stroke weight;
- legible at 16 px;
- readable on dark backgrounds.

Recommended stroke:

- 1.5 px at 24 px icon size.

Icon fills should be avoided except for active states.

### 10.6 Spacing

Spacing tokens:

```text
2 px    hairline/internal compact spacing
4 px    tight button spacing
6 px    toolbar internal margin
8 px    default panel padding
12 px   dialog and group padding
16 px   large panel spacing
24 px   major dialog sections
```

### 10.7 Corner Radius

Professional desktop radius:

```text
Small controls               3 px
Buttons                      4 px
Panel cards                  4 px
Dialogs                      6 px
Floating utility windows     6 px
```

Avoid large rounded web-style corners.

### 10.8 Elevation

Use subtle elevation only for:

- floating panels;
- command palette;
- modal dialogs;
- dropdowns;
- flyouts.

Elevation should be expressed through:

- slight shadow;
- border contrast;
- background layering.

Do not use dramatic shadows.

### 10.9 Hover States

Hover states:

- slightly brighter background;
- accent border for high-value tools;
- no layout shift;
- no size change.

### 10.10 Selected States

Selected state:

- accent blue background or side bar;
- high-contrast text;
- persistent until selection changes.

Active command state:

- highlighted ribbon/toolbox button;
- command line prompt;
- status bar active tool.

### 10.11 Disabled States

Disabled controls:

- muted text;
- reduced border contrast;
- no hover accent;
- tooltip may explain why unavailable.

Disabled controls should remain readable.

## 11. Interaction Rules

### 11.1 Selection

Selection must be visually immediate.

Rules:

- hover preview before click;
- selected objects display clear outline or highlight;
- multi-selection uses consistent highlight;
- locked objects show non-editable selection state;
- hidden objects cannot be selected;
- selection count updates status bar;
- properties update immediately.

### 11.2 Hover

Hover feedback must never obscure geometry.

Viewport hover:

- object outline or subtle glow;
- cursor feedback;
- snap marker if applicable.

UI hover:

- compact background change;
- no excessive animation.

### 11.3 Ribbon Interaction

Ribbon buttons:

- single-click activates immediate command;
- split buttons show variants;
- dropdowns close after command unless pinned;
- active command remains visibly active.

Tooltips:

- short title;
- one-line purpose;
- optional shortcut;
- no marketing copy.

### 11.4 Panels

Panels must support:

- resize;
- collapse;
- float;
- dock;
- search where content is long;
- keyboard navigation.

Manager panels open on demand. They do not appear by default.

### 11.5 Docking

Docking behavior:

- edges show clear drop targets;
- docking preview must be subtle but visible;
- floating panels remember last geometry;
- reset layout returns to viewport-first default.

### 11.6 Shortcuts

Shortcut principles:

- conventional where possible;
- stable across workspaces;
- discoverable in tooltips and command palette.

Core shortcuts:

```text
Ctrl+N        New Project
Ctrl+O        Open Project
Ctrl+S        Save
Ctrl+Shift+S  Save As
Ctrl+Z        Undo
Ctrl+Y        Redo
Ctrl+C        Copy
Ctrl+V        Paste
Delete        Delete
Escape        Cancel command / clear transient state
Ctrl+K        Command Palette
F             Fit View
G             Toggle Grid
S             Toggle Snap, when not text editing
```

### 11.7 Context Menus

Context menus are workspace-aware.

Viewport context menu:

```text
Repeat Last Command
Select
Hide
Isolate
Properties
Move
Rotate
Scale
Delete
Zoom to Selection
```

Object context menu adds object-specific actions.

Panel context menus expose panel-specific actions only.

### 11.8 Command Cancellation

Escape behavior:

1. cancel current input step;
2. cancel current command;
3. clear hover/preview;
4. optionally clear selection only when no command is active.

### 11.9 Command Preview

Commands that create or modify geometry should provide preview when practical.

Preview geometry:

- uses distinct preview color;
- is non-selectable;
- disappears on cancel;
- becomes real only after command confirmation.

## 12. Responsive Behavior

### 12.1 1080p Desktop

Target resolution:

```text
1920 × 1080
```

Behavior:

- full menu bar visible;
- ribbon in compact or standard mode;
- right sidebar at 300 px;
- left toolbar at 68 px;
- viewport remains dominant.

If vertical space is constrained, ribbon groups collapse before command line or status bar are hidden.

### 12.2 1440p Desktop

Target resolution:

```text
2560 × 1440
```

Behavior:

- standard ribbon mode;
- richer labels visible;
- right sidebar may use 320 px;
- command line can optionally show one-line history;
- viewport remains primary.

### 12.3 4K Desktop

Target resolution:

```text
3840 × 2160
```

Behavior:

- high-DPI icons;
- increased viewport clarity;
- panels do not grow excessively;
- max sidebar width remains enforced;
- spacing scales carefully without becoming web-like.

### 12.4 Ultrawide

Target examples:

```text
3440 × 1440
5120 × 1440
```

Behavior:

- viewport gains most extra width;
- sidebars do not expand beyond maximum;
- optional secondary panel docking may use extra width;
- ribbon does not stretch command groups unnaturally.

### 12.5 Laptop

Target examples:

```text
1366 × 768
1440 × 900
1536 × 864
```

Behavior:

- ribbon enters compact mode;
- right sidebar can collapse;
- command line remains visible but compact;
- status bar may hide low-priority items behind overflow;
- left toolbar remains pinned;
- viewport remains usable.

### 12.6 Small Height Behavior

When vertical height is limited:

1. Ribbon groups compact.
2. Ribbon collapses to tabs.
3. Command history collapses to one-line command input.
4. Status bar moves low-priority items into overflow.

The viewport must not be sacrificed before supporting UI compacts.

## 13. Workspace-Specific UI Personality

Each workspace may have subtle identity while preserving the shared system.

### 13.1 CAD

Personality:

- drafting precision;
- clear snaps;
- visible grid;
- fast linework tools.

Accent usage:

- blue selection;
- yellow snap/preview markers.

### 13.2 3D CAD

Personality:

- shaded modeling;
- transform gizmos;
- viewport mode emphasis.

Accent usage:

- axis colors;
- solid selection outlines.

### 13.3 BIM

Personality:

- coordination;
- references;
- issue state;
- model hierarchy.

Accent usage:

- severity colors;
- review state tags.

### 13.4 Simulation

Personality:

- analysis clarity;
- result overlays;
- legend-driven interpretation.

Accent usage:

- scalar ramps;
- warning colors only for engineering warnings.

### 13.5 Machine/CAM

Personality:

- machine state;
- toolpath clarity;
- simulation timeline;
- post-processing confidence.

Accent usage:

- operation states;
- machine safety warnings.

### 13.6 AI

Personality:

- engineering assistant;
- deterministic context;
- task and recommendation history.

Accent usage:

- restrained purple or blue secondary accent;
- never chatbot-first.

## 14. Panel Standards

### 14.1 Panel Header

Panel headers include:

- title;
- optional search;
- pin/collapse;
- close;
- overflow menu.

### 14.2 Panel Content

Panel content uses:

- tables for managers;
- trees for hierarchy;
- forms for properties;
- split views only when necessary.

### 14.3 Empty States

Empty states must be professional and compact.

Format:

```text
No items
Short explanation
Primary action if available
```

Avoid oversized illustrations in engineering panels.

## 15. Dialog Standards

Dialogs should be:

- modal only when required;
- resizable for data-heavy workflows;
- keyboard navigable;
- clear about destructive actions.

Dialog buttons:

```text
Primary action
Secondary action
Cancel
```

Destructive actions use warning color and confirmation.

## 16. Command Palette Standard

The command palette is a keyboard-first professional launcher.

It searches:

- commands;
- tools;
- panels;
- workspaces;
- settings;
- documentation.

Command palette result format:

```text
Category · Command Name                         Shortcut
```

It must support:

- fuzzy search;
- recent commands;
- favorites;
- keyboard navigation;
- Enter to execute;
- Escape to close.

## 17. Accessibility

Requirements:

- all controls keyboard reachable;
- focus rings visible;
- high-contrast theme available;
- no color-only meaning for critical states;
- minimum readable text contrast;
- tooltips available for icon-only buttons;
- status changes readable in text.

## 18. Motion

Motion must be restrained.

Allowed:

- short fade for panel open;
- subtle slide for collapsible sidebar;
- hover transition under 120 ms;
- command palette fade/scale under 120 ms.

Not allowed:

- bouncing;
- elastic motion;
- decorative loading animations in the modeling workspace;
- long transitions that block work.

## 19. Permanent UI Standard

The default Kinematics Studio UI must always preserve:

- viewport-first layout;
- professional CAD/BIM visual density;
- ribbon-based command discovery;
- left pinned icon toolbar;
- right properties sidebar;
- bottom AutoCAD-style command line;
- compact engineering status bar;
- hidden-on-startup manager panels;
- stable keyboard and command workflows.

Any future UI feature must support the viewport, not compete with it. 
