---
title: LinguaIELTS API
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# LinguaIELTS

Nền tảng luyện thi IELTS — FastAPI backend + Vue frontend, chạy qua Docker Compose.

## Yêu cầu

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) hoặc Docker Engine + Compose plugin (Linux)
- File `.env` ở thư mục gốc repo (copy từ `.env.example` nếu có)

## Chạy toàn bộ stack

```bash
# Từ thư mục gốc repo (DATN/)
docker compose up -d
```

Ứng dụng: **http://localhost** (gateway nginx, port 80).

## Rebuild sau khi sửa code

Chỉ sửa **frontend** (Vue/CSS):

```bash
docker compose up -d --build frontend
docker compose restart gateway
```

Chỉ sửa **backend** (Python/API):

```bash
docker compose up -d --build api worker ml-worker beat
docker compose restart gateway
```

Sửa cả hai hoặc muốn build lại sạch:

```bash
docker compose up -d --build
docker compose restart gateway
```

> **Lưu ý:** Sau khi recreate container `api` hoặc `frontend`, nên `restart gateway` để nginx nhận IP mới (hoặc dùng `nginx.docker.conf` đã bật Docker DNS resolver).

Build lại frontend **không dùng cache** (khi vẫn thấy giao diện cũ):

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

## Kiểm tra container đang chạy

```bash
docker compose ps
```

Cột `STATUS` nên có `Up` và (với api/gateway/db) `healthy`.

| Service   | Vai trò                          |
|-----------|----------------------------------|
| gateway   | Nginx, port 80 → http://localhost |
| frontend  | SPA Vue (static)                 |
| api       | FastAPI                          |
| db        | PostgreSQL                       |
| redis     | Cache / Celery broker            |
| worker    | Celery tasks                     |

## Kiểm tra đã deploy bản frontend mới

**1. Xem container vừa recreate chưa**

```bash
docker compose ps frontend
```

Cột `CREATED` phải là vài giây/phút trước (không phải vài giờ).

**2. Xem HTML đang serve bundle nào**

PowerShell:

```powershell
(Invoke-WebRequest -Uri "http://localhost/" -UseBasicParsing).Content | Select-String "index-"
```

Kết quả có dạng `index-XXXXX.js` và `index-XXXXX.css` — hash đổi sau mỗi lần `npm run build`.

**3. Hard refresh trình duyệt**

`Ctrl + Shift + R` (hoặc tab ẩn danh) để tránh cache JS/CSS cũ.

## Xem log khi lỗi

```bash
# Tất cả service
docker compose logs -f --tail=100

# Một service
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f gateway
```

## Dừng / khởi động lại

```bash
docker compose down          # dừng, giữ volume DB
docker compose down -v       # dừng + xóa volume (mất data DB)
docker compose restart api   # restart một service
```

## Dev local không Docker (tùy chọn)

**Frontend** — `fronted/README.md` (`npm run dev` → http://localhost:5173).

**Backend** — `backend/README.md`.

Khi dev frontend local, API vẫn có thể trỏ qua proxy Vite; production/Docker dùng gateway tại port 80.
