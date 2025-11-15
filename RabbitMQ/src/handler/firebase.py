import firebase_admin
from firebase_admin import credentials, db
from typing import Any

class FirebaseClient:
    def __init__(self, service_account_path: str, database_url: str):
        """
        Khởi tạo FirebaseClient
        :param service_account_path: đường dẫn tới serviceAccountKey.json
        :param database_url: URL Realtime Database (https://<your-db>.firebaseio.com/)
        """
        cred = credentials.Certificate(service_account_path)
        self.app = firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
    
    def push_job_result(self, job_id: str, result: Any, path: str = "job_results"):
        """
        Push kết quả job lên Firebase
        :param job_id: JobId để FE có thể track
        :param result: dữ liệu kết quả (dict, string, số,...)
        :param path: node gốc trong Firebase để lưu kết quả
        """
        ref = db.reference(f"{path}/{job_id}")
        ref.set({
            "jobId": job_id,
            "result": result,
            "updatedAt": getattr(db, "SERVER_TIMESTAMP")
        })
        print(f"Pushed result for job {job_id} to Firebase under '{path}/{job_id}'")
