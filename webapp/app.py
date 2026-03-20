"""
Flask web UI and API for the IP Subnet Availability Checker.
Run with: python -m webapp.app
"""
import json
import os
from flask import Flask, request, render_template, jsonify
from src.ipallocator import find_available_subnets, can_allocate_prefix, generate_available_candidates


def _normalize_existing_field(existing_field):
    """
    Accept either a list (from JSON) or a multi-line string (from a form) and return a list of cidr strings.
    """
    if existing_field is None:
        return []
    if isinstance(existing_field, str):
        return [line.strip() for line in existing_field.splitlines() if line.strip()]
    if isinstance(existing_field, (list, tuple)):
        return [str(x).strip() for x in existing_field if x is not None and str(x).strip()]
    # fallback
    return [str(existing_field).strip()]


def create_app():
    # Use explicit paths to ensure templates/static are discovered regardless of cwd
    base_dir = os.path.dirname(__file__)
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, "templates"),
                static_folder=os.path.join(base_dir, "static"))
    app.config.setdefault("JSON_SORT_KEYS", False)

    @app.route("/", methods=["GET"])
    def index():
        # Render form-only page; results may be hydrated after a POST (server-side)
        return render_template("index.html")

    @app.route("/api/check", methods=["POST"])
    def api_check():
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "invalid json body"}), 400

        overall = data.get("overall")
        existing = _normalize_existing_field(data.get("existing", []))
        prefix = data.get("prefix")

        if overall is None or prefix is None:
            return jsonify({"error": "overall and prefix are required"}), 400

        try:
            # RETURN ONLY non-conflicting candidates
            candidates = generate_available_candidates(overall, existing or [], int(prefix))
            available = [c["subnet"] for c in candidates]
            can_alloc = len(available) > 0
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify({
            "can_allocate": can_alloc,
            "available_subnets": available,
            "candidates": candidates  # candidates are now only non-conflicting entries
        })

    @app.route("/check-form", methods=["POST"])
    def form_check():
        overall = request.form.get("overall", "").strip()
        existing_txt = request.form.get("existing", "").strip()
        prefix = request.form.get("prefix", "").strip()

        existing = _normalize_existing_field(existing_txt)

        error = None
        candidates = []
        available = []
        can_alloc = False
        try:
            # compute only non-conflicting candidates
            candidates = generate_available_candidates(overall, existing, int(prefix))
            available = [c["subnet"] for c in candidates]
            can_alloc = len(available) > 0
        except Exception as exc:
            error = str(exc)

        # Pass candidates and available to template so server-side form post can hydrate the UI
        return render_template("index.html",
                               overall=overall,
                               existing_txt=existing_txt,
                               prefix=prefix,
                               available=available,
                               candidates=candidates,
                               can_allocate=can_alloc,
                               error=error)

    return app


if __name__ == "__main__":
    app = create_app()
    # Development server on port 8000
    app.run(host="127.0.0.1", port=8000, debug=True)