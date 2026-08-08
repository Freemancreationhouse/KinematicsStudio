from __future__ import annotations

from engine.topology.body import Body
from engine.topology.edge import Edge
from engine.topology.events import TopologyEvents
from engine.topology.face import Face
from engine.topology.loop import Loop
from engine.topology.shell import Shell
from engine.topology.vertex import Vertex


class TopologyManager:
    """Registry for persistent topology metadata without topology algorithms."""

    def __init__(self) -> None:
        """Create an empty topology manager."""

        self.events = TopologyEvents()
        self._bodies: dict[str, Body] = {}
        self._shells: dict[str, Shell] = {}
        self._faces: dict[str, Face] = {}
        self._loops: dict[str, Loop] = {}
        self._edges: dict[str, Edge] = {}
        self._vertices: dict[str, Vertex] = {}

    def add_body(self, body: Body) -> Body:
        """Register a body metadata record."""

        self._bodies[str(body.id)] = body
        self.events.emit("TopologyBodyAdded", str(body.id), {"body": body})
        return body

    def add_shell(self, shell: Shell) -> Shell:
        """Register a shell metadata record."""

        self._shells[str(shell.id)] = shell
        self.events.emit("TopologyShellAdded", str(shell.id), {"shell": shell})
        return shell

    def add_face(self, face: Face) -> Face:
        """Register a face metadata record."""

        self._faces[str(face.id)] = face
        self.events.emit("TopologyFaceAdded", str(face.id), {"face": face})
        return face

    def add_loop(self, loop: Loop) -> Loop:
        """Register a loop metadata record."""

        self._loops[str(loop.id)] = loop
        self.events.emit("TopologyLoopAdded", str(loop.id), {"loop": loop})
        return loop

    def add_edge(self, edge: Edge) -> Edge:
        """Register an edge metadata record."""

        self._edges[str(edge.id)] = edge
        self.events.emit("TopologyEdgeAdded", str(edge.id), {"edge": edge})
        return edge

    def add_vertex(self, vertex: Vertex) -> Vertex:
        """Register a vertex metadata record."""

        self._vertices[str(vertex.id)] = vertex
        self.events.emit("TopologyVertexAdded", str(vertex.id), {"vertex": vertex})
        return vertex

    def body(self, body_id: str) -> Body | None:
        """Return a body by persistent topology id."""

        return self._bodies.get(str(body_id))

    def bodies(self) -> tuple[Body, ...]:
        """Return all registered bodies."""

        return tuple(self._bodies.values())

    def remove_body(self, body_id: str) -> Body | None:
        """Remove a body metadata record."""

        body = self._bodies.pop(str(body_id), None)
        if body is not None:
            self.events.emit("TopologyBodyRemoved", str(body.id), {"body": body})
        return body

    def clear(self) -> None:
        """Clear all topology metadata."""

        self._bodies.clear()
        self._shells.clear()
        self._faces.clear()
        self._loops.clear()
        self._edges.clear()
        self._vertices.clear()
        self.events.emit("TopologyCleared", "", {})
