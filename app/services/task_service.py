from datetime import datetime
from app import db
from app.models.task import Task

class TaskService:

    @staticmethod
    def create(user_id, data):
        task = Task(
            user_id=user_id,
            title=data["title"],
            description=data["description"],
            status=data.get("status", "new")
        )
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def get_all(user_id, page=1, limit=10):
        query = Task.query.filter(Task.user_id == user_id, Task.deleted_at.is_(None))

        total = query.count()

        tasks = query.offset((page - 1) * limit).limit(limit).all()

        return {
            "data": [t.to_dict() for t in tasks],
            "meta": {
                "total": total,
                "page": page,
                "limit": limit
            }
        }

    @staticmethod
    def get_one(user_id, task_id):
        return Task.query.filter_by(id=task_id, user_id=user_id, deleted_at=None).first()

    @staticmethod
    def soft_delete(user_id, task_id):
        task = Task.query.filter_by(id=task_id, user_id=user_id, deleted_at=None).first()
        if not task:
            return None

        task.deleted_at = datetime.utcnow()
        db.session.commit()
        return task