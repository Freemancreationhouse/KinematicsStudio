# KINEMATICS STUDIO

# BUG TRACKER

---

## BUG TEMPLATE

Bug ID:

Title:

Priority:

Critical / High / Medium / Low

Status:

Open

Assigned Sprint:

Module:

Description:

Steps to Reproduce:

Expected Behaviour:

Actual Behaviour:

Root Cause:

Fix:

Verification:

Closed In Version:

---

# ACTIVE BUGS

## BUG-001

Title:

Development PySide6 runtime unavailable for launch verification

Priority:

Medium

Status:

Open

Assigned Sprint:

Sprint 1

Module:

Development Environment

Description:

The source files compile with the bundled Python runtime, but the available
local Python environments cannot execute a PySide6 MainWindow launch check.

Steps to Reproduce:

Run python or py from the project shell, or run .venv\Scripts\python.exe.

Expected Behaviour:

A working Python 3.12 environment with PySide6 should launch the application
for Sprint verification.

Actual Behaviour:

python and py are not available on PATH. The .venv launcher points to a
missing Python installation. The bundled Codex Python runtime does not include
PySide6.

Root Cause:

Local development runtime configuration is incomplete or stale.

Fix:

Restore a working Python 3.12 virtual environment with PySide6 installed.

Verification:

Run main_v2.py and instantiate MainWindow successfully from the restored
environment.

Closed In Version:

-
