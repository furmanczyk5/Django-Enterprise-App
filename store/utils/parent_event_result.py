class ParentEventResult(object):
    def __init__(self):
        self.parent_event = None

    def set_parent_event(self, parent_event):
        self.parent_event = parent_event

    def has_parent_event(self):
        return True if self.parent_event else False

    def get_parent_event(self):
        return self.parent_event
