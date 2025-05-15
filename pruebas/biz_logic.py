from models import db, TaskList, Task


def create_task_list(name):
    tl = TaskList(name=name)
    db.session.add(tl)
    db.session.commit()
    return tl


def get_all_task_lists():
    return TaskList.query.all()


def create_task(title, task_list_id):
    task = Task(title=title, task_list_id=task_list_id)
    db.session.add(task)
    db.session.commit()
    return task


def get_tasks(task_list_id):
    return Task.query.filter_by(task_list_id=task_list_id).all()


def update_task(task_id, title=None, completed=None):
    task = Task.query.get(task_id)
    if title is not None:
        task.title = title
    if completed is not None:
        task.completed = completed
    db.session.commit()
    return task


def delete_task(task_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
