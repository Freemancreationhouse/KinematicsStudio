from engine.collaboration import Participant
from engine.workspace import Workspace


workspace = Workspace("3D Collaboration Workspace")
manager = workspace.collaboration_manager
session = manager.create_session("Coordination", owner="Lead", notes="Initial review")
participant = Participant("Reviewer", "Coordinator", "reviewer@example.com")
session.add_participant(participant)
session.add_note("Check model", "Lead")
session.tags.append("coordination")

assert manager.active is session
assert session.metadata.owner == "Lead"
assert session.participants[0].name == "Reviewer"
assert manager.search("model") == [session]
assert manager.filter(status="Active") == [session]
assert manager.filter(tag="coordination") == [session]

manager.archive(session)
assert session.status == "Archived"
manager.restore(session)
assert session.status == "Active"

duplicate = manager.duplicate(session, "Coordination Copy")
assert duplicate.name == "Coordination Copy"
assert duplicate.notes == session.notes

data = manager.to_dict()
restored = Workspace("Restored Collaboration Workspace").collaboration_manager
restored.from_dict(data)
assert restored.active.name == "Coordination"
assert restored.get("Coordination Copy") is not None

print("3d-collaboration-manager-ok")
