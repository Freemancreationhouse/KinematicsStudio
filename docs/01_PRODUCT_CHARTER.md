# KINEMATICS STUDIO
## PRODUCT CHARTER
Version: 1.0
Status: LOCKED

---

# THIS DOCUMENT IS THE HIGHEST AUTHORITY

This document defines the vision, philosophy, architecture and development rules of Kinematics Studio.

Every implementation decision MUST follow this document.

If a prompt conflicts with this document:

THIS DOCUMENT WINS.

Never sacrifice the long-term product vision for short-term implementation convenience.

---

# PRODUCT VISION

Kinematics Studio is NOT another CAD software.

Kinematics Studio is NOT another BIM software.

Kinematics Studio is NOT another AI chatbot.

Kinematics Studio is a next-generation Engineering Platform that unifies:

• CAD
• Parametric Design
• Computational Design
• AI
• BIM
• Robotics
• Digital Fabrication
• CAM
• CNC
• Manufacturing
• Architecture
• Engineering
• Product Design

inside one ecosystem.

---

# DESIGN PHILOSOPHY

The software must feel like:

"Professional Engineering Software"

NOT

• Website
• Dashboard
• Admin Panel
• Mobile App

Primary inspirations:

• Autodesk Revit
• Rhino
• Fusion 360
• Blender
• 3ds Max

---

# PRODUCT PRIORITIES

Priority 1

A working product.

Priority 2

Professional user experience.

Priority 3

Maintainable architecture.

Priority 4

Performance.

Priority 5

Advanced features.

Never reverse this order.

---

# USER EXPERIENCE

The user should feel:

"I am using a professional engineering platform."

Not

"I am testing a prototype."

Every screen must look intentional.

Every button must have a purpose.

Every feature must work.

---

# VIEWPORT FIRST

The viewport IS the product.

Everything else supports the viewport.

Approximate space allocation:

Viewport
70–80%

Ribbon
10%

Panels
10–20%

Never allow the interface to dominate the viewport.

---

# ONE SCENE RULE

There shall only be ONE scene.

Never separate geometry into:

Canvas geometry

Viewport geometry

There is ONE shared scene.

Every viewport renders the same data.

Views never own geometry.

Views are renderers only.

---

# VIEW SYSTEM

Changing views never changes data.

Changing views only changes cameras.

Required views:

Top

Bottom

Front

Back

Left

Right

Perspective

Isometric

All views render the same project.

---

# DEVELOPMENT STRATEGY

Development is milestone based.

Each milestone must produce visible progress.

No milestone may end with architecture only.

Every milestone must be executable.

---

# NO ARCHITECTURE FOR ITS OWN SAKE

Architecture exists only to improve the product.

Never introduce:

Manager

Controller

Service

Factory

Registry

Bridge

Adapter

unless it solves a real product problem.

---

# IMPLEMENTATION RULES

Every new feature must satisfy:

Does it work?

Can the user see it?

Can the user test it?

Can the user use it?

If any answer is NO

The feature is incomplete.

---

# AI

AI is an assistant.

AI is NOT the application.

AI must integrate into workflows.

Never replace workflows.

---

# BIM

BIM is a future milestone.

Do not implement BIM until CAD is stable.

---

# CAM

CAM is a future milestone.

Do not implement CAM until CAD modeling is complete.

---

# DIGITAL FABRICATION

Digital fabrication is a future milestone.

---

# UI PRINCIPLES

Professional

Minimal

Dense

Efficient

Predictable

Fast

No oversized buttons.

No wasted space.

No decorative UI.

---

# RIBBON

The ribbon should expose only the most commonly used tools.

Advanced tools belong in:

Panels

Dialogs

Command Palette

Extensions

Never overload the ribbon.

---

# PANELS

Panels are contextual.

Panels should not overwhelm the workspace.

---

# PERFORMANCE

Smooth interaction is more important than visual effects.

Animations should be subtle.

Never reduce viewport responsiveness.

---

# QUALITY STANDARD

Never call a feature complete unless:

It compiles.

It runs.

It is manually testable.

It behaves correctly.

It matches the product vision.

---

# CODING RULES

Prefer readability.

Avoid unnecessary abstraction.

Avoid duplication.

Prefer composition.

Avoid premature optimization.

---

# WORKFLOW

Every task follows this order:

1. Design

2. Implement

3. Compile

4. Run

5. Test

6. Verify

7. Merge

Never skip testing.

---

# MILESTONE COMPLETION

A milestone is complete only when:

The application launches.

The feature works.

The user verifies it.

Only then proceed.

---

# ABSOLUTE RULE

Do not optimize for writing code.

Optimize for building the best engineering software.