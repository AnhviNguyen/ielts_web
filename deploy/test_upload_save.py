from app.core.shared_uploads import save_shared_upload, upload_tmp_dir

print("dir", upload_tmp_dir())
path = save_shared_upload(b"test", ".webm")
print("saved", path)
