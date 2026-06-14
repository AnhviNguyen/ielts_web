# Hướng dẫn Kiểm thử — IELTS Learning Platform Backend

> **Dành cho:** Developer / QA mới tiếp cận project  
> **Framework:** pytest (Python) — tương đương JUnit (Java) / Jest (JavaScript)  
> **Cập nhật:** 2026-06-13

---

## Mục lục

1. [Cấu trúc thư mục tests](#1-cấu-trúc-thư-mục-tests)
2. [So sánh: Python pytest vs Java JUnit](#2-so-sánh-python-pytest-vs-java-junit)
3. [Cách đọc một test case Python](#3-cách-đọc-một-test-case-python)
4. [Cách chạy tests](#4-cách-chạy-tests)
5. [Cách đọc kết quả (PASSED / FAILED / ERROR)](#5-cách-đọc-kết-quả)
6. [Xác thực trạng thái từng test case](#6-xác-thực-trạng-thái-từng-test-case)
7. [Giải thích số lượng tests vs test IDs](#7-giải-thích-số-lượng-tests-vs-test-ids)
8. [Bảng test cases Tầng 1](#8-bảng-test-cases-tầng-1)
9. [Các Tầng Kiểm Thử Khác (Tầng 2, 3, 4, 5, 6)](#9-các-tầng-kiểm-thử-khác-tầng-2-3-4-5-6)

---

## 1. Cấu trúc thư mục tests

Dưới đây là cấu trúc thư mục hoàn chỉnh của toàn bộ các tầng kiểm thử (Tầng 1 đến Tầng 6) trên cả Backend và Frontend:

```
ielts_web/
│
├── backend/
│   └── tests/
│       ├── conftest.py                   ← Cấu hình chung (env vars mặc định)
│       ├── pytest.ini                    ← Cấu hình pytest (markers, asyncio, paths)
│       │
│       ├── unit/                         ← Unit tests (nhanh, cô lập)
│       │   └── core/                     ← Tầng 1: Core / Infrastructure Tests
│       │       ├── test_config.py        ← Settings & validation
│       │       ├── test_security.py      ← JWT & password hashing
│       │       ├── test_password_policy.py ← Kiểm tra độ mạnh password
│       │       ├── test_auth_cookies.py  ← CSRF & cookie helpers
│       │       ├── test_rate_limit.py    ← IP extraction cho rate limiter
│       │       ├── test_storage.py       ← Local & S3 storage backend
│       │       └── test_media_assets.py  ← Resolve audio/image assets
│       │
│       └── integration/                  ← Integration tests (cần DB PostgreSQL thật)
│           ├── db/                       ← Tầng 2: Database / Repository Tests
│           │   ├── test_user_repository.py
│           │   ├── test_vocab_repository.py
│           │   └── ...
│           │
│           ├── services/                 ← Tầng 3: Service Layer Tests
│           │   ├── test_auth_service.py
│           │   ├── test_writing_service.py
│           │   └── ...
│           │
│           ├── test_auth_routes.py       ← Tầng 4: API Routers Integration Tests
│           ├── test_users_routes.py
│           ├── test_admin_routes.py
│           └── ...
│
└── fronted/
    ├── src/
    │   └── stores/
    │       └── __tests__/                ← Tầng 5: Frontend Pinia Store Unit Tests
    │           ├── auth.spec.js
    │           ├── practice.spec.js
    │           ├── ielts.spec.js
    │           └── ...
    │
    └── e2e/                              ← Tầng 6: End-to-End (E2E) Tests (Playwright)
        ├── auth.spec.js
        ├── dashboard.spec.js
        ├── profile.spec.js
        ├── placement.spec.js
        └── ...
```

---

## 2. So sánh: Python pytest vs Java JUnit

Cả hai đều có cùng triết lý: **định nghĩa đầu vào → gọi hàm → kiểm tra đầu ra**.
Cú pháp chỉ khác nhau.

### Java (JUnit 5)

```java
@Test
void testCreateAccessToken_ShouldReturnValidToken() {
    // Arrange (chuẩn bị)
    int userId = 42;

    // Act (thực thi)
    String token = jwtService.createAccessToken(userId);
    String subject = jwtService.decodeAccessToken(token);

    // Assert (kiểm tra — đây là "expected output")
    assertEquals("42", subject);          // expected="42", actual=subject
    assertNotNull(token);
    assertTrue(token.length() > 10);
}

@Test
void testExpiredToken_ShouldReturnNull() {
    String expiredToken = jwtService.createToken(-1); // hết hạn ngay
    String result = jwtService.decodeAccessToken(expiredToken);

    assertNull(result);                   // expected=null, actual=result
}
```

### Python (pytest) — **tương đương hoàn toàn**

```python
def test_sec03_access_token_contains_correct_claims():
    # Arrange (chuẩn bị)
    user_id = 42

    # Act (thực thi)
    token = create_access_token(subject=user_id)
    sub = decode_access_token(token)

    # Assert (kiểm tra — đây chính là "expected output")
    assert sub == str(user_id)    # ← assertEquals("42", subject) của Java
    assert token is not None      # ← assertNotNull(token)

def test_sec04_expired_access_token_returns_none():
    token = create_access_token(subject=1, expires_delta=timedelta(seconds=-1))
    result = decode_access_token(token)

    assert result is None         # ← assertNull(result) của Java
```

### Bảng so sánh nhanh

| Java JUnit                        | Python pytest                        | Ý nghĩa                    |
|-----------------------------------|--------------------------------------|----------------------------|
| `assertEquals(expected, actual)`  | `assert actual == expected`          | So sánh bằng               |
| `assertNull(obj)`                 | `assert obj is None`                 | Kiểm tra None              |
| `assertNotNull(obj)`              | `assert obj is not None`             | Kiểm tra khác None         |
| `assertTrue(condition)`           | `assert condition is True`           | Kiểm tra True              |
| `assertFalse(condition)`          | `assert condition is False`          | Kiểm tra False             |
| `assertThrows(Exception.class, ...)` | `with pytest.raises(Exception):`  | Expect exception           |
| `@ParameterizedTest`              | `@pytest.mark.parametrize(...)`      | Chạy nhiều bộ input        |
| `@BeforeEach` / `@AfterEach`      | `@pytest.fixture`                    | Setup / Teardown           |
| `@Tag("unit")`                    | `@pytest.mark.unit`                  | Nhóm/phân loại test        |

> **Kết luận:** `assert actual == expected` trong Python **chính là** expected output check.
> Khi `assert` fail, pytest in ra giá trị actual vs expected — giống hệt JUnit.

---

## 3. Cách đọc một test case Python

Lấy ví dụ thực tế từ `test_security.py`:

```python
# ① Tên hàm = ID test case + mô tả ngắn
def test_sec04_expired_access_token_returns_none():
    # ② Arrange: chuẩn bị input
    token = create_access_token(
        subject=1,
        expires_delta=timedelta(seconds=-1),  # ← token hết hạn ngay lập tức
    )

    # ③ Act: gọi hàm cần test
    result = decode_access_token(token)

    # ④ Assert: kiểm tra output (= "expected output" trong Java)
    assert result is None
    #      ↑ actual    ↑ expected (là None)
```

Khi test này **PASS** → `decode_access_token` trả về `None` như kỳ vọng.  
Khi test này **FAIL** → pytest in:

```
AssertionError: assert '42' is None
                ↑ actual   ↑ expected
```

---

### Test case kiểm tra exception

```python
def test_pwd02_short_password_raises_400(short_pwd):
    # "Expected output" = phải raise HTTPException với status_code=400
    with pytest.raises(HTTPException) as exc:
        assert_password_strength(short_pwd)       # ← Act

    # Kiểm tra thêm chi tiết exception (= expected output cụ thể hơn)
    assert exc.value.status_code == 400           # ← Assert 1
    assert "10" in exc.value.detail               # ← Assert 2: message phải chứa "10"
```

---

### Test với parametrize (= @ParameterizedTest Java)

```python
@pytest.mark.parametrize("weak_key", [
    "changeme",    # ← Input 1
    "secret",      # ← Input 2
    "short",       # ← Input 3
])
def test_cfg02_production_weak_secret_key_raises(weak_key):
    # Test này chạy 3 lần với 3 giá trị khác nhau
    with pytest.raises((ValueError, ValidationError)):
        _make_settings(ENVIRONMENT="production", SECRET_KEY=weak_key)
```

---

## 4. Cách chạy tests

### Yêu cầu

```bash
# Vào thư mục backend
cd f:\Documents\LearningMaterials\Year4\DATN\code\ielts_web\backend

# Cài dependencies (nếu chưa)
pip install pytest pytest-asyncio httpx
```

### Các lệnh cơ bản

```bash
# ── Chạy toàn bộ tests ───────────────────────────────────────────────────────
python -m pytest tests/ -v

# ── Chỉ chạy Tầng 1 (Core/Infrastructure) ────────────────────────────────────
python -m pytest tests/unit/core/ -v

# ── Chỉ chạy 1 file cụ thể ───────────────────────────────────────────────────
python -m pytest tests/unit/core/test_security.py -v

# ── Chỉ chạy 1 test case cụ thể (theo tên hàm) ───────────────────────────────
python -m pytest tests/unit/core/test_security.py::test_sec04_expired_access_token_returns_none -v

# ── Chạy theo marker (nhóm) ──────────────────────────────────────────────────
python -m pytest -m unit -v               # chỉ unit tests
python -m pytest -m "not ml" -v          # bỏ qua ML tests (nặng)
python -m pytest -m smoke -v             # chỉ smoke tests

# ── Chạy nhanh, dừng ngay khi fail đầu tiên ──────────────────────────────────
python -m pytest tests/unit/core/ -v -x

# ── Xem output chi tiết khi fail ─────────────────────────────────────────────
python -m pytest tests/unit/core/ -v --tb=long

# ── Chạy và xuất báo cáo HTML ────────────────────────────────────────────────
python -m pytest tests/unit/core/ -v --html=report.html  # cần: pip install pytest-html
```

### Options hữu ích

| Option | Ý nghĩa |
|--------|---------|
| `-v` | Verbose — hiện tên từng test và trạng thái |
| `--tb=short` | Traceback ngắn khi fail |
| `--tb=long` | Traceback đầy đủ khi fail |
| `-x` | Dừng ngay khi gặp fail đầu tiên |
| `-k "sec"` | Chỉ chạy tests có tên chứa "sec" |
| `-p no:cacheprovider` | Tắt cache (tránh lỗi quyền trên Windows) |
| `--co` | Chỉ liệt kê tests, không chạy (collect only) |

---

## 5. Cách đọc kết quả

### Kết quả tổng quan

```
========================= short test summary info =========================
FAILED tests/unit/core/test_config.py::test_cfg10...  ← fail
PASSED tests/unit/core/test_security.py::test_sec01   ← pass
======= 2 failed, 116 passed, 1 warning in 1.57s ======
```

### Trạng thái từng dòng (khi dùng `-v`)

```
tests/unit/core/test_security.py::test_sec01_hash_and_verify_success  PASSED  ✓
tests/unit/core/test_security.py::test_sec04_expired_...               PASSED  ✓
tests/unit/core/test_config.py::test_cfg10_auth_httponly...             FAILED  ✗
```

### Khi test FAIL — đọc chi tiết như thế nào?

```
FAILED tests/unit/core/test_config.py::test_cfg10_auth_httponly...

─── FAILURES ──────────────────────────────────────────────────────────────
test_cfg10_auth_httponly_refresh_true_in_production

    def test_cfg10_auth_httponly_refresh_true_in_production():
        s = _make_settings(ENVIRONMENT="production", ...)
>       assert s.auth_httponly_refresh is True      ← dòng assert bị fail
E       AssertionError: assert False is True        ← actual=False, expected=True
E        +  where False = Settings(...).auth_httponly_refresh   ← giá trị thực tế
```

**Đọc như sau:**
- `>` : dòng code gây ra fail
- `E AssertionError:` : kết quả thực tế (`False`) khác kỳ vọng (`True`)
- `E  + where` : giá trị đến từ đâu

---

## 6. Xác thực trạng thái từng test case

### Cách 1: Chạy và xem stdout

```bash
python -m pytest tests/unit/core/test_config.py -v --tb=short -p no:cacheprovider
```

**Output mẫu — tất cả PASS:**
```
test_config.py::test_cfg01_load_dev_settings                    PASSED
test_config.py::test_cfg02_production_weak_secret_key_raises[changeme]  PASSED
test_config.py::test_cfg02_production_weak_secret_key_raises[secret]    PASSED
...
=================== 14 passed in 0.82s ====================
```

### Cách 2: Chạy từng test case riêng lẻ để xác nhận

```bash
# Xác nhận CFG-01 PASS
python -m pytest tests/unit/core/test_config.py::test_cfg01_load_dev_settings -v

# Xác nhận CFG-02 PASS (tất cả parametrize)
python -m pytest tests/unit/core/test_config.py::test_cfg02_production_weak_secret_key_raises -v

# Xem test nào tồn tại (không chạy)
python -m pytest tests/unit/core/test_config.py --collect-only -q
```

### Cách 3: Xem danh sách test IDs

```bash
python -m pytest tests/unit/core/ --collect-only -q
```

**Output:**
```
tests/unit/core/test_config.py::test_cfg01_load_dev_settings
tests/unit/core/test_config.py::test_cfg02_production_weak_secret_key_raises[changeme]
tests/unit/core/test_config.py::test_cfg02_production_weak_secret_key_raises[secret]
...
118 tests collected
```

### Cách 4: Chạy toàn bộ Tầng 1 và xem tóm tắt

```bash
python -m pytest tests/unit/core/ -v --tb=short -p no:cacheprovider
```

**Kết quả hiện tại (2026-06-13):**
```
============ 118 passed in 1.40s ============
```

---

## 7. Giải thích số lượng tests vs test IDs

### Tại sao `test_config.py` có 12 CFG IDs nhưng 14 test functions?

**CFG-10** và **CFG-11** mỗi cái được tách thành **2 hàm test**:

```
CFG-10  → test_cfg10_auth_httponly_refresh_true_in_production   (test với Settings thật)
           test_cfg10b_auth_httponly_refresh_property_logic      (test property logic thuần)

CFG-11  → test_cfg11_auth_cookie_secure_true_in_production      (test với Settings thật)
           test_cfg11b_auth_cookie_secure_property_logic         (test property logic thuần)
```

**Lý do tách:** CFG-10/11 cần test cả 2 góc độ:
1. Test với `Settings` thật (có thể bị ảnh hưởng bởi `.env`)
2. Test property logic thuần túy bằng `SimpleNamespace` (cô lập hoàn toàn)

**Khi dùng `@pytest.mark.parametrize`, 1 hàm tạo ra NHIỀU test:**

```python
@pytest.mark.parametrize("weak_key", ["changeme", "secret", "short", "this-has..."])
def test_cfg02_production_weak_secret_key_raises(weak_key):
    ...
```
→ Tạo ra **4 test instances** từ **1 hàm**, đếm là **4 tests** trong kết quả pytest.

**Bảng đếm chính xác cho `test_config.py` (xác minh bằng `--collect-only`):**

| Test function | Số instances thực tế | CFG IDs |
|--------------|---------------------|---------|
| `test_cfg01` | 1 | CFG-01 |
| `test_cfg02` | **4** (4 giá trị parametrize) | CFG-02 |
| `test_cfg03` | 1 | CFG-03 |
| `test_cfg04` | **2** (2 URL parametrize) | CFG-04 |
| `test_cfg05` | 1 | CFG-05 |
| `test_cfg06` | 1 | CFG-06 |
| `test_cfg07` | 1 | CFG-07 |
| `test_cfg08` | 1 | CFG-08 |
| `test_cfg09` | 1 | CFG-09 |
| `test_cfg10` | 1 | CFG-10 |
| `test_cfg10b` | 1 | CFG-10 (variant b) |
| `test_cfg11` | 1 | CFG-11 |
| `test_cfg11b` | 1 | CFG-11 (variant b) |
| `test_cfg12` | 1 (2 assert bên trong) | CFG-12 |
| **Tổng** | **18 test instances** | **12 CFG IDs** |

```bash
# Xác minh bằng lệnh này:
python -m pytest tests/unit/core/test_config.py --collect-only -q -p no:cacheprovider
# Output: 18 tests collected
```

> **Tóm lại:** "12 CFG IDs" = 12 kịch bản kiểm thử logic.  
> "18 test instances" = số lần pytest thực sự chạy (vì parametrize mở rộng).
> Đây là điều bình thường — nhiều input → nhiều test run để tăng coverage.


> **Quy tắc chung:** `số test functions ≠ số test cases` vì `@parametrize` nhân bội,
> và đôi khi 1 case cần nhiều hàm để test đầy đủ.

---

## 8. Bảng test cases Tầng 1

### `test_config.py` — Settings Validation

| ID | Hàm test | Input | Expected Output | Trạng thái |
|----|----------|-------|-----------------|------------|
| CFG-01 | `test_cfg01_load_dev_settings` | `ENVIRONMENT=development` | Settings load thành công | ✅ PASS |
| CFG-02 | `test_cfg02_production_weak_secret_key_raises` | `ENVIRONMENT=production, SECRET_KEY=weak` | `ValueError` hoặc `ValidationError` | ✅ PASS |
| CFG-03 | `test_cfg03_production_metrics_missing_token_raises` | `ENVIRONMENT=production, METRICS_TOKEN=""` | `ValueError` | ✅ PASS |
| CFG-04 | `test_cfg04_production_weak_db_password_raises` | `DATABASE_URL=.../password@...` | `ValueError` | ✅ PASS |
| CFG-05 | `test_cfg05_debug_release_string_parsed_as_false` | `DEBUG="release"` | `settings.DEBUG == False` | ✅ PASS |
| CFG-06 | `test_cfg06_debug_dev_string_parsed_as_true` | `DEBUG="dev"` | `settings.DEBUG == True` | ✅ PASS |
| CFG-07 | `test_cfg07_redis_required_true_in_production` | `ENVIRONMENT=production` | `redis_required == True` | ✅ PASS |
| CFG-08 | `test_cfg08_redis_required_false_in_development` | `ENVIRONMENT=development` | `redis_required == False` | ✅ PASS |
| CFG-09 | `test_cfg09_ml_preload_disabled_when_celery_enabled` | `CELERY_ENABLED=true` | `ml_preload_on_startup == False` | ✅ PASS |
| CFG-10 | `test_cfg10_auth_httponly_refresh_true_in_production` | `ENVIRONMENT=production` | `auth_httponly_refresh == True` khi field=None | ✅ PASS |
| CFG-10b | `test_cfg10b_auth_httponly_refresh_property_logic` | `SimpleNamespace(None, production)` | property logic trả về `True` | ✅ PASS |
| CFG-11 | `test_cfg11_auth_cookie_secure_true_in_production` | `ENVIRONMENT=production` | `auth_cookie_secure == True` khi field=None | ✅ PASS |
| CFG-11b | `test_cfg11b_auth_cookie_secure_property_logic` | `SimpleNamespace` các cases | property trả về đúng | ✅ PASS |
| CFG-12 | `test_cfg12_redis_required_explicit_override` | `REDIS_REQUIRED=true/false` | Override đúng bất kể ENVIRONMENT | ✅ PASS |

### `test_security.py` — JWT & Password Hashing

| ID | Hàm test | Input | Expected Output | Trạng thái |
|----|----------|-------|-----------------|------------|
| SEC-01 | `test_sec01_hash_and_verify_success` | `plain="MyStr0ngP@ssword!"` | `verify_password(plain, hash) == True` | ✅ PASS |
| SEC-02 | `test_sec02_verify_wrong_password_returns_false` | `wrong password` | `verify_password == False` | ✅ PASS |
| SEC-03 | `test_sec03_access_token_contains_correct_claims` | `subject=42` | `decode_access_token(token) == "42"`, `type=="access"` | ✅ PASS |
| SEC-04 | `test_sec04_expired_access_token_returns_none` | `expires_delta=-1s` | `decode_access_token == None` | ✅ PASS |
| SEC-05 | `test_sec05_tampered_token_returns_none` | Token bị sửa chữ cuối | `decode_access_token == None` | ✅ PASS |
| SEC-06 | `test_sec06_refresh_token_has_correct_type` | `subject=7` | `payload["type"] == "refresh"` | ✅ PASS |
| SEC-07 | `test_sec07_refresh_token_rejected_by_decode_access_token` | Refresh token | `decode_access_token == None` | ✅ PASS |
| SEC-08 | `test_sec08_hash_token_is_deterministic` | `raw="some-token"` | Cùng input → cùng hash, len==64 | ✅ PASS |
| SEC-09 | `test_sec09_different_inputs_give_different_hashes` | 2 inputs khác nhau | 2 hash khác nhau | ✅ PASS |
| SEC-10 | `test_sec10_corrupt_hash_does_not_raise` | Hash không hợp lệ | Trả về `False`, không crash | ✅ PASS |
| SEC-11 | `test_sec11_access_token_with_string_subject` | `subject="user-uuid"` | `decode == "user-uuid"` | ✅ PASS |
| SEC-12 | `test_sec12_decode_empty_string_returns_none` | `""` | `decode == None` | ✅ PASS |

### Xem chi tiết các file khác

Dùng lệnh sau để xem danh sách đầy đủ:

```bash
python -m pytest tests/unit/core/ --collect-only -q -p no:cacheprovider
```

---

## Tóm tắt lệnh nhanh

```bash
# Chạy tất cả Tầng 1 — kết quả mong đợi: 118 passed
python -m pytest tests/unit/core/ -v -p no:cacheprovider

# Chạy 1 file
python -m pytest tests/unit/core/test_security.py -v

# Chạy 1 test cụ thể
python -m pytest tests/unit/core/test_security.py::test_sec04_expired_access_token_returns_none -v

# Xem test nào đang tồn tại
python -m pytest tests/unit/core/ --collect-only -q

# Chạy tất cả (kể cả tests gốc)
python -m pytest tests/ -v --ignore=tests/unit -p no:cacheprovider
```

---

## 9. Các Tầng Kiểm Thử Khác (Tầng 2, 3, 4, 5, 6)

Dưới đây là hướng dẫn nhanh về mục tiêu, cách chạy và ví dụ test case tiêu biểu (bao gồm đầu vào, đầu ra và cách hoạt động) cho các tầng kiểm thử từ Tầng 2 đến Tầng 6.

---

### **Tầng 2 — Database / Repository Tests**
* **Nhiệm vụ:** Kiểm tra tích hợp trực tiếp giữa lớp Repository và PostgreSQL thật qua các thao tác CRUD và các ràng buộc dữ liệu.
* **Cách chạy test:**
  ```bash
  # Vào thư mục backend
  cd backend
  # Chạy tất cả repository tests
  python -m pytest tests/integration/db/ -v
  # Chạy một file test cụ thể
  python -m pytest tests/integration/db/test_user_repository.py -v
  ```
* **Ví dụ tiêu biểu (Ràng buộc email độc nhất - `USR-06`):**
  * **Tên file:** `tests/integration/db/test_user_repository.py`
  * **Đầu vào:** Tạo 2 bản ghi `User` cùng có email `"dup@example.com"`.
  * **Đầu ra:** Bản ghi thứ hai ném ra lỗi `IntegrityError` từ SQLAlchemy/PostgreSQL do vi phạm ràng buộc độc nhất.
  * **Hành vi/Cách hoạt động:**
    ```python
    @pytest.mark.asyncio
    async def test_usr06_duplicate_email_raises_integrity_error(user_repo):
        # 1. Tạo user thứ nhất thành công
        await user_repo.create(email="dup@example.com", password_hash="hash1")
        
        # 2. Thử tạo user thứ hai trùng email -> Mong đợi ném ra lỗi IntegrityError
        with pytest.raises(IntegrityError):
            await user_repo.create(email="dup@example.com", password_hash="hash2")
    ```

---

### **Tầng 3 — Service Layer Tests**
* **Nhiệm vụ:** Kiểm tra logic nghiệp vụ phức tạp ở Service Layer (như gửi OTP, kiểm tra hạn mức hàng ngày, đổi mật khẩu) và tương tác với Repository/DB.
* **Cách chạy test:**
  ```bash
  # Vào thư mục backend
  cd backend
  # Chạy toàn bộ service tests
  python -m pytest tests/integration/services/ -v
  # Chạy một file test cụ thể
  python -m pytest tests/integration/services/test_auth_service.py -v
  ```
* **Ví dụ tiêu biểu (Hạn mức submit Writing hàng ngày - `WS-03`):**
  * **Tên file:** `tests/integration/services/test_writing_service.py`
  * **Đầu vào:** Một user đã hoàn thành 2 bài submit trong ngày, tiến hành thực hiện submit bài viết thứ 3.
  * **Đầu ra:** Ném ra exception `HTTPException` với `status_code=400` và thông báo vượt quá giới hạn ngày.
  * **Hành vi/Cách hoạt động:**
    ```python
    @pytest.mark.asyncio
    async def test_ws03_daily_limit_exceeded_raises_400(writing_service, make_user):
        user = await make_user()
        # Giả lập người dùng đã submit 2 lần trong ngày hôm nay
        await simulate_daily_submissions(user, count=2)
        
        # Thử submit lần thứ 3 -> Mong đợi lỗi HTTPException(400)
        with pytest.raises(HTTPException) as exc:
            await writing_service.submit_essay(user.id, topic_id=1, essay_text="...")
        assert exc.value.status_code == 400
        assert "daily limit" in exc.value.detail.lower()
    ```

---

### **Tầng 4 — API Routers Integration Tests**
* **Nhiệm vụ:** Kiểm tra tích hợp luồng API endpoint từ HTTP request đến DB response, bao gồm xác thực (Authentication), phân quyền (Authorization) và mã trạng thái HTTP (HTTP status code).
* **Cách chạy test:**
  ```bash
  # Vào thư mục backend
  cd backend
  # Chạy toàn bộ integration api tests (bỏ qua db và services)
  python -m pytest tests/integration/ -v --ignore=tests/integration/db --ignore=tests/integration/services
  # Chạy một file test cụ thể
  python -m pytest tests/integration/test_auth_routes.py -v
  ```
* **Ví dụ tiêu biểu (Kiểm tra quyền truy cập Admin - `ADM-01`):**
  * **Tên file:** `tests/integration/test_admin_routes.py`
  * **Đầu vào:** Gửi request `GET /admin/users` bằng token của một người dùng thường (`role="user"`).
  * **Đầu ra:** Nhận về mã lỗi HTTP `403 Forbidden`.
  * **Hành vi/Cách hoạt động:**
    ```python
    @pytest.mark.asyncio
    async def test_adm01_non_admin_gets_403(client, user_token):
        # Gửi request với token của user thường qua API client
        response = await client.get("/admin/users", headers={"Authorization": f"Bearer {user_token}"})
        
        # Kết quả mong đợi là 403 Forbidden
        assert response.status_code == 403
    ```

---

### **Tầng 5 — Frontend Pinia Store Unit Tests (Vitest)**
* **Nhiệm vụ:** Kiểm tra unit test cho trạng thái của client-side stores (Pinia), đảm bảo xử lý logic token, profile, bài làm và đồng bộ hóa API hoạt động đúng.
* **Cách chạy test:**
  ```bash
  # Vào thư mục fronted
  cd fronted
  # Chạy toàn bộ unit tests cho các Pinia stores
  npm run test:unit
  # Chạy một file test cụ thể
  npm run test:unit -- src/stores/__tests__/auth.spec.js
  ```
* **Ví dụ tiêu biểu (Tải thông tin người dùng - `auth.spec.js`):**
  * **Tên file:** `fronted/src/stores/__tests__/auth.spec.js`
  * **Đầu vào:** Gọi action `fetchProfile()` sau khi mock API `/users/me` trả về thông tin user.
  * **Đầu ra:** Store cập nhật state `profile` chính xác và `isAuthenticated` thành `true`.
  * **Hành vi/Cách hoạt động:**
    ```javascript
    test('fetchProfile cập nhật store chính xác', async () => {
      const authStore = useAuthStore()
      // Mock API phản hồi thành công thông tin user
      mockApi.onGet('/users/me').reply(200, { email: 'test@example.com', role: 'user' })
      
      await authStore.fetchProfile()
      
      // Kiểm tra state của store sau khi gọi action
      expect(authStore.profile).toEqual({ email: 'test@example.com', role: 'user' })
      expect(authStore.isAuthenticated).toBe(true)
    })
    ```

---

### **Tầng 6 — End-to-End (E2E) Tests (Playwright)**
* **Nhiệm vụ:** Kiểm tra toàn vẹn luồng trải nghiệm của người dùng trên giao diện trình duyệt thực tế, tương tác với hệ thống backend và PostgreSQL thật.
* **Cách chạy test:**
  ```bash
  # Vào thư mục fronted
  cd fronted
  # Chạy toàn bộ kiểm thử E2E ở chế độ headless
  npm run test:e2e
  # Chạy một file test cụ thể
  npx playwright test e2e/auth.spec.js
  ```
* **Ví dụ tiêu biểu (Luồng Onboarding chọn xuất phát điểm - `placement.spec.js`):**
  * **Tên file:** `fronted/e2e/placement.spec.js`
  * **Đầu vào:** Tạo tài khoản mới -> Truy cập Dashboard -> Thấy modal Chọn xuất phát điểm -> Nhập điểm số mục tiêu thủ công -> Click lưu.
  * **Đầu ra:** Modal đóng lại và hiển thị giao diện Dashboard học tập chính (với tiêu đề "Dashboard" hiển thị).
  * **Hành vi/Cách hoạt động:**
    ```javascript
    test('Người dùng mới nhập điểm thủ công thành công', async ({ page }) => {
      await page.goto('/register')
      await page.locator('#reg-email').fill('newuser@example.com')
      await page.locator('#register-btn').click()
      
      // Kiểm tra modal Onboarding hiển thị
      await expect(page.getByText('Set your starting point')).toBeVisible()
      await page.getByText('Enter existing scores').click()
      
      // Nhập điểm
      await page.locator('label:has-text("Reading") input').fill('6.5')
      await page.locator('button:has-text("Save starting bands")').click()
      
      // Đóng modal và vào Dashboard chính thành công
      await expect(page.locator('.choice-card')).not.toBeVisible()
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
    })
    ```

