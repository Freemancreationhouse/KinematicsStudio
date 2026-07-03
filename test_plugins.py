from engine.core import plugins


class TestPlugin:

    def run(self):

        return "Plugin Loaded"


plugins.register("test", TestPlugin())

print(

    plugins.get("test").run()

)