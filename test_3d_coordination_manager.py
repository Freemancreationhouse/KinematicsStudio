from engine.geometry import Vector3
from engine.references3d import CoordinationManager


manager = CoordinationManager()
manager.model_alignment("ref-1", "Shared")
manager.origin_alignment("ref-1", Vector3(1.0, 2.0, 3.0))
manager.coordinate_mapping("WCS", "UCS-1")
manager.reference_offset("ref-1", Vector3(10.0, 0.0, 0.0))
manager.reference_rotation("ref-1", Vector3(0.0, 0.0, 90.0))
manager.reference_scale("ref-1", Vector3(2.0, 2.0, 2.0))
manager.conflict_placeholder("Future clash detection placeholder")

assert len(manager.rules) == 6
assert manager.rules[0].rule_type == "Model Alignment"
assert manager.rules[-1].settings["scale"]["x"] == 2.0
assert manager.conflicts[0]["status"] == "Placeholder"

restored = CoordinationManager()
restored.from_dict(manager.to_dict())

assert restored.rules[1].settings["origin"]["z"] == 3.0
assert restored.conflicts[0]["description"] == "Future clash detection placeholder"

print("3d-coordination-manager-ok")
