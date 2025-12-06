import json
from functools import lru_cache
from agents.quiz_generator.agent.factory import build_agent
from agents.quiz_generator.tools.create_blitz import create_blitz_quiz
from agents.quiz_generator.tools.create_mini import create_mini_quiz
from agents.quiz_generator.tools.create_full import create_full_quiz


# Singleton agent
@lru_cache(maxsize=1)
def get_agent():
    return build_agent()


agent = get_agent()


def blitz(topic: str):
    """
    Generate a blitz quiz for a given C topic.
    """
    result = create_blitz_quiz.invoke({
        "topic": topic
    })

    result = json.loads(result)
    if not result.get("quiz_title"):
        return {"success": False, "error": result.get("error")}

    return result


def mini(topic: str):
    """
    Generate a mini quiz for a given C topic.
    """
    result = create_mini_quiz.invoke({
        "topic": topic
    })

    result = json.loads(result)
    if not result.get("quiz_title"):
        return {"success": False, "error": result.get("error")}

    return result


def full(topic: str):
    """
    Generate a full quiz for a given C topic.
    """
    result = create_full_quiz.invoke({
        "topic": topic,
    })

    result = json.loads(result)
    if not result.get("quiz_title"):
        return {"success": False, "error": result.get("error")}

    return result
