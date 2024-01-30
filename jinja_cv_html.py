import argparse
from os import path as p
import re
import yaml
import markdown
from jinja2 import Template
from jinja2.filters import FILTERS

from util.jinja_get_variables import get_variables
from util.text_util import split_into_sentences
from util.various import browser_open

YAMLPATH = "/home/chris/Documents/projects/cstenkamp.de/scripts/cv_long_en.yaml"
TEMPLATEPATH = "/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/content/page/cv/cv.html.jinja"
CVPATH = "/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/content/page/cv"
HUGO_PUBLIC_PATH = "/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/public"
OUTPATH = "/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/content/page/cv"

SECTIONTRANSLATE = {
    "personal_data": ["Personal Information", "Persönliche Daten"],
    "education": ["Education", "Ausbildung"],
    "work": ["Vocational Experience", "Experience", "Teaching Experience", "Berufserfahrung"],
    "volunteer": ["Honorary Offices and Academic Self Government", "Ehrenamt und akademische Selbstverwaltung", "Ehrenamt"],
    "skills": ["Programming Languages and Computer Skills"],
    "awards": ["Awards, Certificates and Stipends"],
    "languages": ["Natural Languages", "Sprachen"],
    "interests": ["Hobbies and Interests"],
}

IGNORE_SECTIONS = ["personal_data"]

MIXINS = dict(
           github_user = "cstenkamp",
           linkedin_user = "cstenkamp",
           so_user = "5122790",
           about_text = "I may have overengineered this a little."
         )

# TODO:
#  * remove empty "(see )"
#  * Sections bachelor thesis, master thesis, attended conferences
#  * design of awards and languages sucks

########################################################################################################################
# main

def parse_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('yamlpath', help='Path of the cv-yaml as exported from parse_cv.py')
    parser.add_argument('cvpath', help='Path where the HTML will be (dir of which is where stylesheet and image reside)')
    parser.add_argument('templatepath', help='Path of the template-HTML')
    parser.add_argument('hugopublicpath', help='Path of the Hugo-Public-Directory (for fontawesome) - OUTSIDE of docker!')
    return parser.parse_args()


def main():
    args = parse_command_line_args()
    cnt = prepare_content_dict(args.yamlpath, p.dirname(args.cvpath), ".", args.hugopublicpath, MIXINS)

    unfulfilled_vars = [i for i in get_variables(p.dirname(args.templatepath), p.basename(args.templatepath)) if i not in cnt]
    print(unfulfilled_vars)

    with open(args.templatepath) as f:
        tmpl = Template(f.read())

    html = tmpl.render(**cnt)
    # browser_open(html)
    with open(args.cvpath, "w") as wfile:
        wfile.write(html)


def prepare_content_dict(yamlpath, cvdir, image_path, hugo_public_path, mixins=None):
    with open(yamlpath, "r") as rfile:
        cv_content = yaml.load(rfile, yaml.SafeLoader)
    cv_content["Basic Info"] = {k: "\n".join(v) for k, v in cv_content["Basic Info"].items()}
    for k, v in cv_content.items():
        if v.get("basic"):
            for k2, v2 in v["basic"].items():
                if not isinstance(v2, str):
                    cv_content[k]["basic"][k2] = "\n".join(cv_content[k]["basic"][k2])

    cnt = cv_content["Basic Info"]
    cnt.update(cvpath = cvdir,
               image_link = f"{image_path}/{cnt['photo']}.jpg",
               homepage_link = f"https://{cnt['homepage']}",
               location = cnt["address"].split("\n")[-1].split(" ")[-1],
               hugo_public_path = hugo_public_path,
               )
    cnt.update(mixins)

    cnt["sections"] = [{"title": v, "sectionkey": k, "content": cv_content[v]}
                         for k, vv in SECTIONTRANSLATE.items() for v in vv if cv_content.get(v) and k not in IGNORE_SECTIONS]

    cnt = update(cnt, fn=inline_edit)
    return cnt


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


########################################################################################################################

if __name__ == '__main__':
    main()
