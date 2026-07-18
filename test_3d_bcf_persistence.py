import os
import tempfile

from engine.bcf import BCFComment, BCFTopic, BCFViewpoint
from engine.cad.application import CADApplication
from engine.geometry import Vector3


app = CADApplication()
topic = BCFTopic("Persisted Topic", "BCF project persistence")
topic.status = "In Review"
topic.priority = "High"
topic.add_comment(BCFComment("Keep this comment", "Reviewer"))
topic.add_viewpoint(
    BCFViewpoint("Saved Camera", Vector3(10.0, 20.0, 30.0), Vector3(3.0, 4.0, 5.0))
)
app.workspace.bcf_manager.add_topic(topic)
app.workspace.selection.select(topic)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bcf_project.ksproj")
    app.save_project(path)

    opened = CADApplication()
    workspace = opened.open_project(path)
    restored = workspace.bcf_manager.get_topic("Persisted Topic")

    assert restored is not None
    assert restored.status == "In Review"
    assert restored.priority == "High"
    assert restored.comments[0].text == "Keep this comment"
    assert restored.viewpoints[0].name == "Saved Camera"
    assert restored.selected is True

print("3d-bcf-persistence-ok")
