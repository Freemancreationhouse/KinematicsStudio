from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget

from engine.commands import (
    CancelManufacturingJobCommand,
    CaptureMachineDiagnosticsCommand,
    CreateMachineProfileCommand,
    CreateManufacturingJobCommand,
    ExecuteManufacturingJobCommand,
    ExportManufacturingJobCommand,
    GenerateToolpathCommand,
    InitializeMachineCAMWorkspaceCommand,
    PauseManufacturingJobCommand,
    PostProcessManufacturingJobCommand,
    QueueManufacturingJobCommand,
    ResumeManufacturingJobCommand,
    SimulateManufacturingJobCommand,
)


class MachineRibbon(QWidget):
    """Production Machine/CAM ribbon with command-routed workflow actions."""

    BUTTONS = [
        ("Machine Profile", "Create or activate the production machine profile."),
        ("Create Job", "Create a CAM job with setup and operation metadata."),
        ("Generate Toolpath", "Generate validated native CNC toolpaths."),
        ("Simulate", "Run virtual toolpath playback and verification."),
        ("Post Process", "Generate controller-specific G-code."),
        ("Export", "Export the generated manufacturing program."),
        ("Queue Job", "Queue and upload the active job through dispatch metadata."),
        ("Execute Job", "Start the uploaded manufacturing session."),
        ("Pause", "Pause the active manufacturing session."),
        ("Resume", "Resume the active manufacturing session."),
        ("Cancel Job", "Stop/cancel the active manufacturing session."),
        ("Diagnostics", "Capture Machine/CAM validation and diagnostics."),
    ]

    def __init__(self, tool_manager):
        super().__init__()
        self.tool_manager = tool_manager
        layout = QGridLayout(self)

        row = 0
        col = 0
        for text, tooltip in self.BUTTONS:
            button = QPushButton(text)
            button.setMinimumHeight(42)
            button.setToolTip(tooltip)
            self._connect(button, text)
            layout.addWidget(button, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)

    def _connect(self, button, text):
        actions = {
            "Machine Profile": self._machine_profile,
            "Create Job": self._create_job,
            "Generate Toolpath": self._generate_toolpath,
            "Simulate": self._simulate,
            "Post Process": self._post_process,
            "Export": self._export,
            "Queue Job": self._queue_job,
            "Execute Job": self._execute_job,
            "Pause": self._pause,
            "Resume": self._resume,
            "Cancel Job": self._cancel_job,
            "Diagnostics": self._diagnostics,
        }
        button.clicked.connect(actions[text])

    def _machine_profile(self):
        self._execute(CreateMachineProfileCommand(self._workspace()), "Machine profile ready.")

    def _create_job(self):
        self._execute(CreateManufacturingJobCommand(self._workspace()), "Manufacturing job created.")

    def _generate_toolpath(self):
        self._execute(GenerateToolpathCommand(self._workspace()), "Toolpath generated.")

    def _simulate(self):
        self._execute(SimulateManufacturingJobCommand(self._workspace()), "Manufacturing simulation completed.")

    def _post_process(self):
        self._execute(PostProcessManufacturingJobCommand(self._workspace()), "G-code generated.")

    def _export(self):
        self._execute(ExportManufacturingJobCommand(self._workspace()), "Manufacturing program exported.")

    def _queue_job(self):
        self._execute(QueueManufacturingJobCommand(self._workspace()), "Manufacturing job queued.")

    def _execute_job(self):
        self._execute(ExecuteManufacturingJobCommand(self._workspace()), "Manufacturing job execution started.")

    def _pause(self):
        self._execute(PauseManufacturingJobCommand(self._workspace()), "Manufacturing job paused.")

    def _resume(self):
        self._execute(ResumeManufacturingJobCommand(self._workspace()), "Manufacturing job resumed.")

    def _cancel_job(self):
        self._execute(CancelManufacturingJobCommand(self._workspace()), "Manufacturing job cancelled.")

    def _diagnostics(self):
        self._execute(CaptureMachineDiagnosticsCommand(self._workspace()), "Machine/CAM diagnostics captured.")

    def _execute(self, command, message):
        workspace = self._workspace()
        if workspace is None:
            self._status("Machine/CAM action failed: no active workspace.")
            return
        if command is None:
            return
        workspace.command_manager.execute(command)
        self._status(message)

    def _workspace(self):
        app = getattr(self.tool_manager, "app", None)
        return getattr(app, "workspace", None)

    def _status(self, message):
        canvas = getattr(self.tool_manager, "canvas", None)
        status_bar = getattr(canvas, "status_bar", None)
        if status_bar is not None:
            status_bar.show_status_text(message)
