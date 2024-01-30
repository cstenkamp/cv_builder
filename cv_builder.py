from pprint import pprint
from datetime import datetime
import re
import yaml

PATH = "/home/chris/Documents/projects/cstenkamp.de/components/cv_generator/all_cvs.yaml"
# TODO keep original order

class CVBuilder():
    def __init__(self, path):
        self.path = path
        self.yaml = self.load_yaml()
        self.translations = self.yaml["Translations"]

    def load_yaml(self):
        with open(self.path, "r") as rfile:
            cv = yaml.load(rfile, Loader=yaml.SafeLoader)
        return cv

    def get_langs(self):
        return set(self.yaml["Variants"]["Languages"].keys())
        # print(cv["Translations"])

    def default_lang(self):
        langs = self.yaml["Variants"]["Languages"]
        return [k for k, v in langs.items() if v.get("default")][0]

    def wordwise_translate(self, what, tolang):
        # TODO does not work if there's eg a colon after the word
        transl = self.translations[tolang]
        if isinstance(what, (int, float)):
            what = str(what)
        if isinstance(what, str):
            what = what.replace(":", " :")
            what = " ".join([transl.get(i, i) for i in what.split(" ")])
            what = what.replace(" :", ":")
        elif isinstance(what, (list, set, tuple)):
            what = [self.wordwise_translate(i, tolang) for i in what]
        return what

    def hndlval(self, val, lang):
        assert isinstance(val, (dict, str, int, float, list, tuple, set))
        if isinstance(val, str) and "img(" in val:
            assert re.match(r"img\((.*?)\)", val)[0] == "img("+re.match(r"img\((.*?)\)", val)[1]+")", "if you use 'img(..)', that must be the full value!"
            print("TODO: img")
        if isinstance(val, str) and "date(" in val:
            date = datetime.strptime(re.match(r"date\((.*?)\)", val)[1], "%Y-%m-%d")
            fmtstring = self.yaml["Variants"]["Languages"][lang]["datefmt"]
            val = re.sub(r"date\(.*?\)", date.strftime(fmtstring), val)
        return self.subdict_select_keys(val, lang) if isinstance(val, dict) \
                else self.wordwise_translate(val, lang) if isinstance(val, (str, int, float)) \
                else self.handle_sublist(val, lang) if isinstance(val, (list, tuple, set)) \
                else val

    def build_lang_variant(self, language):
        cv = {k: v for k, v in self.yaml.items() if k not in ["Variants", "Translations"]}
        ncv = {}
        for k, v in cv.items():
            k = self.wordwise_translate(k, language)
            if not re.match(r".*?\[.*?].*?", k):
                ncv[k] = v
            elif f"[{language}]" in k:
                ncv[re.sub(r"(\[.*?])", "", k).strip()] = v
        cv = {k: self.hndlval(v, language) for k, v in ncv.items()}
        cv = {k: v for k, v in cv.items() if v}
        pprint(cv, width=200, sort_dicts=False)

    def subdict_select_keys(self, di, lang):
        other_langs = self.get_langs() - {lang}
        ndi, removekeys = {}, set()
        for k, v in di.items():
            usekey = (not "_hidden" in k)
            for ola in other_langs:
                usekey = usekey and not (f"_{ola}" in k)
                # am I working with default-lang? if so use `orig_key = k.replace(f"_{ola}", "")`
            if usekey:
                if f"_{lang}" in k: # then don't use the default key
                    removekeys.add(k.replace(f"_{lang}", ""))
                ndi[k] = self.hndlval(v, lang)
        di = {}
        # now remove the default keys if we took the _smth keys
        for k, v in ndi.items():
            if k not in removekeys:
                k = self.wordwise_translate(k.replace(f"_{lang}", ""), lang)
                di[k] = self.wordwise_translate(v, lang)
        # now handle the special key "show_on"
        if "show_on" in di:
            if isinstance(di["show_on"], str):
                di["show_on"] = [di["show_on"]]
            if lang in di["show_on"]:
                di = {k: v for k, v in di.items() if k != "show_on"}
            else:
                return {}
        # pprint(di, width=200, sort_dicts=False)
        return di

    def handle_sublist(self, lst, lang):
        if all(isinstance(i, str) for i in lst):
            lst = self.handle_textual_sublist(lst, lang)
        else:
            lst = [self.hndlval(elem, lang) for elem in lst]
        lst = [i for i in lst if i]
        # pprint(lst, width=200, sort_dicts=False)
        return lst

    def handle_textual_sublist(self, lst, lang):
        other_langs = self.get_langs() - {lang}
        nlst = []
        for elem in lst:
            useelem = True
            for ola in other_langs:
                useelem = useelem and not (f"[{ola}]" in elem)
            if useelem:
                if f"[{lang}]" in elem: # then don't use the default key
                    elem = elem.replace(f"[{lang}]", "").strip()
                nlst.append(elem)
        return nlst


# TODO handle date(), img()

builder = CVBuilder(PATH)
builder.build_lang_variant("de")