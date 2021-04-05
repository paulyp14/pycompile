

class SemanticError(Exception):
    pass


class SemanticWarning(Warning):
    pass


class InheritanceError(Exception):
    def __init__(self, inherit_name: str):
        super().__init__()
        self.inherit_name: str = inherit_name
