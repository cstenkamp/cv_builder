############################### externe imports ####################################
import os.path

from flask import Flask, redirect, url_for, session, make_response, render_template, Response
from flask import request
from flask_cors import CORS, cross_origin
from jinja2 import Template

from components.cv_generator.jinja_cv_html import prepare_content_dict, MIXINS
from components.cv_generator.util.jinja_get_variables import get_variables

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


@app.route("/", methods=['GET'])
@cross_origin(supports_credentials=True)
def read_yaml():
    yamlpath = f"/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/content/page/cv/{request.args.get('name')}.yaml"
    print(yamlpath)
    if not os.path.isfile(yamlpath):
        # return ""
        yamlpath = "/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/content/page/cv/cv_long_en.yaml"

    # with open("/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/content/page/cv/cv.html") as rfile:
    #     text = rfile.read()

    cnt = prepare_content_dict(yamlpath, "/home/chris/Documents/projects/cstenkamp.de/components/cv", ".", "", MIXINS)

    # unfulfilled_vars = [i for i in get_variables("/home/chris/Documents/projects/cstenkamp.de/components/cstenkamp-de/content/page/cv/",
    #                                              "cv.html.jinja") if i not in cnt]
    # print(unfulfilled_vars)

    with open("/home/chris/Documents/projects/cstenkamp.de/components/cv_generator/cv.html.jinja") as f:
        tmpl = Template(f.read())

    html = tmpl.render(**cnt)

    return html

####################################################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)