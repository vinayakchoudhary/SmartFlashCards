from cs50 import SQL
from flask import Flask, redirect, render_template, session, request
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta, datetime
from random import choice

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///database.db")


@app.route("/")
def index():
    if "username" not in session:
        return redirect("/register")
    missedCards = db.execute("SELECT * FROM cards WHERE username = ? and nextDate < ?",
                             session["username"], (date.today()).strftime("%Y-%m-%d"))
    for i in range(len(missedCards)):
        db.execute("UPDATE cards SET nextDate = ?, level = ?, streak=0 WHERE username = ? AND question = ?", (date.today() + timedelta(days=(i % 7))
                                                                                                              ).strftime("%Y-%m-%d"), round(((int((missedCards[i])["level"]))/2) + 0.1), session["username"], (missedCards[i])["question"])
    count = ((db.execute("SELECT COUNT(*) AS n FROM cards WHERE username=? AND nextDate=? AND archived='no'",
             session["username"], (date.today()).strftime("%Y-%m-%d")))[0])["n"]
    return render_template("index.html", count=count)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" in session:
        return redirect("/")
    if request.method == "GET":
        return render_template("register.html", error="")
    username = request.form.get("username")
    password = request.form.get("password")

    if not username:
        return render_template("register.html", error="Please enter username")
    if not password:
        return render_template("register.html", error="Please enter password")
    if password != request.form.get("confirmation"):
        return render_template("register.html", error="Password and confirmative password must be same")
    users = db.execute("SELECT * FROM users")
    for user in users:
        if user["username"] == username:
            return render_template("register.html", error="Username already in use")
    db.execute("INSERT INTO users (username, password) VALUES (?, ?)",
               username, generate_password_hash(password))
    db.execute("INSERT INTO tags (username, name) VALUES (?, ?)", username, "Untagged")
    session["username"] = username
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect("/")
    if request.method == "GET":
        return render_template("login.html", error="")
    username = request.form.get("username")
    password = request.form.get("password")

    if not username:
        return render_template("register.html", error="Please enter username")
    if not password:
        return render_template("register.html", error="Please enter password")
    users = db.execute("SELECT * FROM users")
    for user in users:
        if (user["username"] == username) and (check_password_hash(user["password"], password)):
            session["username"] = username
            return redirect("/")
    return render_template("login.html", error="Username not found")


@app.route("/revise")
def revise():
    if "username" not in session:
        return redirect("/")
    if not request.args.get("question"):
        todayCards = db.execute("SELECT * FROM cards WHERE username=? AND nextDate=? AND archived='no'",
                                session["username"], (date.today()).strftime("%Y-%m-%d"))
        if len(todayCards) == 0:
            return redirect("/")
        chosenCard = choice(todayCards)
        return redirect(f"/revise?question={chosenCard["question"]}")
    chosenCard = db.execute("SELECT * FROM cards WHERE username=? AND nextDate=? AND question=? AND archived='no'",
                            session["username"], (date.today()).strftime("%Y-%m-%d"), request.args.get("question"))
    if len(chosenCard) == 0:
        return redirect("/")  # this is only if user tampered with url
    else:
        chosenCard = chosenCard[0]
        return render_template(f"reviseCard_{chosenCard["type"]}.html", question=request.args.get("question"))


GAPS = [1, 2, 7, 14, 30]


def correctAns(question):
    card = (db.execute("SELECT * FROM cards WHERE username=? AND question=?",
            session["username"], question))[0]
    if int(card["level"]) == 5:
        nextDate = (datetime.strptime(card["nextDate"], "%Y-%m-%d") +
                    timedelta(days=30)).strftime("%Y-%m-%d")
        db.execute("UPDATE cards SET nextDate=? WHERE username=? AND question=?",
                   nextDate, session["username"], question)
        return
    if int(card["level"]) == (int(card["streak"]) + 1):
        nextDate = (datetime.strptime(card["nextDate"], "%Y-%m-%d") +
                    timedelta(days=GAPS[int(card["level"])])).strftime("%Y-%m-%d")
        db.execute("UPDATE cards SET level=?, nextDate=?, streak=0 WHERE username=? AND question=?", int(
            card["level"]) + 1, nextDate, session["username"], question)
    else:
        nextDate = (datetime.strptime(card["nextDate"], "%Y-%m-%d") +
                    timedelta(days=GAPS[(int(card["level"]) - 1)])).strftime("%Y-%m-%d")
        db.execute("UPDATE cards SET nextDate=?, streak=? WHERE username=? AND question=?",
                   nextDate, (int(card["streak"]) + 1), session["username"], question)
    return


