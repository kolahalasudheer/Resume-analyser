"""
State Manager for AI Engine
"""

class AIStateManager:
    """Manages state for AI conversations or context"""
    def __init__(self):
        self.context = {}
        
    def update(self, key, value):
        self.context[key] = value
        
    def get(self, key):
        return self.context.get(key)
