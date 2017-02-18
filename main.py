from flask import *
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
boardFullnames = getJSONFile("boardFullnames.json",empty=dict())

def getPostsFromBoard(board):
	return getJSONFile("boards/{}.json".format(board));

def writePostsToBoard(board,posts):
        return dumpJSONFile("boards/{}.json".format(board),posts);

def getNews():
	return getJSONFile("news.json");

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
        posts.append({"name":values["name"],"subject":values.get("subject"),"comment":md.markdown(values["comment"])})
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

@app.route("/404.html")
def notfound():
	return render_template("404.html")

app.run(port=USE_PORT)

dumpJSONFile("boards.json",boards)
dumpJSONFile("boardFullnames.json",boardFullnames)
