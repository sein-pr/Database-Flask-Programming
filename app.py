import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Creates a path to the database in the project folder
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# The sqlite database is named 'site.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # This is good practice to disable
db = SQLAlchemy(app)

# Define a Model for blog posts
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    # Fetch all posts from the database
    posts = Post.query.all()
    return render_template("index.html", posts=posts)

# Add these routes to your app.py
# (This code should be added below the `home` route)

# Add a New Post
@app.route("/add", methods=["POST"])
def add_post():
    title = request.form.get("title")
    content = request.form.get("content")
    new_post = Post(title=title, content=content)
    
    db.session.add(new_post)
    db.session.commit()
    
    return redirect(url_for("home"))

# Delete a Post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    # This will return a 404 error if the post doesn't exist, which handles the error handling task.
    post = Post.query.get_or_404(post_id)
    
    db.session.delete(post)
    db.session.commit()
    
    return redirect(url_for("home"))

# Add this new route to your app.py file

# Update a Post
@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == "POST":
        post.title = request.form.get("title")
        post.content = request.form.get("content")
        db.session.commit()
        return redirect(url_for("home"))
    
    return render_template("edit_post.html", post=post)

# Add this new route to your app.py file

# Read a single Post
@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post_detail.html", post=post)

if __name__ == "__main__":
    app.run(debug=True)