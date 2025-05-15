# schemas.py
from flask_marshmallow import Marshmallow
from models import TaskList, Task

ma = Marshmallow()


class TaskListSchema(ma.SQLAlchemySchema):
    class Meta:
        model = TaskList

    id = ma.auto_field(dump_only=True)
    name = ma.String(required=True)


class TaskSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Task

    id = ma.auto_field(dump_only=True)
    title = ma.String(required=True)
    completed = ma.Boolean()
    task_list_id = ma.Integer(required=True)
