from .agent import greeting_agent

# adk web / adk eval look for root_agent in the package
root_agent = greeting_agent

__all__ = ["greeting_agent", "root_agent"]
