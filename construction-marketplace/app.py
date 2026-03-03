from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===================== MODELS =====================

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))  # customer / contractor


class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    budget = db.Column(db.Integer)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default="open")
    selected_bid_id = db.Column(db.Integer, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Bid(db.Model):
    __tablename__ = "bid"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    timeline = db.Column(db.String(100))
    contractor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))


class Rating(db.Model):
    __tablename__ = "rating"

    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    review = db.Column(db.Text)
    contractor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"))


# Create tables AFTER all models are defined
with app.app_context():
    db.create_all()


# ===================== ROUTES =====================

@app.route("/")
def home():
    return render_template("index.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        new_user = User(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role=request.form["role"]
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            session["role"] = user.role

            if user.role == "customer":
                return redirect("/customer_dashboard")
            else:
                return redirect("/contractor_dashboard")

        return "Invalid Credentials"

    return render_template("login.html")


# ---------- DASHBOARDS ----------
@app.route("/customer_dashboard")
def customer_dashboard():
    if session.get("role") == "customer":
        projects = Project.query.filter_by(customer_id=session["user_id"]).all()
        return render_template("dashboard_customer.html", projects=projects)
    return redirect("/login")


@app.route("/contractor_dashboard")
def contractor_dashboard():
    if session.get("role") == "contractor":
        projects = Project.query.filter_by(status="open").all()
        return render_template("dashboard_contractor.html", projects=projects)
    return redirect("/login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- POST PROJECT ----------
@app.route("/post_project", methods=["GET", "POST"])
def post_project():
    if session.get("role") != "customer":
        return redirect("/login")

    if request.method == "POST":
        new_project = Project(
            title=request.form["title"],
            description=request.form["description"],
            budget=request.form["budget"],
            location=request.form["location"],
            customer_id=session["user_id"]
        )

        db.session.add(new_project)
        db.session.commit()

        return redirect("/customer_dashboard")

    return render_template("post_project.html")


# ---------- VIEW BIDS ----------
@app.route("/view_bids/<int:project_id>")
def view_bids(project_id):
    if session.get("role") != "customer":
        return redirect("/login")

    bids = Bid.query.filter_by(project_id=project_id).all()
    return render_template("view_bids.html", bids=bids)


# ---------- ACCEPT BID ----------
@app.route("/accept_bid/<int:bid_id>")
def accept_bid(bid_id):
    if session.get("role") != "customer":
        return redirect("/login")

    bid = Bid.query.get(bid_id)
    project = Project.query.get(bid.project_id)

    project.status = "closed"
    project.selected_bid_id = bid_id

    db.session.commit()

    return redirect(f"/view_bids/{project.id}")


# ---------- RATE CONTRACTOR ----------
@app.route("/rate/<int:contractor_id>", methods=["GET", "POST"])
def rate(contractor_id):
    if session.get("role") != "customer":
        return redirect("/login")

    if request.method == "POST":
        new_rating = Rating(
            score=request.form["score"],
            review=request.form["review"],
            contractor_id=contractor_id,
            customer_id=session["user_id"]
        )

        db.session.add(new_rating)
        db.session.commit()

        return redirect("/customer_dashboard")

    return render_template("rate.html")


# ---------- CONTRACTOR PROFILE ----------
@app.route("/contractor/<int:id>")
def contractor_profile(id):
    contractor = User.query.get(id)
    ratings = Rating.query.filter_by(contractor_id=id).all()

    return render_template(
        "contractor_profile.html",
        contractor=contractor,
        ratings=ratings
    )


# ---------- AI COST ESTIMATOR ----------
if os.path.exists("cost_model.pkl"):
    model = pickle.load(open("cost_model.pkl", "rb"))
else:
    model = None


@app.route("/estimate", methods=["GET", "POST"])
def estimate():
    if request.method == "POST" and model:
        area = int(request.form["area"])
        prediction = model.predict([[area]])[0]
        return render_template("estimate.html", result=prediction)

    return render_template("estimate.html")


# ===================== RUN =====================

if __name__ == "__main__":
    app.run(debug=True)
