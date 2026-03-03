@app.route("/post_project", methods=["GET", "POST"])
def post_project():
    if session.get("role") != "customer":
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        budget = request.form["budget"]
        location = request.form["location"]

        new_project = Project(
            title=title,
            description=description,
            budget=budget,
            location=location,
            customer_id=session["user_id"]
        )

        db.session.add(new_project)
        db.session.commit()

        return redirect("/customer_dashboard")

    return render_template("post_project.html")
