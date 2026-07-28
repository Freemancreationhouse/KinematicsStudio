class AIContextEngine:
    """Builds AI context exclusively from the existing Workspace."""

    def build(self, workspace, include_history=True):
        """Return a JSON-safe context snapshot for AI providers."""

        product = getattr(workspace, "product_manager", None)
        selection = getattr(workspace, "selection", None)
        scene = getattr(workspace, "scene3d", None)
        command_manager = getattr(workspace, "command_manager", None)
        selected = list(getattr(selection, "selected", [])) if selection is not None else []
        context = {
            "workspace": self.workspace_context(workspace),
            "project": self.project_context(workspace),
            "selection": self.selection_context(selected),
            "visible_objects": self.visible_object_context(workspace),
            "layers": self.layer_context(workspace),
            "materials": self.material_context(product),
            "viewport": self.viewport_context(workspace),
            "units": self.unit_context(workspace),
            "document_settings": self.document_settings_context(workspace),
            "properties": self.property_context(selected),
            "history": self.history_context(command_manager) if include_history else {},
        }
        if product is not None:
            context.update({
                "features": self.feature_context(product),
                "bodies": self.body_context(product),
                "dependencies": self.dependency_context(product),
            })
        if scene is not None:
            context["scene"] = {"entities_3d": len(scene.entities())}
        return context

    def workspace_context(self, workspace):
        """Return workspace-level context."""

        return {
            "name": getattr(workspace, "name", ""),
            "entities_2d": len(getattr(workspace, "entities", [])),
            "layers": getattr(getattr(workspace, "layer_manager", None), "count", 0),
            "settings_keys": sorted((getattr(workspace, "project_settings", {}) or {}).keys()),
        }

    def project_context(self, workspace):
        """Return project metadata from Workspace settings."""

        settings = getattr(workspace, "project_settings", {}) or {}
        return {
            "template": settings.get("template", ""),
            "runtime_configuration": (settings.get("runtime", {}) or {}).get("configuration", ""),
        }

    def selection_context(self, selected):
        """Return selected object metadata."""

        return [
            {
                "id": getattr(item, "id", ""),
                "name": getattr(item, "name", ""),
                "type": getattr(item, "type_name", item.__class__.__name__),
            }
            for item in selected
        ]

    def property_context(self, selected):
        """Return common selected object properties."""

        return [
            {
                "visible": getattr(item, "visible", None),
                "locked": getattr(item, "locked", None),
                "layer": getattr(item, "layer_name", ""),
            }
            for item in selected
        ]

    def visible_object_context(self, workspace):
        """Return visible 2D and 3D object metadata without mutating project data."""

        visible_2d = workspace.visible_entities() if hasattr(workspace, "visible_entities") else []
        visible_3d = workspace.visible_3d_entities() if hasattr(workspace, "visible_3d_entities") else []
        return [
            {
                "id": getattr(item, "id", ""),
                "name": getattr(item, "name", ""),
                "type": getattr(item, "type_name", item.__class__.__name__),
                "layer": getattr(item, "layer_name", ""),
            }
            for item in list(visible_2d) + list(visible_3d)
        ]

    def layer_context(self, workspace):
        """Return layer metadata for AI context."""

        manager = getattr(workspace, "layer_manager", None)
        return [
            {
                "name": getattr(layer, "name", ""),
                "visible": getattr(layer, "visible", True),
                "locked": getattr(layer, "locked", False),
                "color": getattr(layer, "color", ""),
            }
            for layer in getattr(manager, "layers", [])
        ]

    def material_context(self, product):
        """Return ProductManager material metadata."""

        if product is None:
            return []
        return [
            {
                "id": getattr(material, "id", ""),
                "name": getattr(material, "name", ""),
                "category": getattr(material, "category", ""),
            }
            for material in getattr(product, "engineering_materials", [])
        ]

    def viewport_context(self, workspace):
        """Return viewport metadata available from the shared Workspace."""

        return {
            "view_states": len(getattr(getattr(workspace, "view_state_manager", None), "states", [])),
            "display_mode": getattr(getattr(workspace, "display_mode_manager", None), "current_mode", ""),
            "visual_style": getattr(getattr(getattr(workspace, "visual_style_manager", None), "current", None), "name", ""),
        }

    def unit_context(self, workspace):
        """Return unit metadata from project settings."""

        settings = getattr(workspace, "project_settings", {}) or {}
        return settings.get("units", {"length": "mm", "angle": "deg"})

    def document_settings_context(self, workspace):
        """Return JSON-safe project document settings."""

        settings = getattr(workspace, "project_settings", {}) or {}
        return {
            key: value
            for key, value in settings.items()
            if key not in {"ai_studio"} and isinstance(value, (str, int, float, bool, dict, list, tuple, type(None)))
        }

    def feature_context(self, product):
        """Return feature metadata from ProductManager."""

        return [
            {
                "id": feature.id,
                "name": feature.name,
                "type": getattr(feature, "feature_type", ""),
                "status": getattr(getattr(feature, "metadata", None), "status", ""),
                "body_id": getattr(getattr(feature, "result", None), "body_id", ""),
            }
            for feature in getattr(product, "features", [])
        ]

    def body_context(self, product):
        """Return body metadata from ProductManager."""

        return [
            {
                "id": body.id,
                "name": body.name,
                "part_id": getattr(body, "part_id", ""),
                "mesh_entity_id": getattr(body, "mesh_entity_id", ""),
                "features": list(getattr(body, "feature_ids", [])),
            }
            for body in getattr(product, "bodies", [])
        ]

    def dependency_context(self, product):
        """Return dependency graph metadata from ProductManager."""

        return {
            "graphs": len(getattr(product, "dependency_graphs", [])),
            "nodes": len(getattr(product, "dependency_nodes", [])),
            "edges": [
                {
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "relationship": edge.relationship,
                }
                for edge in getattr(product, "dependency_edges", [])
            ],
        }

    def history_context(self, command_manager):
        """Return undo/redo history metadata."""

        if command_manager is None:
            return {}
        return {
            "undo_count": getattr(command_manager, "undo_count", 0),
            "redo_count": getattr(command_manager, "redo_count", 0),
            "commands": [getattr(command, "name", command.__class__.__name__) for command in command_manager.history()],
        }
