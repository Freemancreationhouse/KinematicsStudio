from engine.commands.command import Command
from engine.entities import MeshEntity
from engine.geometry import Matrix4, PrimitiveGenerator, Vector3


class CreatePrimitiveCommand(Command):
    """Create a generated 3D primitive through the existing command system."""

    def __init__(
        self,
        workspace,
        primitive_type,
        parameters=None,
        position=None,
        display_mode="wireframe",
        name=None,
    ):

        self.workspace = workspace
        self.primitive_type = str(primitive_type)
        self.parameters = dict(parameters or {})
        self.position = position or Vector3()
        self.display_mode = display_mode
        self.entity_name = name or f"{self.primitive_type.title()} Primitive"
        self.entity = self._create_entity()

    # --------------------------------

    def execute(self):
        """Add the primitive entity to the workspace 3D scene."""

        if self.entity not in self.workspace.scene3d.entities():
            self.workspace.add_3d_entity(self.entity)

        self.workspace.selection.select(self.entity)

    # --------------------------------

    def undo(self):
        """Remove the primitive entity from the workspace 3D scene."""

        self.workspace.remove_3d_entity(self.entity)

    # --------------------------------

    def preview_entity(self):
        """Return a detached preview entity for interactive tools."""

        return self._create_entity()

    # --------------------------------

    def _create_entity(self):

        mesh = PrimitiveGenerator.generate(self.primitive_type, **self.parameters)
        entity = MeshEntity(
            mesh,
            name=self.entity_name,
            display_mode=self.display_mode,
            primitive_type=self.primitive_type,
            parameters=self.parameters,
        )
        entity.set_transform_state(position=self.position)

        return entity
