from flask import Flask, render_template, request, redirect, url_for
import os
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

mongo = PyMongo(app)


def get_category_names():
    categories = []
    for category in mongo.db.collection_names():
        if not category.startswith("system."):
            categories.append(category)
    return categories    


@app.route("/")
def get_tasks():
    tasks = mongo.db.tasks.find()
    return render_template("tasks.html", tasks=tasks)


@app.route("/tasks/<category>")
def get_tasks_by_category(category):
    tasks = mongo.db[category].find()
    return render_template("tasks.html", tasks=tasks)


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method=="POST":
        form_values = request.form.to_dict()
        form_values["is_urgent"] = "is_urgent" in form_values
        category = form_values["category_name"]
        mongo.db[category].insert_one(form_values)
        return redirect("/")
    else:
        categories = get_category_names()
        return render_template("addtask.html", categories=categories)


@app.route('/tasks/<category>/<task_id>/edit', methods=["GET", "POST"])
def edit_task(category, task_id):
    if request.method=="POST":
        form_values = request.form.to_dict()
        form_values["is_urgent"] = "is_urgent" in form_values
        mongo.db[category].update({"_id": ObjectId(task_id)}, form_values)
        
        if form_values["category_name"] != category:
            the_task = mongo.db[category].find_one({"_id": ObjectId(task_id)})
            mongo.db[category].remove(the_task)
            mongo.db[form_values["category_name"]].insert(the_task)
            
        return redirect(url_for("get_tasks_by_category", category=form_values["category_name"]))
    else:
        the_task =  mongo.db[category].find_one({"_id": ObjectId(task_id)})
        categories = get_category_names()
        return render_template('edittask.html', task=the_task, categories=categories)


@app.route('/tasks/<category>/<task_id>/delete', methods=["POST"])
def delete_task(category, task_id):
    the_task = mongo.db[category].find_one({"_id": ObjectId(task_id)})
    mongo.db[category].remove(the_task)
    return redirect(url_for("get_tasks_by_category", category=category))




@app.route('/categories')
def get_categories():
    categories = get_category_names()
    return render_template("categories.html", categories=categories)

@app.route('/categories/add', methods=["POST"])
def add_category():
    category_name = request.form["category_name"]
    mongo.db.create_collection(category_name)
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
        app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), debug=True)