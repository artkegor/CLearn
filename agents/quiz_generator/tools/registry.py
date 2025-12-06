from agents.quiz_generator.tools.get_c_knowledge import get_c_knowledge
from agents.quiz_generator.tools.create_blitz import create_blitz_quiz
from agents.quiz_generator.tools.create_mini import create_mini_quiz
from agents.quiz_generator.tools.create_full import create_full_quiz

TOOLS = [
    get_c_knowledge,
    create_blitz_quiz,
    create_mini_quiz,
    create_full_quiz
]