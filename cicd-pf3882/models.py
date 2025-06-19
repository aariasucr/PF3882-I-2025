from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class TaskList(db.Model):
    __tablename__ = "task_lists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tasks = db.relationship("Task", backref="task_list", cascade="all, delete-orphan")


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    task_list_id = db.Column(db.Integer, db.ForeignKey("task_lists.id"), nullable=False)
