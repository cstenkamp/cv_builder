from pprint import pprint
from datetime import datetime
import re
import yaml
import os
from itertools import permutations, chain
import requests


def main(path):
    builder = CVBuilder(path)
    print("variants:", builder.list_variants())
    print("Defaults:", builder.default_variants())
    print("Postfixes:", builder.all_postfixes())
    cv = builder.build_variant(language="de")

    print("All Links:", builder.all_links)
    builder.check_links()
    print()



class CVBuilder():
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.yaml = self.load_yaml()
        self.translations = self.yaml["translations"]
        self.all_links = []

    def load_yaml(self):
        print("CV YAML Path:", self.path)
        with open(self.path, "r") as rfile:
            cv = yaml.load(rfile, Loader=yaml.SafeLoader)
        return cv

    # === Getting all possible variants ===

    def list_variants(self):
        return {k: {v2["name"]: k2 for k2, v2 in v.items() if k2 not in "priority"} for k, v in self.yaml["variants"].items()}

    def default_variants(self):
        """Return a dict of variant defaults as specified in the YAML.

        Example output: {"language": "en", "Length": "sh", "Cat": "tech"}
        Keys are the Variant categories as in the YAML (not lowercased).
        If no explicit default is found for a category, the first non-"priority" key is returned.
        """
        defaults = {}
        for varname, opts in self.yaml.get("variants", {}).items():
            default_key = None
            for k, v in opts.items():
                if k == "priority":
                    continue
                # v is expected to be a dict for actual variant entries
                if isinstance(v, dict) and v.get("default"):
                    default_key = k
                    break
                if default_key is None:
                    default_key = k
            defaults[varname] = default_key
        return defaults

    def all_postfixes(self):
        return [v2 for v in self.list_variants().values() for v2 in v.values()]

    def _get_used_postfixes(self, variant):
        perms = list(chain.from_iterable(permutations(variant.values(), i) for i in range(1, len(variant)+1)))
        return sorted(perms, key=lambda p: len(p), reverse=True)  # we want to go from long to short
        # once we find the most specific postfix, we can remove all others

    # === language tools ===

    def wordwise_translate(self, what, tolang):
        # TODO does not work if there's eg a colon after the word
        transl = self.translations[tolang]
        if isinstance(what, (int, float)):
            what = str(what)
        if isinstance(what, str):
            what = what.replace(":", " :").replace("{", " {")
            what = " ".join([transl.get(i, i) for i in what.split(" ")])
            what = what.replace(" :", ":").replace(" {", "{")
        elif isinstance(what, (list, set, tuple)):
            what = [self.wordwise_translate(i, tolang) for i in what]
        return what

    # def get_langs(self):
    #     return set(self.yaml["variants"]["language"].keys())
    #     # print(cv["translations"])

    # def default_lang(self):
    #     langs = self.yaml["variants"]["language"]
    #     return [k for k, v in langs.items() if k not in ["priority"] and v.get("default")][0]
    #

    # === main builder ===

    def build_variant(self, language, annotate_kind=True, **kwargs):
        variant = {**self.default_variants(), **{"language": language, **kwargs}}
        print("Building variant:", variant)

        # remove all entries for a variants not considered here (eg. "Programmiersprachen [de]" in english version):
        considered_keybrackets = ["[" + ",".join(i) + "]" for i in self._get_used_postfixes(variant)]
        ncv = {}
        for k, v in self.yaml.items():
            if k not in ["variants", "translations"]:
                k = self.wordwise_translate(k, language)
                if not re.match(r".*?\[.*?\].*?", k):
                    ncv[k] = v
                else:
                    for var in considered_keybrackets:
                        if var in k:
                            key = re.sub(r"(\[.*?\])", "", k).strip()
                            if key not in ncv: # we go from long to short, so the most specific gets looked at first
                                ncv[key] = v
        print()
        # go through the sections for selection and translation
        cv = {k: self.handle_values(v, variant, k) for k, v in ncv.items()}
        cv = {(k if not re.match(r".*?\{(.*?)}", k) else re.match(r"(.*?)\{", k)[1]).strip(): v for k, v in cv.items() if v}
        pprint(cv, width=200, sort_dicts=False)

        # if annotate_kind:
        #     cv = {k: {"chronog": v} if isinstance(v, list) and all(isinstance(i, dict) for i in v) \
        #           else {"lst": v} if isinstance(v, list) \
        #           else {"basic": {k2: v2 for k2, v2 in v.items() if k2 != "design"}, "design": v["design"]} if isinstance(v, dict) and "design" in v \
        #           else v \
        #           for k, v in cv.items()}
        return cv

    # === The functions that are recursively called on all dictionaries & lists to get the right variant etc ===

    def handle_values(self, val, variant, key=""):
        """ handles dictionary values. In the first order those correspond to section content, however this is called
            recursively (handle_values -> handle_subdict -> handle_values). Special Treatmens are: img(..) & date(..)"""
        # img & date
        assert isinstance(val, (dict, str, int, float, list, tuple, set))
        if isinstance(val, str) and "img(" in val:
            assert re.match(r"img\((.*?)\)", val)[0] == "img("+re.match(r"img\((.*?)\)", val)[1]+")", "if you use 'img(..)', that must be the full value!"
        if isinstance(val, str) and "date(" in val:
            date = datetime.strptime(re.match(r"date\((.*?)\)", val)[1], "%Y-%m-%d")
            fmtstring = self.yaml["variants"]["language"][variant["language"]]["datefmt"]
            val = re.sub(r"date\(.*?\)", date.strftime(fmtstring), val)

        result = self.handle_subdict(val, variant) if isinstance(val, dict) \
                else self.wordwise_translate(val, variant["language"]) if isinstance(val, (str, int, float)) \
                else self.handle_sublist(val, variant) if isinstance(val, (list, tuple, set)) \
                else val

        # always add links...
        if isinstance(val, str):
            for j in re.findall(r"\[.*?\]\((.*?)\)", val):
                self.all_links.append(j if j.startswith("http") else "https://cstenkamp.de/" + j.removeprefix("/"))

        # now if the key had design-instructions (in curly brackets) add that here
        if re.match(r".*?\{.*?}", key):
            design_info = re.match(r".*?\{(.*?)}", key)[1]
            if isinstance(result, dict):
                result["design"] = design_info
            elif isinstance(result, list):
                result = [f"<!--design: {design_info}-->"]+result
        return result


    def handle_subdict(self, di, variant):
        used_postfixes = ["_"+"_".join(i) for i in self._get_used_postfixes(variant)]
        # remove all those keys that indicate undemanded variants (eg. title_de_short) - for that
        # we take the longest postfix-combination that matches, and then remove all others of the same name
        varianted_keys = variant_basekeys = {k for k in di.keys() if any(i in k for i in used_postfixes)}
        for pf in self.all_postfixes():
            variant_basekeys = {i.removesuffix(f"_{pf}")for i in variant_basekeys}
        basekeys2 = {i for i in variant_basekeys}
        used_variants = {}
        for pf in used_postfixes:
            for var in varianted_keys:
                if var.endswith(pf) and var.removesuffix(pf) in variant_basekeys:  # the first found one is the longest -> ignore all others
                    # print(f"{var.removesuffix(pf)} -> {var}")
                    variant_basekeys.remove(var.removesuffix(pf))
                    used_variants[var] = var.removesuffix(pf)
        di = {used_variants.get(k, k): v for k, v in di.items() if (not any(k.endswith("_"+i) for i in self.all_postfixes()) or k in used_variants) and v}

        # now handle the special key "show_on"
        if "show_on" in di:
            if isinstance(di["show_on"], str):
                di["show_on"] = set(i.strip() for i in di["show_on"].split(","))
            if set(di["show_on"]).issubset(set(variant.values())):
                di = {k: v for k, v in di.items() if k != "show_on"}
            else:
                di = {}

        # check links
        for v in di.values():
            if isinstance(v, str) and re.match(r"\[.*?\]\(.*?\)", v):
                for i in re.findall(r"\[.*?\]\((.*?)\)", v):
                    self.all_links.append(i if i.startswith("http") else "https://cstenkamp.de/" + i.removeprefix("/"))
        if di.get("hp_link"):
            self.all_links.append(di["hp_link"] if di["hp_link"].startswith("http") else "https://cstenkamp.de/" + di["hp_link"].removeprefix("/"))

        di = {self.wordwise_translate(k, variant["language"]): self.handle_values(v, variant, k) for k, v in di.items()}
        # pprint(di, width=200, sort_dicts=False)
        return di

    def handle_sublist(self, lst, variant):
        if all(isinstance(i, str) for i in lst):
            lst = self.handle_textual_sublist(lst, variant)
        else:
            lst = [self.handle_values(elem, variant) for elem in lst]
        return [self.wordwise_translate(i, variant["language"]) for i in lst if i]

    def handle_textual_sublist(self, lst, variant):
        nlst = []
        for elem in lst:
            if (parantheses := set(re.findall(r"\[(.*?)\]", elem))):
                parantheses = set(i.strip() for j in parantheses for i in j.split(","))
                if parantheses.issubset(set(variant.values())):
                    nlst.append(re.sub(r"\[.*?\]", "", elem).strip())
                elif not len(parantheses - set(self.all_postfixes())) < len(parantheses):
                    nlst.append(elem)
            else:
                nlst.append(elem)
        for i in nlst:
            for j in re.findall(r"\[.*?\]\((.*?)\)", i):
                self.all_links.append(j if j.startswith("http") else "https://cstenkamp.de/"+j.removeprefix("/"))
        return nlst

    def check_links(self, timeout=20):
        self.all_links = set(self.all_links)
        print(f"Testing {len(self.all_links)} links...")
        results = []
        for url in self.all_links:
            try:
                r = requests.get(url, timeout=10)
                results.append((url, r.status_code, r.ok))
                if not r.ok or r.status_code != 200:
                    print(f"{url} returned {r.status_code}")
            except requests.RequestException as e:
                results.append((url, None, False))
                print(f"{url} raised an Exception")
        return results




if __name__ == '__main__':
    from os.path import dirname, join
    main(join(dirname(__file__), "..", "cv", "all_cvs.yaml"))