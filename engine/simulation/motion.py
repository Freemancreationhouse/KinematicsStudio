"""Motion and mechanism simulation foundation for Simulation Workspace.

Motion data references existing workspace/product geometry by identifier only.
The mechanism solver evaluates deterministic rigid-body kinematics through the
existing solver interface and stores results in the shared results database.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import cos, pi, sin, sqrt
from uuid import uuid4


MOTION_STUDY_TYPES = {
    "Mechanism Study",
    "Rigid Body Study",
    "Assembly Motion Study",
    "Animation Study",
    "Kinematic Study",
    "Comparative Motion Study",
}


MOTION_JOINT_TYPES = {
    "Fixed Joint",
    "Revolute Joint",
    "Prismatic Joint",
    "Cylindrical Joint",
    "Planar Joint",
    "Spherical Joint",
    "Pin Joint",
    "Slider Joint",
    "Hinge Joint",
    "Rack & Pinion",
    "Gear Pair",
    "Belt",
    "Chain",
    "Cam",
    "Custom Joint",
}


MOTION_DRIVER_TYPES = {
    "Angular Motor",
    "Linear Motor",
    "Velocity Driver",
    "Position Driver",
    "Acceleration Driver",
    "Servo",
}


MOTION_MECHANISM_TYPES = {
    "Four-Bar Linkage",
    "Slider-Crank",
    "Scissor Mechanism",
    "Pantograph",
    "Gear Train",
    "Pulley",
    "Door Hinge",
    "Drawer Slide",
    "Furniture Hinge",
    "Robot Arm",
    "Custom Mechanism",
}


@dataclass
class MotionRigidBody:
    """Rigid body metadata referencing existing CAD/product geometry."""

    study_id: str
    name: str
    geometry_references: list = field(default_factory=list)
    mass: float = 1.0
    center_of_gravity: dict = field(default_factory=dict)
    inertia_metadata: dict = field(default_factory=dict)
    reference_frame: dict = field(default_factory=dict)
    local_coordinate_systems: list = field(default_factory=list)
    is_ground: bool = False
    group: str = ""
    suppressed: bool = False
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe rigid body metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "geometry_references": [dict(item) for item in self.geometry_references],
            "mass": self.mass,
            "center_of_gravity": dict(self.center_of_gravity),
            "inertia_metadata": dict(self.inertia_metadata),
            "reference_frame": dict(self.reference_frame),
            "local_coordinate_systems": [dict(item) for item in self.local_coordinate_systems],
            "is_ground": self.is_ground,
            "group": self.group,
            "suppressed": self.suppressed,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create rigid body metadata from persisted data."""

        data = data or {}
        return MotionRigidBody(
            data.get("study_id", ""),
            data.get("name", "Rigid Body"),
            [dict(item) for item in data.get("geometry_references", [])],
            float(data.get("mass", 1.0)),
            dict(data.get("center_of_gravity", {})),
            dict(data.get("inertia_metadata", {})),
            dict(data.get("reference_frame", {})),
            [dict(item) for item in data.get("local_coordinate_systems", [])],
            bool(data.get("is_ground", False)),
            data.get("group", ""),
            bool(data.get("suppressed", False)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class MotionJoint:
    """Joint or motion constraint between two rigid bodies."""

    study_id: str
    name: str
    joint_type: str
    parent_body_id: str = ""
    child_body_id: str = ""
    axis: dict = field(default_factory=dict)
    origin: dict = field(default_factory=dict)
    limits: dict = field(default_factory=dict)
    constraint_metadata: dict = field(default_factory=dict)
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe joint metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "joint_type": self.joint_type,
            "parent_body_id": self.parent_body_id,
            "child_body_id": self.child_body_id,
            "axis": dict(self.axis),
            "origin": dict(self.origin),
            "limits": dict(self.limits),
            "constraint_metadata": dict(self.constraint_metadata),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create joint metadata from persisted data."""

        data = data or {}
        return MotionJoint(
            data.get("study_id", ""),
            data.get("name", "Motion Joint"),
            data.get("joint_type", "Custom Joint"),
            data.get("parent_body_id", ""),
            data.get("child_body_id", ""),
            dict(data.get("axis", {})),
            dict(data.get("origin", {})),
            dict(data.get("limits", {})),
            dict(data.get("constraint_metadata", {})),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class MotionDriver:
    """Time-dependent motion driver for a joint or rigid body."""

    study_id: str
    name: str
    driver_type: str
    target_id: str = ""
    function: dict = field(default_factory=dict)
    profile: dict = field(default_factory=dict)
    synchronization_group: str = ""
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe driver metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "driver_type": self.driver_type,
            "target_id": self.target_id,
            "function": dict(self.function),
            "profile": dict(self.profile),
            "synchronization_group": self.synchronization_group,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create driver metadata from persisted data."""

        data = data or {}
        return MotionDriver(
            data.get("study_id", ""),
            data.get("name", "Motion Driver"),
            data.get("driver_type", "Position Driver"),
            data.get("target_id", ""),
            dict(data.get("function", {})),
            dict(data.get("profile", {})),
            data.get("synchronization_group", ""),
            bool(data.get("enabled", True)),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class MotionMechanism:
    """Reusable mechanism library entry bound to a motion study."""

    study_id: str
    name: str
    mechanism_type: str
    body_ids: list = field(default_factory=list)
    joint_ids: list = field(default_factory=list)
    driver_ids: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self):
        """Return JSON-safe mechanism metadata."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "mechanism_type": self.mechanism_type,
            "body_ids": list(self.body_ids),
            "joint_ids": list(self.joint_ids),
            "driver_ids": list(self.driver_ids),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create mechanism metadata from persisted data."""

        data = data or {}
        return MotionMechanism(
            data.get("study_id", ""),
            data.get("name", "Mechanism"),
            data.get("mechanism_type", "Custom Mechanism"),
            list(data.get("body_ids", [])),
            list(data.get("joint_ids", [])),
            list(data.get("driver_ids", [])),
            dict(data.get("metadata", {})),
            data.get("id", str(uuid4())),
        )


@dataclass
class MotionAnimationSettings:
    """Animation timeline and playback metadata for motion results."""

    study_id: str
    duration: float = 1.0
    time_step: float = 0.1
    loop: bool = False
    playback_speed: float = 1.0
    keyframes: list = field(default_factory=list)
    camera_tracking_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe animation settings."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "duration": self.duration,
            "time_step": self.time_step,
            "loop": self.loop,
            "playback_speed": self.playback_speed,
            "keyframes": [dict(item) for item in self.keyframes],
            "camera_tracking_metadata": dict(self.camera_tracking_metadata),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create animation settings from persisted data."""

        data = data or {}
        return MotionAnimationSettings(
            data.get("study_id", ""),
            float(data.get("duration", 1.0)),
            float(data.get("time_step", 0.1)),
            bool(data.get("loop", False)),
            float(data.get("playback_speed", 1.0)),
            [dict(item) for item in data.get("keyframes", [])],
            dict(data.get("camera_tracking_metadata", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


@dataclass
class MotionExecutionRecord:
    """Execution history record for a motion study."""

    study_id: str
    result_id: str = ""
    report_id: str = ""
    status: str = "Pending"
    started_at: str = ""
    completed_at: str = ""
    diagnostics: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        """Return JSON-safe motion execution history."""

        return {
            "id": self.id,
            "study_id": self.study_id,
            "result_id": self.result_id,
            "report_id": self.report_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "diagnostics": dict(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(data):
        """Create motion execution history from persisted data."""

        data = data or {}
        return MotionExecutionRecord(
            data.get("study_id", ""),
            data.get("result_id", ""),
            data.get("report_id", ""),
            data.get("status", "Pending"),
            data.get("started_at", ""),
            data.get("completed_at", ""),
            dict(data.get("diagnostics", {})),
            data.get("id", str(uuid4())),
            dict(data.get("metadata", {})),
        )


class MechanismKinematicsSolver:
    """Rigid-body kinematic mechanism solver registered through SimulationWorkspace."""

    solver_type = "Rigid Body Mechanism Kinematics"
    compatible_study_types = ["Motion"]

    def solve(self, simulation_workspace, study):
        """Solve a motion study and return timeline, transforms and joint states."""

        started_at = self._timestamp()
        validation = self.validate(simulation_workspace, study)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

        bodies = [item for item in simulation_workspace.motion_rigid_bodies if item.study_id == study.id and not item.suppressed]
        joints = [item for item in simulation_workspace.motion_joints if item.study_id == study.id and item.enabled]
        drivers = [item for item in simulation_workspace.motion_drivers if item.study_id == study.id and item.enabled]
        mechanisms = [item for item in simulation_workspace.motion_mechanisms if item.study_id == study.id]
        animation = simulation_workspace.motion_animation_for(study) or MotionAnimationSettings(study.id)
        duration = max(float(animation.duration), 0.0)
        time_step = max(float(animation.time_step), 0.001)
        times = self._times(duration, time_step)
        body_by_id = {body.id: body for body in bodies}
        joint_states = []
        body_history = []
        previous_positions = {}

        for time_value in times:
            state = self._state_at(time_value, bodies, joints, drivers, body_by_id)
            joint_states.append({"time": time_value, "joints": state["joints"]})
            body_history.append({"time": time_value, "bodies": state["bodies"]})
            previous_positions = state["positions"]

        travel = self._travel(body_history)
        angular = self._angular_displacement(joint_states)
        velocity = self._velocity_metadata(body_history, time_step)
        acceleration = self._acceleration_metadata(velocity, time_step)
        constraint_status = self._constraint_status(joints, body_by_id)
        diagnostics = {
            "solver": self.solver_type,
            "started_at": started_at,
            "completed_at": self._timestamp(),
            "body_count": len(bodies),
            "joint_count": len(joints),
            "driver_count": len(drivers),
            "mechanism_count": len(mechanisms),
            "timeline_steps": len(times),
            "closed_loop_mechanism_metadata": any(item.mechanism_type in {"Four-Bar Linkage", "Gear Train", "Chain"} for item in mechanisms),
            "converged": all(item["valid"] for item in constraint_status),
            "constraint_error": max([item["error"] for item in constraint_status] or [0.0]),
        }
        statistics = {
            "joint_states": joint_states,
            "body_transforms": body_history[-1]["bodies"],
            "motion_history": body_history,
            "travel_distance": travel,
            "angular_displacement": angular,
            "velocity_metadata": velocity,
            "acceleration_metadata": acceleration,
            "constraint_status": constraint_status,
            "timeline_data": {"duration": duration, "time_step": time_step, "samples": times},
            "mechanism_summary": [item.to_dict() for item in mechanisms],
            "animation": animation.to_dict(),
        }
        report = self._report(study, bodies, joints, drivers, mechanisms, statistics, diagnostics)
        return {
            "result_type": "Motion Mechanism Result",
            "scalars": {
                "body_count": len(bodies),
                "joint_count": len(joints),
                "driver_count": len(drivers),
                "maximum_travel": max(travel.values() or [0.0]),
                "maximum_angular_displacement": max([abs(value) for value in angular.values()] or [0.0]),
                "constraint_error": diagnostics["constraint_error"],
            },
            "vectors": {
                "joint_states": joint_states,
                "body_transforms": body_history[-1]["bodies"],
                "motion_history": body_history,
                "timeline_data": statistics["timeline_data"],
                "constraint_status": constraint_status,
                "motion_trails": self._motion_trails(body_history),
            },
            "statistics": statistics,
            "reports": [report],
            "history": [{"event": "motion_mechanism_solve", "timestamp": diagnostics["completed_at"], "solver": self.solver_type}],
            "visualization_metadata": {
                "overlays": ["Joint Visualization", "Constraint Visualization", "Motion Trails", "Body Transforms", "Reference Frames", "Axes"],
                "timeline": {"play": True, "pause": True, "stop": True, "loop": animation.loop, "playback_speed": animation.playback_speed},
                "color_legends": {
                    "travel_distance": {"min": min(travel.values() or [0.0]), "max": max(travel.values() or [0.0])},
                    "constraint_error": {"min": 0.0, "max": diagnostics["constraint_error"]},
                },
            },
            "metadata": {"diagnostics": diagnostics, "recommendations": report["recommendations"], "last_positions": previous_positions},
            "diagnostics": diagnostics,
            "report": report,
        }

    def validate(self, simulation_workspace, study):
        """Validate a motion study before execution."""

        errors = []
        warnings = []
        if study is None:
            return {"valid": False, "errors": ["Motion study was not found."], "warnings": []}
        if study.study_type != "Motion":
            errors.append("Mechanism solver requires a Motion study.")
        bodies = [item for item in simulation_workspace.motion_rigid_bodies if item.study_id == study.id and not item.suppressed]
        joints = [item for item in simulation_workspace.motion_joints if item.study_id == study.id and item.enabled]
        if not bodies:
            errors.append("Motion study requires at least one active rigid body.")
        if not any(item.is_ground for item in bodies):
            warnings.append("Motion study has no ground body.")
        body_ids = {item.id for item in bodies}
        for joint in joints:
            if joint.joint_type not in MOTION_JOINT_TYPES:
                errors.append(f"Unsupported motion joint type: {joint.joint_type}")
            if joint.parent_body_id and joint.parent_body_id not in body_ids:
                errors.append(f"Joint {joint.name} references a missing parent body.")
            if joint.child_body_id and joint.child_body_id not in body_ids:
                errors.append(f"Joint {joint.name} references a missing child body.")
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _times(self, duration, time_step):
        count = int(duration / time_step)
        values = [round(index * time_step, 10) for index in range(count + 1)]
        if not values or values[-1] < duration:
            values.append(duration)
        return values

    def _state_at(self, time_value, bodies, joints, drivers, body_by_id):
        positions = {}
        body_states = {}
        joint_states = {}
        for body in bodies:
            frame = dict(body.reference_frame or {})
            positions[body.id] = {
                "x": float(frame.get("x", 0.0)),
                "y": float(frame.get("y", 0.0)),
                "z": float(frame.get("z", 0.0)),
                "rotation": float(frame.get("rotation", 0.0)),
            }
        for joint in joints:
            value = self._driver_value(joint, drivers, time_value)
            parent = positions.get(joint.parent_body_id, {"x": 0.0, "y": 0.0, "z": 0.0, "rotation": 0.0})
            child = positions.get(joint.child_body_id, dict(parent))
            axis = self._axis(joint.axis)
            if joint.joint_type in {"Revolute Joint", "Pin Joint", "Hinge Joint", "Gear Pair", "Cam"}:
                child["rotation"] = self._clamp(value, joint.limits)
                radius = float(joint.constraint_metadata.get("radius", 1.0))
                child["x"] = parent["x"] + radius * cos(child["rotation"])
                child["y"] = parent["y"] + radius * sin(child["rotation"])
                child["z"] = parent["z"]
            elif joint.joint_type in {"Prismatic Joint", "Slider Joint", "Rack & Pinion", "Belt", "Chain"}:
                travel = self._clamp(value, joint.limits)
                child["x"] = parent["x"] + axis["x"] * travel
                child["y"] = parent["y"] + axis["y"] * travel
                child["z"] = parent["z"] + axis["z"] * travel
            elif joint.joint_type == "Fixed Joint":
                child = dict(parent)
            else:
                child["x"] = parent["x"] + axis["x"] * value
                child["y"] = parent["y"] + axis["y"] * value
                child["z"] = parent["z"] + axis["z"] * value
            if joint.child_body_id:
                positions[joint.child_body_id] = child
            joint_states[joint.id] = {
                "name": joint.name,
                "joint_type": joint.joint_type,
                "position": value,
                "axis": axis,
                "parent_body_id": joint.parent_body_id,
                "child_body_id": joint.child_body_id,
            }
        for body in bodies:
            item = positions[body.id]
            body_states[body.id] = {
                "name": body.name,
                "translation": {"x": item["x"], "y": item["y"], "z": item["z"]},
                "rotation": {"z": item["rotation"]},
                "matrix_metadata": self._transform_metadata(item),
                "reference_frame": dict(body.reference_frame),
            }
        return {"positions": positions, "bodies": body_states, "joints": joint_states}

    def _driver_value(self, joint, drivers, time_value):
        value = float(joint.constraint_metadata.get("initial_position", 0.0))
        for driver in drivers:
            if driver.target_id != joint.id:
                continue
            amplitude = float(driver.function.get("amplitude", driver.profile.get("amplitude", 1.0)))
            offset = float(driver.function.get("offset", 0.0))
            frequency = float(driver.function.get("frequency", 1.0))
            rate = float(driver.function.get("rate", 1.0))
            mode = driver.function.get("type", "linear")
            if driver.driver_type == "Angular Motor":
                if mode == "sine":
                    value = offset + amplitude * sin(2.0 * pi * frequency * time_value)
                else:
                    value = offset + rate * time_value
            elif driver.driver_type in {"Linear Motor", "Velocity Driver"}:
                value = offset + rate * time_value
            elif driver.driver_type == "Position Driver":
                value = offset + amplitude
            elif driver.driver_type == "Servo":
                value = offset + amplitude * min(max(time_value, 0.0), 1.0)
        return value

    def _axis(self, axis):
        dx = float(axis.get("x", 1.0))
        dy = float(axis.get("y", 0.0))
        dz = float(axis.get("z", 0.0))
        length = sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        return {"x": dx / length, "y": dy / length, "z": dz / length}

    def _clamp(self, value, limits):
        minimum = limits.get("min")
        maximum = limits.get("max")
        if minimum is not None:
            value = max(float(minimum), value)
        if maximum is not None:
            value = min(float(maximum), value)
        return value

    def _transform_metadata(self, item):
        angle = item["rotation"]
        return {
            "translation": {"x": item["x"], "y": item["y"], "z": item["z"]},
            "rotation_z": angle,
            "cos": cos(angle),
            "sin": sin(angle),
        }

    def _travel(self, body_history):
        start = body_history[0]["bodies"]
        end = body_history[-1]["bodies"]
        travel = {}
        for body_id, item in end.items():
            first = start.get(body_id, item)["translation"]
            last = item["translation"]
            travel[body_id] = sqrt((last["x"] - first["x"]) ** 2 + (last["y"] - first["y"]) ** 2 + (last["z"] - first["z"]) ** 2)
        return travel

    def _angular_displacement(self, joint_states):
        first = joint_states[0]["joints"] if joint_states else {}
        last = joint_states[-1]["joints"] if joint_states else {}
        return {joint_id: last[joint_id]["position"] - first.get(joint_id, last[joint_id])["position"] for joint_id in last}

    def _velocity_metadata(self, body_history, time_step):
        if len(body_history) < 2:
            return {}
        velocity = {}
        for current, previous in zip(body_history[1:], body_history[:-1]):
            for body_id, item in current["bodies"].items():
                before = previous["bodies"][body_id]["translation"]
                after = item["translation"]
                speed = sqrt((after["x"] - before["x"]) ** 2 + (after["y"] - before["y"]) ** 2 + (after["z"] - before["z"]) ** 2) / max(time_step, 0.001)
                velocity.setdefault(body_id, []).append(speed)
        return {body_id: {"maximum": max(values), "average": sum(values) / max(len(values), 1)} for body_id, values in velocity.items()}

    def _acceleration_metadata(self, velocity, time_step):
        return {body_id: {"maximum": item["maximum"] / max(time_step, 0.001), "average": item["average"] / max(time_step, 0.001)} for body_id, item in velocity.items()}

    def _constraint_status(self, joints, body_by_id):
        status = []
        for joint in joints:
            valid = (not joint.parent_body_id or joint.parent_body_id in body_by_id) and (not joint.child_body_id or joint.child_body_id in body_by_id)
            status.append({"joint_id": joint.id, "name": joint.name, "valid": valid, "error": 0.0 if valid else 1.0})
        return status

    def _motion_trails(self, body_history):
        trails = {}
        for sample in body_history:
            for body_id, item in sample["bodies"].items():
                trails.setdefault(body_id, []).append({"time": sample["time"], **item["translation"]})
        return trails

    def _report(self, study, bodies, joints, drivers, mechanisms, statistics, diagnostics):
        recommendations = []
        if not any(body.is_ground for body in bodies):
            recommendations.append("Add or identify a ground body to improve mechanism reference stability.")
        if diagnostics["constraint_error"] > 0.0:
            recommendations.append("Review joints with missing body references before using motion results.")
        return {
            "id": str(uuid4()),
            "title": f"{study.name} Motion Engineering Report",
            "study_id": study.id,
            "study_summary": {"name": study.name, "motion_type": study.metadata.get("motion_type", "")},
            "rigid_body_summary": [item.to_dict() for item in bodies],
            "joint_summary": [item.to_dict() for item in joints],
            "constraint_summary": statistics["constraint_status"],
            "driver_summary": [item.to_dict() for item in drivers],
            "mechanism_summary": [item.to_dict() for item in mechanisms],
            "travel_summary": statistics["travel_distance"],
            "angular_motion": statistics["angular_displacement"],
            "timeline_summary": statistics["timeline_data"],
            "warnings": [],
            "recommendations": recommendations,
            "solver_statistics": diagnostics,
        }

    def _timestamp(self):
        return datetime.now(timezone.utc).isoformat()
