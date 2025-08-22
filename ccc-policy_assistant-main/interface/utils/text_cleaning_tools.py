# © 2025 Numantic Solutions LLC
# MIT License
#
# Tools for cleaning text

import re
import json


def clean_web_texts(web_texts: list) -> str:
    '''
    Method to clean the webpage text often found in ptag components. This method
    takes a list of texts and returns a single string of cleaned texts joined together.

    To use it with a single string, pass the string in a list.

     Args:
        web_texts: A list of texts to be cleaned

    Returns:
        A single string of concatenated cleaned texts
    '''

    # remove unwanted characters
    pats = [r"\n|\xa0", r"\s+", r"\[\d+]", r"\[…]", r"\s{2,}", r"\||>|/"]

    ptag_text = " ".join(web_texts)
    for pat in pats:
        ptag_text = re.sub(pat, " ", ptag_text)

    ptag_text = ptag_text.strip()

    return ptag_text

def clean_contents(intext: str):
    """
    Cleans a given text by removing patterns and stripping extra whitespace.

    This function takes a string input, removes specific patterns defined in the
    list, and eliminates leading and trailing whitespaces. The cleaned text is
    then returned.

    Parameters:
        intext (str): The input string that needs to be cleaned.

    Returns:
        str: The cleaned string with specified patterns removed and extra
        whitespace stripped.
    """

    pats = [r"\[\d+]"]

    for pat in pats:
        intext = re.sub(pat, "", intext)

    intext = intext.strip()

    return intext

def replace_phrases(text: str,
                    phrases: dict) -> str:
    """
    Replace multiple phrases in a text using a dictionary of phrase mappings.

    This function performs a text substitution using regular expressions, replacing
    occurrences of each key in the phrases dictionary with its corresponding value.

    Args:
        text (str): The input text where phrases will be replaced
        phrases (dict): A dictionary where keys are phrases to find and values are
                       their replacements

    Returns:
        str: The text with all specified phrases replaced

    Examples:
        >>> text = "Hello @user1 and @user2"
        >>> phrases = {"@user1": "#John#", "@user2": "#Jane#"}
        >>> replace_phrases(text, phrases)
        'Hello #John# and #Jane#'
    """

    for r in phrases:
        pat = "{}".format(r)

        text = re.sub(pat, phrases[r], text)

    return text

def get_text_between_phrases(text: str,
                             start_string: str,
                             end_string: str) -> str:
    """
    Extracts all substrings between specified start and end phrases from the given text.

    The function uses regular expressions to find all non-overlapping substrings
    that are delimited by the provided start and end strings. Non-greedy matching
    is employed to ensure the smallest possible substring is captured between these
    phrases. Escaped characters are handled appropriately to avoid unintended
    effects caused by special regular expression characters in the input.

    Parameters:
    text: str
        The full text in which substrings are to be extracted.
    start_string: str
        The phrase indicating the start of a substring to extract.
    end_string
        The phrase indicating the end of a substring to extract.

    Returns:
    str
        A list of all substrings found between the provided start
        and end phrases.
    """

    # Escape the start and end strings to handle potential regex special characters
    escaped_start = re.escape(start_string)
    escaped_end = re.escape(end_string)

    # Construct the regex pattern with a non-greedy capture group
    pattern = rf"{escaped_start}(.*?){escaped_end}"

    # Find all occurrences
    all_matches = re.findall(pattern, text)

    return all_matches
