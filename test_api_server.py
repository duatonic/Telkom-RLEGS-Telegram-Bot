from flask import Flask, request, jsonify, current_app, send_from_directory, abort
import os, tempfile, time, uuid
from googleservice import GoogleService
import json

def _files_summary(files):
    out = {}
    for k, f in files.items():
        out[k] = {
            "filename": f.filename,
            "mimetype": f.mimetype,
            # works for SpooledTemporaryFile/FileStorage that support seek/tell
        }
        try:
            pos = f.stream.tell()
            f.stream.seek(0, os.SEEK_END)
            out[k]["size"] = f.stream.tell()
            f.stream.seek(pos, os.SEEK_SET)
        except Exception:
            out[k]["size"] = None
    return out

def log_request_summary():
    info = {
        "method": request.method,
        "path": request.path,
        "url": request.url,
        "remote_addr": request.remote_addr,
        "content_type": request.content_type,
        "content_length": request.content_length,
        "args": request.args.to_dict(flat=True),          # query params
        "form": request.form.to_dict(flat=True),          # text fields (multipart or urlencoded)
        "json": request.get_json(silent=True),            # None unless JSON
        "files": _files_summary(request.files),           # names, filenames, types, sizes
        "headers": {k: v for k, v in request.headers.items()
                    if k.lower() in ("content-type","content-length","user-agent",
                                      "x-telegram-initdata","x-forwarded-for")},
    }
    current_app.logger.info("REQUEST:\n%s", json.dumps(info, indent=2))

def create_app():
    app = Flask(__name__, static_folder="webapp", static_url_path="")

    # Create one GoogleService instance per process and store as an extension:
    app.extensions = getattr(app, "extensions", {})
    app.extensions["google_service"] = GoogleService()

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    # SPA fallback: any non-API path returns index.html
    @app.get("/<path:path>")
    def spa_catch_all(path: str):
        if path.startswith("api/"):
            abort(404)
        # If a real file exists (e.g., /app.js), Flask will serve it automatically
        # because static_url_path="" maps the static folder at root.
        return app.send_static_file("index.html")

    @app.post("/api/append-to-sheet")
    def drive_then_sheet():
        log_request_summary()
        
        foto_evidence = request.files.get("foto_evidence")
        if not foto_evidence: return jsonify({"error":"image required"}), 400
        if foto_evidence.content_length and foto_evidence.content_length > 16777216:
            return jsonify({"error":"file too large"}), 413
        
        form_dict = request.form.to_dict(flat=True)
        for key, value in form_dict.items():
            if value == '':
                form_dict[key] = '-'

        image_file = foto_evidence.stream
        image_file.seek(0)

        svc: GoogleService = current_app.extensions["google_service"]
        svc.authenticate()
        svc.build_services()

        try:
            drive_link = svc.upload_to_drive(image_file, f"{form_dict.get('kode_sa')}_{form_dict.get('tanggal')}_{form_dict.get('kegiatan')}.jpg")
            form_dict['foto_evidence'] = drive_link
            
            # TODO: change foto evidence file type to match with what telegram bot does, change empty fields to `-` in the javascript front end
            row = [
                form_dict.get('kode_sa', '-'),      # 1
                form_dict.get('nama', '-'),         # 2
                form_dict.get('no_telp', '-'),      # 3
                form_dict.get('witel', '-'),        # 4
                form_dict.get('telda', '-'),        # 5
                form_dict.get('tanggal', '-'),      # 6
                form_dict.get('kategori', '-'),     # 7
                form_dict.get('tenant', '-'),       # 8
                form_dict.get('kegiatan', '-'),     # 9
                form_dict.get('layanan', '-'),      # 10
                form_dict.get('tarif', '-'),        # 11
                form_dict.get('nama_pic', '-'),     # 12
                form_dict.get('jabatan_pic', '-'),  # 13
                form_dict.get('telepon_pic', '-'),  # 14
                form_dict.get('paket_deal', '-'),   # 15
                form_dict.get('deal_bundling', '-'), # 16
                form_dict.get('foto_evidence', '-'), # 17
            ]

            success, res = svc.append_to_sheet([row])

            return jsonify({"row": row, "status": success})
    
        except Exception as e:
            current_app.logger.info(f'Error ocurred on google service process: {e}')

    return app

# Dev entrypoint
if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