def wrongAns(question):
    card = (db.execute("SELECT * FROM cards WHERE username=? AND question=?",
            session["username"], question))[0]
    if int(card["level"]) == 1:
        nextDate = (datetime.strptime(card["nextDate"], "%Y-%m-%d") +
                    timedelta(days=1)).strftime("%Y-%m-%d")
        db.execute("UPDATE cards SET nextDate=? WHERE username=? AND question=?",
                   nextDate, session["username"], question)
        return
    nextDate = (datetime.strptime(card["nextDate"], "%Y-%m-%d") +
                timedelta(days=GAPS[(int(card["level"]) - 2)])).strftime("%Y-%m-%d")
    db.execute("UPDATE cards SET level=?, nextDate=?, streak=0 WHERE username=? AND question=?", int(
        card["level"]) - 1, nextDate, session["username"], question)
    return


@app.route("/showAns_enter", methods=["GET", "POST"])
def showAns_enter():
    if "username" not in session:
        return redirect("/")
    currCard = db.execute("SELECT * FROM cards WHERE username=? AND question=? AND nextDate=? AND archived='no'",
                          session["username"], request.args.get("question"), (date.today()).strftime("%Y-%m-%d"))
    if len(currCard) == 0:
        return redirect("/")
    currCard = currCard[0]
    if request.method == "POST":
        if (currCard["answer"]).lower() == (request.form.get("answer")).lower():
            correctAns(request.args.get("question"))
            status = "correct"
        else:
            wrongAns(request.args.get("question"))
            status = "wrong"
        return render_template("showAns_enter.html", status=status, answer=currCard["answer"])


@app.route("/showAns_self", methods=["GET", "POST"])
def showAnswer_self():
    if "username" not in session:
        return redirect("/")
    currCard = db.execute("SELECT * FROM cards WHERE username=? AND question=? AND nextDate=? AND archived='no'",
                          session["username"], request.args.get("question"), (date.today()).strftime("%Y-%m-%d"))
    if len(currCard) == 0:
        return redirect("/")
    currCard = currCard[0]
    if request.method == "GET":
        return render_template("showAns_self.html", question=request.args.get("question"), answer=currCard["answer"])

    if request.form.get("answer") == "correct":
        correctAns(request.args.get("question"))
    elif request.form.get("answer") == "wrong":
        wrongAns(request.args.get("question"))
    return redirect("/revise")


