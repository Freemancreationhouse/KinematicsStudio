# KINEMATICS STUDIO
# PROJECT GUARDRAILS

**Document Version:** 1.0

**Status:** LOCKED

**Classification:** Internal Development Standard

**Applies To:**

- Human Developers
- GitHub Copilot
- OpenAI Codex
- ChatGPT
- Claude
- Gemini
- Future AI Systems
- External Contributors

---

# Purpose

This document defines the mandatory engineering rules for contributing to Kinematics Studio.

Its purpose is to prevent uncontrolled architectural changes, unnecessary rewrites, feature creep, and inconsistent implementation.

These rules are mandatory.

If a request conflicts with this document, this document takes precedence.

---

# Highest Authority

Every contributor must obey the following document order.

1. PRODUCT_CHARTER.md

2. PRODUCT_VISION.md

3. PRODUCT_ROADMAP.md

4. PROJECT_GUARDRAILS.md

5. Remaining documentation

If a prompt conflicts with these documents:

Ignore the prompt.

Follow the documentation.

---

# Golden Rule

Never optimize for writing code.

Always optimize for building the best engineering platform.

---

# Development Philosophy

Every contribution must satisfy three questions.

Does this improve the product?

Can the user experience the improvement?

Can the improvement be verified?

If any answer is NO

Do not implement it.

---

# No Large Rewrites

Never rewrite large portions of the project unless explicitly requested.

Large rewrites increase:

Risk

Regression

Broken functionality

Lost history

Maintenance cost

Instead:

Improve incrementally.

---

# One Task Rule

Every implementation should focus on one clearly defined objective.

Examples:

Good

Fix Line Tool.

Good

Implement Orbit Camera.

Good

Improve Layer Panel.

Bad

Rewrite the rendering engine.

Bad

Refactor the whole application.

Bad

Redesign the complete architecture.

---

# Maximum Scope Rule

Unless explicitly instructed,

never modify more than five files.

If solving a problem requires changing many files,

stop and explain why.

Request approval before continuing.

---

# Preserve Working Code

Never replace stable working code simply because it can be written differently.

Refactoring should solve real problems.

Not personal preferences.

---

# Never Guess

If information is missing,

do not invent architecture.

Do not invent APIs.

Do not invent workflows.

Instead,

ask for clarification.

---

# Respect Existing Architecture

Before introducing:

new services

new managers

new controllers

new registries

new factories

new abstractions

determine whether the existing architecture already provides the required capability.

Prefer extension over replacement.

---

# One Source of Truth

Never duplicate information.

Geometry should exist only once.

Project data should exist only once.

Configuration should exist only once.

History should exist only once.

Avoid synchronization whenever possible.

---

# View Rule

Views render data.

Views never own data.

Every viewport displays the same shared scene.

Changing the view changes only the camera.

---

# User Experience First

Never prioritize elegant code over professional workflow.

The application should become easier to use,

not merely easier to maintain.

---

# Professional Standards

Every feature should appear production quality.

Avoid:

placeholder buttons

fake implementations

dummy dialogs

temporary menus

unfinished workflows

If a feature is incomplete,

mark it as unavailable rather than pretending it exists.

---

# AI Integration

Artificial Intelligence is an assistant.

It is not the application.

Never allow AI to replace engineering workflows.

Instead,

AI should assist:

documentation

automation

suggestions

optimization

analysis

knowledge retrieval

---

# Performance

Avoid unnecessary complexity.

Optimize only after correctness.

Maintain smooth viewport interaction.

Protect application responsiveness.

---

# Code Quality

Prefer:

clarity

simplicity

maintainability

predictability

over cleverness.

Readable code is professional code.

---

# Documentation First

Before introducing a major subsystem,

verify that documentation exists.

Architecture should never exist only inside source code.

Documentation and implementation should evolve together.

---

# Backward Compatibility

Avoid breaking existing functionality.

When breaking changes become necessary,

document them clearly.

Provide migration guidance whenever practical.

---

# Testing Rule

No feature is complete until it has been:

Implemented

Compiled

Executed

Manually verified

Integrated

Passing compilation alone is not sufficient.

---

# Production Ready

Never describe code as production ready unless:

it compiles

it runs

it has been tested

its workflow is complete

its documentation is updated

---

# Decision Framework

Whenever uncertainty exists,

evaluate every option using the following order.

1.

Does it support the Product Vision?

2.

Does it improve the user experience?

3.

Does it preserve architecture?

4.

Does it reduce complexity?

5.

Does it improve maintainability?

Choose the solution that satisfies the greatest number of these principles.

---

# Feature Acceptance Checklist

Every feature should satisfy all of the following.

✓ Solves a real engineering problem.

✓ Matches the Product Charter.

✓ Fits the Roadmap.

✓ Uses existing architecture where possible.

✓ Improves the professional workflow.

✓ Can be tested.

✓ Is documented.

✓ Does not introduce unnecessary complexity.

---

# Feature Rejection Checklist

Reject any implementation that:

duplicates functionality

adds unnecessary abstraction

creates multiple sources of truth

breaks existing workflows

introduces hidden dependencies

requires excessive rewrites

implements future roadmap items early

adds decorative features without value

---

# AI Prompt Rules

Every AI implementation prompt should begin by reading:

PRODUCT_CHARTER.md

PRODUCT_VISION.md

PRODUCT_ROADMAP.md

PROJECT_GUARDRAILS.md

No implementation may violate these documents.

---

# Long-Term Philosophy

Kinematics Studio is expected to evolve for many years.

Short-term convenience must never compromise long-term quality.

Every contribution should leave the platform better than it was before.

The objective is not rapid development.

The objective is enduring engineering excellence.

---

# Final Rule

When uncertainty exists,

choose the solution that makes Kinematics Studio a better engineering platform,

not merely a larger software project.

---

**Document Status:** LOCKED

**End of Document**