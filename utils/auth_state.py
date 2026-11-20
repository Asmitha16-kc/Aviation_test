import json
from pathlib import Path
from urllib.parse import urlsplit


def session_storage_path(state_path):
    path = Path(state_path)
    return path.with_name(f"{path.stem}.session.json")


def app_origin(base_url):
    parsed = urlsplit(base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def capture_session_storage(page):
    return page.evaluate(
        """() => {
            const values = {};
            for (let index = 0; index < sessionStorage.length; index += 1) {
                const key = sessionStorage.key(index);
                values[key] = sessionStorage.getItem(key);
            }
            return values;
        }"""
    )


def save_session_storage(path, origin, values):
    Path(path).write_text(
        json.dumps({"origin": origin, "values": values}, indent=2),
        encoding="utf-8",
    )


def restore_session_storage(context, path, origin):
    path = Path(path)
    if not path.exists():
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("origin") != origin or not isinstance(data.get("values"), dict):
        raise ValueError(f"Invalid session-storage state in {path}")

    origin_json = json.dumps(origin)
    values_json = json.dumps(data["values"])
    context.add_init_script(
        script=f"""(() => {{
            if (window.location.origin !== {origin_json}) return;
            const values = {values_json};
            for (const [key, value] of Object.entries(values)) {{
                sessionStorage.setItem(key, value);
            }}
        }})();"""
    )
