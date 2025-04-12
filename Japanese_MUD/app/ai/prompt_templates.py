"""
Templates for AI prompt generation
These templates are used to generate prompts for the OpenAI API
"""

# Template for generating location descriptions
LOCATION_DESCRIPTION_TEMPLATE = """
Create a vivid description of a {setting} in Japan. The description should naturally incorporate 
the Japanese word "{word}" (meaning: {meaning}) in a way that makes its meaning clear from context.
The description should be about 3-4 sentences long and immersive.
"""

# Template for generating NPC dialogue
NPC_DIALOGUE_TEMPLATE = """
Write a short dialogue from a {npc_type} character who uses the Japanese word "{word}" 
(meaning: {meaning}) in their speech. Make the meaning of the word clear from context.
"""

# Template for generating item descriptions
ITEM_DESCRIPTION_TEMPLATE = """
Describe a {item_type} found in Japan that relates to the word "{word}" (meaning: {meaning}). 
Make the description help the player understand the meaning of the word.
"""

# Template for help text
HELP_TEXT_TEMPLATE = """
You are playing a Japanese language learning text adventure game. Available commands:
- look: examine your surroundings
- move (north/south/east/west/up/down): travel in a direction
- take/drop [item]: pick up or drop items
- talk/say [text]: communicate with NPCs
- use/give/open/close [item]: interact with objects
- eat/drink [item]: consume food or drinks
- inventory: check what you're carrying
- help: show this message

As you explore, you'll encounter Japanese vocabulary words. Try to understand them from context, 
and use them when you can!
"""

# Template for generating game intro
GAME_INTRO_TEMPLATE = """
Create an engaging introduction to a Japanese language learning adventure game. The player is 
starting their journey in {starting_location}, Japan. Use simple Japanese vocabulary appropriate 
for beginners (JLPT N5 level).
"""

# Template for vocabulary explanation
VOCABULARY_EXPLANATION_TEMPLATE = """
Explain the Japanese word "{word}" (meaning: {meaning}) in a simple way that a beginner would 
understand. Include an example sentence using the word in context.
""" 