# [2507] n8
#

import json, os, requests


def generate_questions():
    """ Generate random questions, if unable to do so will return default questions. """

    project=os.environ["GOOGLE_CLOUD_PROJECT"]
    url = "https://" + project + ".uc.r.appspot.com/random_questions"

    defaults = (
        "How many districts are there in the California community college system?",
        "What is the part-time enrollment of Foothill College?",
        "What college is designated a Center of Excellence in bioprocessing?",
        "How many California community colleges partner with the California " +
            "Department of Corrections and Rehabilitation (CDCR) to provide in‑person courses?",
        "What are the responsibilities of the board members of a California community college?"
    )
    questions = []
    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            for question in data["questions"]:
                questions.append(question)
        else:
            questions = defaults

    except requests.exceptions.RequestException as e:
        questions = defaults

    return questions
