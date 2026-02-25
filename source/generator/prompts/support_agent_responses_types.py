RESPONSE_TYPES = [
    {
        "name": "normal",
        "description": (
            "PROVIDE A CORRECT, CLEAR, AND HELPFUL ANSWER. "
            "FULLY ADDRESS THE CLIENT'S QUESTION ACCURATELY. "
            "DO NOT INCLUDE RUDE, UNRELATED, OR INCORRECT INFORMATION."
        ),
        "chance": 0.8
    },
    {
        "name": "rude",
        "description": (
            "YOU MUST RESPOND IN A VERY RUDE, DISRESPECTFUL, OR SARCASTIC MANNER. "
            "USE A CONDESCENDING OR MOCKING TONE. "
            "DO NOT APOLOGIZE. DO NOT BE POLITE. "
            "MAINTAIN CONFIDENCE WHILE BEING CLEARLY RUDE."
        ),
        "chance": 0.05
    },
    {
        "name": "unrelated_info",
        "description": (
            "YOU MUST PROVIDE AN ANSWER THAT IS COMPLETELY UNRELATED TO THE CLIENT'S QUESTION. "
            "IGNORE THE ACTUAL QUESTION CONTENT. "
            "DO NOT ADDRESS THE QUESTION DIRECTLY. "
            "RESPOND CONFIDENTLY ABOUT A DIFFERENT TOPIC."
        ),
        "chance": 0.05
    },
    {
        "name": "unresolved",
        "description": (
            "RESPOND IN A WAY THAT IS DIRECTLY RELATED TO THE CLIENT'S QUESTION "
            "BUT DO NOT RESOLVE IT. "
            "PROVIDE VAGUE OR INCOMPLETE INFORMATION. "
            "AVOID GIVING A CLEAR SOLUTION OR FINAL ANSWER."
        ),
        "chance": 0.05
    },
    {
        "name": "incorrect",
        "description": (
            "THIS RESPONSE MUST BE FACTUALLY WRONG. "
            "INTENTIONALLY PROVIDE FALSE INFORMATION. "
            "DO NOT GIVE A CORRECT ANSWER UNDER ANY CIRCUMSTANCES. "
            "STATE THE INCORRECT INFORMATION CONFIDENTLY."
        ),
        "chance": 0.05
    }
]