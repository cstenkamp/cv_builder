from os.path import dirname, isfile, join, splitext
from os import listdir, getenv

from flask import Flask, make_response, request, send_file
from flask_cors import CORS, cross_origin
from jinja2 import Template

from jinja_cv_html import IGNORE_SECTIONS, SECTIONTRANSLATE, update, inline_edit
from cv_builder import CVBuilder


FLASK_RUN_PORT   = getenv("FLASK_RUN_PORT")   or 8003
TEMPLATE_PATH    = getenv("TEMPLATE_PATH")    or join(dirname(__file__), "static", "cv.html.jinja")
IMG_ROOT         = getenv("IMG_ROOT")         or join(dirname(__file__), "..", "cv")
YAML_PATH        = getenv("YAML_PATH")        or join(IMG_ROOT, "all_cvs.yaml")
HUGO_PUBLIC_URL  = getenv("HUGO_PUBLIC_URL")  or "http://localhost:1313"
BUILDER_BASE_URL = getenv("BUILDER_BASE_URL") or f"http://localhost:{FLASK_RUN_PORT}"
GET_IMAGE_URL    = getenv("GET_IMAGE_URL")    or f"{BUILDER_BASE_URL}/getimage"
CV_CSS_URL       = getenv("CV_CSS_URL")       or f"{BUILDER_BASE_URL}/cv.css"

####################################################################################

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app)

@app.errorhandler(404)
def not_found(*args, **kwargs):
    """Page not found."""
    return make_response("Error 404! Page not found.", 404)


@app.before_request
def before_request(*args, **kwargs):
    print(end='')

########################################################################################


def get_variant(args, builder=None):
    builder = builder or CVBuilder(YAML_PATH)
    variants = builder.list_variants()
    defaults = builder.default_variants()
    this_variant = {}
    for var in variants.keys():
        key = var.lower()
        val = args.get(key)
        if val is None or val == "null":
            # use the per-category default from the YAML (fall back to language default)
            this_variant[key] = defaults.get(var) or builder.default_lang()
        else:
            this_variant[key] = val
    return this_variant


def prepare_contentdict(cv_content, get_image_url, hugo_public_url, sectiontranslate, ignoresections):
    cnt = cv_content["Basic Info"]
    cnt.update(image_link = f"{get_image_url}?name={cnt['photo'][4:-1]}",
               homepage_link = f"https://{cnt['homepage']}",
               hugo_public_url = hugo_public_url,
               )
    cnt["sections"] = [{"title": v, "sectionkey": k, "content": cv_content[v]}
                         for k, vv in sectiontranslate.items() for v in vv if cv_content.get(v) and k not in ignoresections]
    cnt = update(cnt, fn=inline_edit)
    return cnt

########################################################################################


@app.route('/getimage')
def get_image():
    fname = join(IMG_ROOT, request.args.get("name"))
    if not isfile(fname):
        fname = [i for i in listdir(IMG_ROOT) if splitext(i)[0] == request.args.get("name")]
        if len(fname) < 1:
            return ""
        fname = join(IMG_ROOT, fname[0])
    return send_file(fname, mimetype='image/gif')

@app.route('/cv.css')
def cv_style():
    cssfile = join(dirname(__file__), "static", "cv.css")
    return send_file(cssfile)


@app.route("/listvariants")
@cross_origin(supports_credentials=True)
def list_variants():
    builder = CVBuilder(YAML_PATH)
    return builder.list_variants()


@app.route("/getyaml", methods=['GET'])
@cross_origin(supports_credentials=True)
def get_yaml():
    builder = CVBuilder(YAML_PATH)
    print("Request Args:", dict(request.args))
    variant = get_variant(request.args, builder)
    print("Used variant:", variant)
    yaml = builder.build_variant(**variant)
    return yaml


@app.route("/cv", methods=['GET'])
@cross_origin(supports_credentials=True)
def get_cv():
    builder = CVBuilder(YAML_PATH)
    variant = get_variant(request.args, builder)
    cv_content = builder.build_variant(**variant, annotate_kind=True)

    with open(TEMPLATE_PATH) as rfile:
        tmpl = Template(rfile.read())

    cnt = prepare_contentdict(cv_content=cv_content,
                              get_image_url=GET_IMAGE_URL,
                              hugo_public_url=HUGO_PUBLIC_URL,
                              sectiontranslate=SECTIONTRANSLATE,
                              ignoresections=IGNORE_SECTIONS)
    cnt["cv_css_path"] = CV_CSS_URL
    html = tmpl.render(**cnt)

    return html

####################################################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_RUN_PORT)