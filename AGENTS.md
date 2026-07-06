# AGENTS.md
# Kinematics Studio V2

## Project

Kinematics Studio V2 is a professional CAD / CAM / BIM / AI / Digital Fabrication platform.

This project follows a frozen architecture.

The objective is to extend the platform without redesigning its structure.

---

# General Rules

- Read this file before making any changes.
- Read ARCHITECTURE.md before implementing new features.
- Read ROADMAP.md before starting a sprint.
- Read SPECIFICATIONS.md before implementing any tool.

---

# Frozen Architecture

Never redesign the architecture.

Never rename:

- folders
- packages
- classes
- public APIs

Extend existing systems whenever possible.

Avoid duplicate logic.

Maintain backward compatibility.

---

# Engineering Rules

- Prefer extending existing modules over creating new ones.
- Keep classes focused on one responsibility.
- Keep methods short and readable.
- Add docstrings to public classes and methods.
- Reuse existing systems before creating new code.
- Validate every feature before marking a sprint complete.
- Never mark a sprint complete unless it has passed UI validation.

---

# Development Rules

Every feature must:

- Support Undo
- Support Redo
- Support Selection
- Support Snap
- Support Workspace
- Support Renderer
- Support Property Panel
- Support Status Bar
- Support Command System

Never bypass the Command System.

Permanent geometry changes must always happen through Commands.

---

# Geometry Development Rules

All geometry operations must reuse the shared Geometry Layer.

Always use:

- engine.geometry.primitives
- engine.geometry.transforms
- engine.geometry.tolerance

Do not duplicate:

- Line intersection
- Segment intersection
- Distance calculations
- Transformation math
- Rectangle edge extraction
- Floating-point tolerance checks

If a helper does not exist:

1. Add it to the appropriate Geometry module.
2. Reuse it everywhere.
3. Never implement geometry math directly inside tools.

---

# Command Rules

Every editing operation must create a Command.

Examples:

- AddEntityCommand
- MoveEntityCommand
- TrimEntityCommand
- ExtendEntityCommand
- OffsetEntityCommand
- RotateEntityCommand
- MirrorEntityCommand
- ScaleEntityCommand

Undo and Redo must always work.

---

# Coding Rules

Do not create duplicate utility functions.

Do not duplicate geometry algorithms.

Do not duplicate rendering code.

Do not duplicate selection logic.

Keep reusable code inside shared modules.

---

# Testing Rules

Run only related tests during normal development.

Run full regression testing only before a release.

Every sprint must:

- Launch main_v2.py
- Pass related tests
- Produce a validation report

---

# Documentation Rules

Update whenever required:

- ROADMAP.md
- TASKS.md
- CHANGELOG.md
- SPECIFICATIONS.md

Never remove previous release history.

---

# Git Rules

Commit after every completed sprint.

Tag every completed release.

Keep Git history clean.

Never commit:

- __pycache__
- *.pyc
- .venv
- temporary files

---

# Long-term Rule

The architecture is frozen.

Improve the implementation.

Do not redesign the product.