from flask import Blueprint, request, jsonify, g
from app.services.task_service import TaskService
from app.middleware.auth_middleware import auth_required

task_bp = Blueprint("tasks", __name__)

@task_bp.route("/tasks", methods=["GET"])
@auth_required
def get_tasks():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))

    result = TaskService.get_all(g.current_user.id, page, limit)
    return jsonify(result), 200


@task_bp.route("/tasks", methods=["POST"])
@auth_required
def create_task():
    data = request.get_json()
    task = TaskService.create(g.current_user.id, data)
    return jsonify(task.to_dict()), 201


@task_bp.route("/tasks/<task_id>", methods=["DELETE"])
@auth_required
def delete_task(task_id):
    task = TaskService.soft_delete(g.current_user.id, task_id)
    if not task:
        return jsonify({"message": "Not found"}), 404

    return "", 204