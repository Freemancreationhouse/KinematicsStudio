import os
import tempfile

from engine.annotations3d import ReviewItem
from engine.bcf import BCFComment, BCFProject, BCFSnapshot, BCFTopic, BCFViewpoint
from engine.clashes import ClashResult
from engine.collaboration import Issue
from engine.geometry import Vector3
from engine.references3d import ReferenceInstance, ReferenceModel
from engine.workspace.workspace import Workspace


class DummyCamera:
    def __init__(self):

        self.position = Vector3(10.0, 20.0, 30.0)
        self.target = Vector3(1.0, 2.0, 3.0)
        self.up = Vector3(0.0, 0.0, 1.0)


workspace = Workspace()
camera = DummyCamera()
project = BCFProject("Coordination")
workspace.bcf_manager.add_project(project)

clash = ClashResult("Hard Clash", "Pipe hits duct", location=Vector3(1.0, 2.0, 3.0))
issue = Issue("Issue A", "Resolve clash", position=Vector3(2.0, 3.0, 4.0))
review = ReviewItem("Review A")
model = ReferenceModel("Architectural", path="arch.obj")
reference = ReferenceInstance(model.id, "Architectural Instance")

workspace.clash_manager.add_result(clash)
workspace.issue_manager.add(issue)
workspace.review_manager.add(review)
workspace.reference_manager.add_model(model)
workspace.reference_manager.add_instance(reference)

clash_topic = workspace.bcf_manager.create_topic_from_clash(clash, camera)
issue_topic = workspace.bcf_manager.create_topic_from_issue(issue, camera)
review_topic = workspace.bcf_manager.create_topic_from_review(review, camera)
reference_topic = workspace.bcf_manager.create_topic_from_reference(reference, camera)

clash_topic.add_comment(BCFComment("Coordinate with MEP", "Coordinator"))
clash_topic.add_snapshot(BCFSnapshot("Marked View", "snapshot.png"))
clash_topic.add_viewpoint(BCFViewpoint("Alternate", Vector3(4.0, 5.0, 6.0)))

assert clash_topic.linked_clash_id == clash.id
assert issue_topic.linked_issue_id == issue.id
assert review_topic.linked_review_id == review.id
assert reference_topic.linked_reference_id == reference.id
assert len(workspace.bcf_manager.visible_topics()) == 4
assert clash_topic in workspace.visible_bcf_topics()
assert clash_topic in workspace.selectable_3d_entities()

selected = workspace.bcf_manager.sync_selection(workspace, clash_topic)
assert selected == [clash]
assert clash.selected is True

camera.position = Vector3()
restored = workspace.bcf_manager.restore_viewpoint(clash_topic, camera)
assert restored is not None
assert camera.position.x == 10.0

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "coordination.bcf")
    workspace.bcf_manager.export_bcf(path)
    assert os.path.exists(path)

    imported_workspace = Workspace()
    imported = imported_workspace.bcf_manager.import_bcf(path)
    assert imported.name == "Coordination"
    assert imported_workspace.bcf_manager.get_topic("Hard Clash") is not None

topic = BCFTopic("Manual", "Manual BCF topic")
topic.add_viewpoint(BCFViewpoint())
data = topic.to_dict()
restored_topic = BCFTopic.from_dict(data)
assert restored_topic.title == topic.title
assert restored_topic.viewpoints[0].name == "Viewpoint"

print("3d-bcf-manager-ok")
