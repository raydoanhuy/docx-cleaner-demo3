        import os
        from flask import Flask, request, jsonify, send_file
        from github import Github
        from werkzeug.utils import secure_filename
        import tempfile
        import zipfile
        import io

        app = Flask(__name__)

        # Cấu hình GitHub
        GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"  # Thay bằng token của bạn
        REPO_NAME = "YOUR_REPO_NAME"  # Thay bằng tên repository của bạn
        UPLOAD_PATH = "legal_docs"  # Đường dẫn thư mục upload trong repository
        WORKFLOW_NAME = "process-docx.yml" # Tên file workflow

        # Khởi tạo đối tượng GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)

        def create_github_file(path, content, message="Upload file"):
            """Tạo hoặc cập nhật file trên GitHub."""
            try:
                # Kiểm tra xem file đã tồn tại chưa
                contents = repo.get_contents(path)
                # Nếu tồn tại, cập nhật file
                repo.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=contents.sha
                )
            except Exception:
                # Nếu chưa tồn tại, tạo file mới
                repo.create_file(
                    path=path,
                    message=message,
                    content=content
                )

        def dispatch_workflow(workflow_name):
            """Kích hoạt workflow trên GitHub."""
            workflows = repo.get_workflows()
            for workflow in workflows:
                if workflow.path == workflow_name:
                    workflow.run()
                    return True
            return False

        def get_workflow_run_id(workflow_name):
            """Lấy ID của lần chạy workflow mới nhất."""
            workflows = repo.get_workflows()
            for workflow in workflows:
                if workflow.path == workflow_name:
                    runs = workflow.get_runs()
                    if runs.totalCount > 0:
                        return runs[0].id
            return None

        def download_artifact(run_id, artifact_name="training-data"):
            """Tải artifact từ lần chạy workflow."""
            run = repo.get_workflow_run(run_id)
            artifacts = run.get_artifacts()
            for artifact in artifacts:
                if artifact.name == artifact_name:
                    # Tải artifact
                    zip_content = artifact.download_contents()
                    # Giải nén và trả về file
                    zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
                    for name in zip_file.namelist():
                        return zip_file.read(name)
            return None

        @app.route("/upload", methods=["POST"])
        def upload_file():
            """API endpoint để tải lên file .docx và xử lý."""
            if "docx-file" not in request.files:
                return jsonify({"status": "error", "message": "No file part"}), 400
            file = request.files["docx-file"]
            if file.filename == "":
                return jsonify({"status": "error", "message": "No file selected"}), 400
            if not file.filename.endswith(".docx"):
                return jsonify({"status": "error", "message": "Invalid file type"}), 400

            # Lưu file vào thư mục legal_docs trên GitHub
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_PATH, filename)
            content = file.read()
            create_github_file(path=file_path, content=content)

            # Kích hoạt workflow
            if not dispatch_workflow(WORKFLOW_NAME):
                return jsonify({"status": "error", "message": "Failed to dispatch workflow"}), 500
            
            # Lấy workflow run ID
            run_id = get_workflow_run_id(WORKFLOW_NAME)
            if run_id is None:
                return jsonify({"status": "error", "message": "Workflow run not found"}), 500

            # Chờ workflow hoàn thành (có thể dùng cơ chế polling hoặc webhook)
            import time
            while True:
                run = repo.get_workflow_run(run_id)
                if run.status == "completed":
                    break
                time.sleep(5)  # Chờ 5 giây trước khi kiểm tra lại

            # Tải artifact
            training_data = download_artifact(run_id)
            if training_data is None:
                return jsonify({"status": "error", "message": "Artifact not found"}), 500

            # Trả về file cho người dùng tải xuống
            return jsonify({
                'status': 'success',
                'download_url': '/download'
            })

        @app.route('/download')
        def download_file():
            # Lấy run_id từ tham số
            run_id = get_workflow_run_id(WORKFLOW_NAME) # Đường dẫn file training_data.txt
            training_data = download_artifact(run_id)
            if training_data:
                return send_file(
                    io.BytesIO(training_data),
                    mimetype='text/plain',  # Đặt kiểu MIME
                    as_attachment=True,
                    download_name='training_data.txt'  # Tên file tải về
                )
            else:
                return "File not found", 404
        if __name__ == "__main__":
            app.run(debug=True, port=5000)
        
        
