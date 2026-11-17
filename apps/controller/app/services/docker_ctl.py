from app.config import settings

_client = None


def _docker():
    global _client
    if _client is not None:
        return _client
    try:
        import docker

        client = docker.from_env()
        client.ping()
        _client = client
        return client
    except Exception:
        # do not cache the failure: the socket may appear later (dev restarts)
        return None


def container_name(worker_id: str) -> str:
    return f"kick-{worker_id}"


def lifecycle(worker_id: str, action: str) -> dict:
    client = _docker()
    name = container_name(worker_id)
    allowed = {name.strip() for name in settings.docker_worker_names.split(",") if name.strip()}
    if name not in allowed:
        raise ValueError(f"worker container {name} is not managed")
    if client is None:
        return {"ok": False, "reason": "docker socket unavailable", "action": action, "container": name}
    container = client.containers.get(name)
    if action == "start":
        container.start()
    elif action == "stop":
        container.stop(timeout=15)
    elif action == "restart":
        container.restart(timeout=15)
    else:
        raise ValueError(f"unknown action {action}")
    container.reload()
    return {"ok": True, "action": action, "container": name, "state": container.status}
