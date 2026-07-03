class AppContext:

    def __init__(self):

        self.project = None
        self.canvas = None
        self.tool_manager = None
        self.workspace = None

        self.settings = {}

    # ------------------------------------

    def initialize(

        self,

        project,

        canvas,

        tool_manager,

        workspace=None,

    ):

        self.project = project
        self.canvas = canvas
        self.tool_manager = tool_manager
        self.workspace = workspace


app = AppContext()