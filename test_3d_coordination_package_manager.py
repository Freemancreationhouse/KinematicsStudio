from engine.bcf import BCFTopic
from engine.clashes import ClashResult
from engine.collaboration import Issue
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.model_compare import RevisionMetadata
from engine.coordination_package import PackageMetadata
from engine.workspace.workspace import Workspace


workspace = Workspace()
entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Package Box")
entity.id = "package-box"
workspace.add_3d_entity(entity)

model = workspace.reference_manager.create_model("Coordination Reference", "coordination.obj")
topic = BCFTopic("Package Topic", "Package BCF data")
workspace.bcf_manager.add_topic(topic)
workspace.clash_manager.add_result(ClashResult("Hard Clash", location=Vector3(1.0, 2.0, 3.0)))
workspace.issue_manager.add(Issue("Package Issue", position=Vector3(4.0, 5.0, 6.0)))
workspace.review_manager.create("Package Review")
revision = workspace.revision_manager.capture_revision(
    "Package Revision",
    workspace,
    RevisionMetadata("Reviewer", "Native", "Delivery revision", ("delivery",), ()),
)
workspace.revision_manager.compare_revisions(revision, revision)

package = workspace.coordination_package_manager.create_delivery_package(
    "Delivery Package",
    workspace,
    PackageMetadata("Author", "Recipient", "Final delivery package", "1.1", "Ready"),
)

assert package in workspace.coordination_package_manager.packages
assert package.manifest.summary["references"] == 1
assert package.manifest.summary["bcf_topics"] == 1
assert package.manifest.summary["clashes"] == 1
assert package.manifest.summary["revisions"] == 1
assert package.statistics.issues == 1
assert package.statistics.reviews == 1
assert package.validation.valid is True
assert workspace.coordination_package_manager.archive_summary()["archives"] == 1
assert workspace.coordination_package_manager.search_archives("delivery")

model.status = "Missing"
validation = workspace.coordination_package_manager.validate_package(package, workspace)
assert validation.valid is False
assert validation.errors

print("3d-coordination-package-manager-ok")