@app.route("/cards", methods=["GET", "POST"])
def cards():
    if "username" not in session:
        return redirect("/")
    tags = db.execute("SELECT * FROM tags WHERE username = ?", session["username"])
    cards = db.execute("SELECT * FROM cards WHERE username = ? AND archived='no'",
                       session["username"])
    if request.method == "GET":
        return render_template("cards.html", error="", tags=tags, cards=cards)

    if not request.form.get("question"):
        return render_template("cards.html", error="Please enter the question", tags=tags, cards=cards)
    if request.form.get("type") != "self" and request.form.get("type") != "enter":
        return render_template("cards.html", error="Invalid input", tags=tags, cards=cards)

    if len(db.execute("SELECT * FROM cards WHERE username=? AND question=?", session["username"], request.form.get("question"))) > 0:
        return render_template("cards.html", error="Question already in use", tags=tags, cards=cards)

    if not request.form.get("answer"):
        return render_template("cards.html", error="Please enter the answer", tags=tags, cards=cards)
    if len(db.execute("SELECT * FROM tags WHERE username = ? AND name = ?", session["username"], request.form.get("tag"))) == 0:
        return render_template("cards.html", error="Please enter valid tag", tags=tags, cards=cards)

    db.execute("INSERT INTO cards (username, question, answer, level, nextDate,tag ,type, streak, archived) VALUES (?,?,?,1,?,?, ?, 0, 'no')", session["username"],
               request.form.get("question"), request.form.get(
                   "answer"), (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
               request.form.get("tag"), request.form.get("type"))
    return redirect("/cards")


@app.route("/editCard", methods=["POST", "GET"])
def editCard():
    if "username" not in session:
        return redirect("/login")
    tags = db.execute("SELECT * FROM tags WHERE username = ?", session["username"])
    card = db.execute("SELECT * FROM cards WHERE username = ? AND question=?",
                      session["username"], request.args.get("question"))
    if len(card) != 1:
        return redirect("/cards")
    card = card[0]
    if request.method == "GET":
        return render_template("editCard.html", error="", tags=tags, card=card)

    if not request.form.get("question"):
        return render_template("editCard.html", error="Please enter the question", tags=tags, card=card)
    if request.form.get("type") != "self" and request.form.get("type") != "enter":
        return render_template("editCard.html", error="Invalid input", tags=tags, card=card)
    if not request.form.get("answer"):
        return render_template("editCard.html", error="Please enter the answer", tags=tags, card=card)
    if not request.form.get("tag"):
        return render_template("editCard.html", error="Please enter the tag", tags=tags, card=card)

    db.execute("SELECT * FROM cards WHERE username =? AND question=?",
               session["username"], card["question"])

    db.execute("UPDATE cards SET question=?, answer=?, tag=?, type=? WHERE username =? AND question=?", request.form.get("question"),
               request.form.get("answer"), request.form.get("tag"), request.form.get("type"), session["username"], request.args.get("question"))
    return redirect("/cards")


@app.route("/tags", methods=["GET", "POST"])
def tags():
    if "username" not in session:
        return redirect("/")
    tags = db.execute("SELECT name FROM tags WHERE username = ?", session["username"])
    for tag in tags:
        tag["count"] = 0
    counts = db.execute(
        "SELECT tag, COUNT(*) FROM cards WHERE username=? AND archived='no' GROUP BY tag", session["username"])
    for count in counts:
        for tag in tags:
            if tag["name"] == count["tag"]:
                tag["count"] += int(count["COUNT(*)"])
    if request.method == "GET":
        return render_template("tags.html", error="", tags=tags)
    name = request.form.get("name")
    if not name:
        return render_template("tags.html", error="Please enter tag name", tags=tags)
    for tag in tags:
        if tag["name"] == name:
            return render_template("tags.html", error="Tag already exists")
    db.execute("INSERT INTO tags (username, name) VALUES (?, ?)", session["username"], name)
    return redirect("/tags")


@app.route("/editTag", methods=["POST", "GET"])
def editTag():
    if "username" not in session:
        return redirect("/")
    if request.method == "GET":
        return render_template("editTag.html", name=request.args.get("tag"))
    db.execute("UPDATE cards SET tag=? WHERE username=? AND tag=?",
               request.form.get("name"), session["username"], request.args.get("tag"))
    db.execute("UPDATE tags SET name=? WHERE username=? AND name=?",
               request.form.get("name"), session["username"], request.args.get("tag"))
    return redirect("/tags")


@app.route("/deleteTag")
def deleteTag():
    if "username" not in session:
        return redirect("/")
    db.execute("UPDATE cards SET tag='Untagged' WHERE username=? AND tag=?",
               session["username"], request.args.get("tag"))
    db.execute("DELETE FROM tags WHERE username=? AND name=?",
               session["username"], request.args.get("tag"))
    return redirect("/tags")


@app.route("/archiveCard")
def archiveCard():
    if "username" not in session:
        return redirect("/")
    card = db.execute("SELECT * FROM cards WHERE username = ? AND question = ?",
                      session["username"], request.args.get("question"))
    if len(card) != 1:
        return render_template("cards.html", error="Question not found")
    card = card[0]
    db.execute("UPDATE cards SET archived = 'yes' WHERE username=? AND question=?",
               session["username"], request.args.get("question"))
    return redirect("/cards")


@app.route("/archivedCards")
def archivedCards():
    if "username" not in session:
        return redirect("/")

    cards = db.execute("SELECT * FROM cards WHERE username=? AND archived='yes'",
                       session["username"])
    return render_template("archivedCards.html", cards=cards)


@app.route("/unarchiveCard")
def unarchiveCard():
    if "username" not in session:
        return redirect("/")

    db.execute("UPDATE cards SET level=1, nextDate=?, streak=0, archived='no' WHERE username=? AND question=?",
               (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"), session["username"], request.args.get("question"))
    return redirect("/archivedCards")


@app.route("/deleteCard")
def deleteCard():
    if "username" not in session:
        return redirect("/")
    card = db.execute("SELECT * FROM cards WHERE username = ? AND question = ?",
                      session["username"], request.args.get("question"))
    db.execute("DELETE FROM cards WHERE username = ? AND question = ?",
               session["username"], request.args.get("question"))
    if (card[0])["archived"] == "no":
        return redirect("/cards")
    else:
        return redirect("/archivedCards")


@app.route("/logout")
def logour():
    session.clear()
    return redirect("/")
