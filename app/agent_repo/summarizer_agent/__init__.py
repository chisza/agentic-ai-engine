from .agent import summarizer_agent

# adk web / AgentLoader looks for `root_agent` in the package
root_agent = summarizer_agent

__all__ = ["summarizer_agent", "root_agent"]
