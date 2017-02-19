from flask import *
from functools import wraps
import json,re,md,os.path
app = Flask(__name__)

def getJSONFile(filename, empty=list()):
        if not os.path.exists(filename):
                return empty
        with open(filename) as f:
                return json.loads(f.read());

def dumpJSONFile(filename,obj):
        with open(filename,"w") as f:
                json.dump(obj,f)

USE_PORT=65010
boards = getJSONFile("boards.json")
boardFullnames = getJSONFile("boardFullnames.json")

def getPostsFromBoard(board):
        return getJSONFile("boards/{}.json".format(board));

def writePostsToBoard(board,posts):
        return dumpJSONFile("boards/{}.json".format(board),posts);

def getNews():
        return getJSONFile("news.json");

def baseAPI(endpoint,board=None):
        if endpoint == "boards.json":
                return json.dumps(getJSONFile("boardFullnames.json"))
        elif board and endpoint == "posts.json":
                return json.dumps(getPostsFromBoard(board))

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    credentials = getJSONFile("admin_credentials.json")
    return username == credentials['username'] and password == credentials['password']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return authenticate()
        if not check_auth(auth.username, auth.password):
            return Response("403 Forbidden",403)
        return f(*args, **kwargs)
    return decorated

def adminTools(tool):
        if not hasattr(session,"logged_in"):
                return redirect(url_for("admin_login"),code=302)
        if not tool:
                return render_template("admin/index.html")
        elif tool == "create_board":
                return redirect("/",code=302)

def doPost(values,board):
        session.error=None
        session.highlight=[]
        session.placeholders={}
        for key in values.keys():
                        if values[key]:
                                session.placeholders[key] = values[key]
        if not board and "board" in values.keys():
                board = values['board']
        elif not board and "board" not in values.keys():
                session.error = "Specify board."
                return redirect(url_for("post"))
        board = re.sub(r"/([a-z]*)/",r"\1",board)
        if board not in boards:
                session.error = "Invalid board: "+board
                return redirect(url_for("post"))
        if not (values.get("name") and values.get("comment")):
                if not values.get("name"):
                        session.highlight.append("name")
                if not values.get("comment"):
                        session.highlight.append("comment")
                session.error = "Required inputs not filled out."
                return redirect(url_for("post",board=board))
        posts = getPostsFromBoard(board)
        posts.append({"name":values["name"],"subject":values.get("subject"),"comment":md.markdown(values["comment"].replace("<","&lt;"))})
        writePostsToBoard(board,posts)
        return redirect(url_for("boardPage",board=board))

@app.route("/")
def homepage():
        return render_template("homepage.html",news=getNews(),boards=boards,boardNames=boardFullnames);

@app.route("/<board>/")
def boardPage(board):
        if board in boards:
                return render_template("board.html",posts=getPostsFromBoard(board),boardname=boardFullnames[board])
        else:
                return redirect(url_for("notfound"))

@app.route("/post")
@app.route("/<board>/post")
def post(board=None):
        if board and board not in boards:
                return redirect(url_for("notfound"));
        if not hasattr(session,"placeholders"):
                session.placeholders = {"name":"Anonymous","subject":"","comment":""}
        return render_template("post.html",board=board);

@app.route("/handlePost")
def handlePost():
        return doPost(request.args,None)

@app.route("/api/<endpoint>")
@app.route("/api/<board>/<endpoint>")
def api(board=None,endpoint=None):
        if endpoint and not board:
                return Response(baseAPI(endpoint),mimetype="text/plain")
        elif endpoint and board:
                return Response(baseAPI(endpoint,board),mimetype="text/plain")
        else:
                return redirect(url_for("api",endpoint="boards.json"),code=302)

@app.route("/admin/login")
@requires_auth
def admin_login():
        session.logged_in = True;
        return redirect(request.referrer)

@app.route("/404.html")
def notfound():
        return render_template("404.html")

app.run(port=USE_PORT)

dumpJSONFile("boards.json",boards)
dumpJSONFile("boardFullnames.json",boardFullnames)
