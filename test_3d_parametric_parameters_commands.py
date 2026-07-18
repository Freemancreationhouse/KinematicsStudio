from engine.commands import AddParametricParameterCommand
from engine.product import ComputedParameter, Expression, ExpressionBinding, GlobalParameter, ParameterCategory
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager

category = ParameterCategory("Command Parameters", "Float")
source = GlobalParameter("Command Source", 1.0)
target = ComputedParameter("Command Target", 0.0)
expression = Expression("Command Expression", "Command Source")
binding = ExpressionBinding("Command Binding", source.id, target.id, "ParameterToParameter", expression.id)

for item in (category, source, target, expression, binding):
    workspace.command_manager.execute(AddParametricParameterCommand(workspace, item))

assert manager.parameter_categories == [category]
assert manager.parameters == [source, target]
assert manager.expressions == [expression]
assert manager.expression_bindings == [binding]
assert binding.id in source.binding_ids
assert binding.id in expression.binding_ids

workspace.command_manager.undo()
assert manager.expression_bindings == []
workspace.command_manager.redo()
assert manager.expression_bindings == [binding]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.expression_bindings == []
assert manager.expressions == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.expressions == [expression]
assert manager.expression_bindings == [binding]

print("3d-parametric-parameters-commands-ok")
