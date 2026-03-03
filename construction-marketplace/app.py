# ---------------- PROJECT MODEL ----------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    budget = db.Column(db.Integer)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default="open")
    selected_bid_id = db.Column(db.Integer, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# ---------------- BID MODEL ----------------
class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    timeline = db.Column(db.String(100))
    contractor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


# ---------------- RATING MODEL ----------------
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    review = db.Column(db.Text)
    contractor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# Create DB again to include new tables
with app.app_context():
    db.create_all()


# ---------------- POST PROJECT ----------------
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


# ---------------- VIEW BIDS ----------------
@app.route("/view_bids/<int:project_id>")
def view_bids(project_id):
    if session.get("role") != "customer":
        return redirect("/login")

    bids = Bid.query.filter_by(project_id=project_id).all()
    return render_template("view_bids.html", bids=bids)


# ---------------- ACCEPT BID ----------------
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


# ---------------- RATE CONTRACTOR ----------------
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


# ---------------- CONTRACTOR PROFILE ----------------
@app.route("/contractor/<int:id>")
def contractor_profile(id):
    contractor = User.query.get(id)
    ratings = Rating.query.filter_by(contractor_id=id).all()

    return render_template("contractor_profile.html",
                           contractor=contractor,
                           ratings=ratings)
