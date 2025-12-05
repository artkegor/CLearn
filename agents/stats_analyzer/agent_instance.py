from functools import lru_cache
from agents.stats_analyzer.agent.create_agent import build_agent
from agents.stats_analyzer.tools.brief_summary import brief_summary_tool
from agents.stats_analyzer.tools.detailed_summary import detailed_summary_tool


# Singleton pattern to get the agent instance
@lru_cache(maxsize=1)
def get_agent():
    return build_agent()


agent = get_agent()


def brief_summary(user_data: str):
    """
    Function to get a brief summary of user statistics.
    """
    result = brief_summary_tool.invoke({
        "user_data": user_data
    })

    if not result.get("success"):
        return {"success": False, "error": result.get("error")}
    result = result["summary"]

    return result


def detailed_summary(user_data: str):
    """
    Function to get a detailed summary of user statistics.
    """
    result = detailed_summary_tool.invoke({
        "user_data": user_data
    })

    if not result.get("success"):
        return {"success": False, "error": result.get("error")}
    result = result["summary"]

    return result
