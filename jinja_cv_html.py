import re
import markdown
from jinja2.filters import FILTERS

from util.text_util import split_into_sentences

SECTIONTRANSLATE = {
    "personal_data": ["Personal Information", "Persönliche Daten"],
    "education": ["Education", "Ausbildung"],
    "work": ["Vocational Experience", "Experience", "Teaching Experience", "Berufserfahrung"],
    "volunteer": ["Honorary Offices and Academic Self Government", "Ehrenamt und akademische Selbstverwaltung", "Ehrenamt"],
    "skills": ["Programming Languages and Computer Skills", "Programmiersprachen und -kompetenzen"],
    "awards": ["Awards, Certificates and Stipends"],
    "languages": ["Natural Languages", "Sprachen", "Natürliche Sprachen"],
    "interests": ["Hobbies and Interests"],
}

IGNORE_SECTIONS = ["personal_data"]


########################################################################################################################

def regex_search(value, regex):
    """https://stackoverflow.com/a/67384801/5122790"""
    if value and bool(re.search(regex, value)):
        return value[re.search(regex, value).regs[1][0]:re.search(regex, value).regs[1][1]]
FILTERS["regex_search"] = regex_search


def update(original_dict, future_dict = None, fn = None):
    # Recursively updates values of a nested dict by performing recursive calls
    # https://stackoverflow.com/a/56630315/5122790
    future_dict = future_dict or original_dict
    fn = fn or (lambda x: x)
    if isinstance(original_dict, dict):
        tmp_dict = {}
        for key, value in original_dict.items():
            tmp_dict[key] = update(value, future_dict, fn)
        return tmp_dict
    elif isinstance(original_dict, (list, tuple)):
        tmp_list = []
        for i in original_dict:
            tmp_list.append(update(i, future_dict, fn))
        return tmp_list
    elif isinstance(original_dict, str):
        return fn(original_dict)

def inline_edit(txt):
    txt = txt.replace("\small ", "").replace("\small", "")
    txt = markdown.markdown(txt).removeprefix("<p>").removesuffix("</p>")
    txt = txt.replace("<li>", "<li class=noinline>")
    for forbid_txt in ["enclosed", "handed in"]:
        if forbid_txt in txt: # remove the text, but keep the HTML-tags lol
            txt = " ".join([i if not forbid_txt in i else "".join([j.group() for j in re.finditer(r"<(.*?)>", i) if j]) for i in split_into_sentences(txt)])
    return txt

