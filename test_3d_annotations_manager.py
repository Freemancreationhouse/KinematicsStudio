from engine.annotations3d import MARKUP_TYPES
from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Annotation Workspace")
manager = workspace.annotation_manager3d

text = manager.text_note("Check clearance", Vector3(1.0, 2.0, 3.0))
assert text.annotation_type == "Text Note"
assert text.text == "Check clearance"
assert text.screen_space is False

screen = manager.create("Text Note", "Screen label", [Vector3(10.0, 20.0, 0.0)], True)
assert screen.screen_space is True

callout = manager.callout("Look here", [Vector3(), Vector3(10.0, 0.0, 0.0)])
arrow = manager.arrow([Vector3(), Vector3(0.0, 10.0, 0.0)])
cloud = manager.cloud([Vector3(), Vector3(1.0, 0.0, 0.0), Vector3(1.0, 1.0, 0.0)])
highlight = manager.highlight([Vector3(), Vector3(2.0, 0.0, 0.0)])
freehand = manager.freehand_sketch([Vector3(), Vector3(1.0, 1.0, 0.0)])
marker = manager.marker("A", Vector3())
pinned = manager.pinned_note("Pinned", Vector3())
revision = manager.revision_marker("R1", Vector3())
tag = manager.review_tag("QA", Vector3())

created_types = {
    item.annotation_type for item in (
        text, callout, arrow, cloud, highlight, freehand, marker, pinned, revision, tag
    )
}
assert set(MARKUP_TYPES).issubset(created_types)
assert len(cloud.segments()) == 3
assert len(manager.visible_annotations()) == 11

data = manager.to_dict()
restored = Workspace("Restored Annotation Workspace").annotation_manager3d
restored.from_dict(data)
assert len(restored.annotations) == 11
assert restored.annotations[0].text == "Check clearance"

print("3d-annotations-manager-ok")
