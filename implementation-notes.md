# Implementation Notes — LinguaIELTS

> File này ghi lại mọi quyết định nằm ngoài spec, các thay đổi so với yêu cầu, tradeoff và ghi chú kỹ thuật quan trọng.

---

## 1. Quyết định nằm ngoài spec

### 1.1 icon_profile.jpg — vị trí tệp
- **Quyết định**: File `icon_profile.jpg` được đặt tại `fronted/public/icon_profile.jpg` (đã tồn tại). File ở root dự án được giữ nguyên để tham khảo, không xóa.
- **Lý do SOLID**: `fronted/public/` là thư mục dành cho static assets của Vite — đây là Single Responsibility nguyên tắc, asset frontend thuộc về frontend project.
- **Reference trong code**: Dùng `/icon_profile.jpg` (tuyệt đối, relative to public/) thay vì `@/assets/` vì không cần Vite processing cho ảnh đơn giản này.

### 1.2 Default avatar logic
- **Quyết định**: Khi `avatar_url` là null/empty, hiển thị `/icon_profile.jpg` thay vì initials text.
- **Thay đổi**: AppTopbar, AppSidebar, Profile.vue đều dùng cùng logic: `avatarUrl || '/icon_profile.jpg'`.
- **Lý do**: Người dùng chưa upload ảnh vẫn có giao diện nhất quán và đẹp.

### 1.3 Avatar upload flow
- Backend endpoint đã có: `PUT /users/me/avatar` (multipart form).
- **Quyết định**: Thêm avatar upload vào Profile.vue thay vì tạo trang riêng.
- **Sau khi upload**: Gọi lại `auth.fetchProfile()` để đồng bộ `auth.profile.avatar_url` trên toàn app (Topbar, Sidebar, Profile đều reactive theo `auth.profile`).

### 1.4 Streak logic — tradeoff giữa "daily login" và "khi làm bài"
- **Spec gốc**: "khi người dùng sử dụng trang web liên tiếp thì cứ +1 dần vào"
- **Quyết định**: Streak được tăng ở **hai nơi**:
  1. **Activity ping** (`POST /users/me/activity-ping`): gọi từ frontend khi user load app, cập nhật streak nếu chưa active hôm nay.
  2. **Khi submit bài** (`history_service.py`, `practice_service.py`): cũng gọi streak update.
- **Lý do**: "sử dụng trang web" có thể chỉ là mở trang, không nhất thiết làm bài. Activity ping đảm bảo streak tăng khi chỉ login.
- **Cảnh báo streak**: Frontend hiển thị toast warning khi streak > 0 và người dùng chưa hoạt động hôm nay (logic check trên `last_activity_date`).

### 1.5 EXP calculation
- **Spec gốc**: "cứ 10' là được 1 exp"
- **Quyết định**: XP = `max(1, floor(duration_seconds / 600))`. Minimum 1 XP mỗi lần hoàn thành bài.
- **Lý do**: Tránh user nhận 0 XP khi làm bài rất nhanh (dưới 10 phút), vẫn cần khuyến khích.
- **Tradeoff**: User có thể "spam" bài ngắn để nhận XP. Chấp nhận được ở giai đoạn này.
- **Vocabulary (2026-05)**: Cùng công thức qua `app/core/xp.py`. `POST /vocabulary/sessions/complete` ghi `History` (subject `Vocabulary`, mode `vocab`) + `Progress` + streak/XP. Dashboard: Getting Started task, Study Plan skill `vocabulary`, Progress/Reports badge.

### 1.6 Leaderboard
- **Quyết định**: Leaderboard không require auth (public endpoint) để cho phép chia sẻ link, nhưng highlight rank của current user nếu đã login.
- **Top 50**: Giới hạn 50 users để tránh query chậm.
- **Privacy**: Chỉ hiển thị `full_name` hoặc phần trước `@` của email, không hiển thị email đầy đủ.

### 1.7 Result.vue — Answer Key
- **Spec gốc**: "nên có thêm như bức hình (nó có chức năng là liệt kê các câu trả lời mà mình trả lời trong bài)"
- **Quyết định**: Thêm section "Answer Key" bên dưới score card, hiển thị grouped theo Part.
- **Grouping logic**: Part được lấy từ `part_index` trong `details` array (backend cần thêm field này). Nếu không có, fallback to nhóm 10 câu (IELTS standard).
- **Backend change**: `practice_service.py` submit thêm `part_index` (0-based) vào mỗi detail item.

### 1.8 Dashboard Getting Started — reset 00:00
- **Quyết định**: "Getting Started" tasks là persistent (không reset daily). Đây là onboarding checklist, không phải daily goals.
- **Thay đổi so với spec**: Daily study tracking (study_days) dùng `History.completed_at` date để đếm ngày học trong tuần, reset tự nhiên theo tuần/ngày từ dữ liệu thực.
- **Lý do**: Nếu reset daily toàn bộ Getting Started, user sẽ mất cảm giác tiến bộ. Daily reset chỉ phù hợp với daily challenge/streaks, không phải onboarding.

### 1.9 Listening transcript highlight
- **Quyết định**: Sử dụng `HTMLAudioElement.ontimeupdate` event kết hợp với timestamp data trong quiz JSON để highlight transcript đoạn đang phát.
- **Data requirement**: Transcript cần có `start_time` và `end_time` per segment trong data JSON. Nếu không có → fallback to static transcript (không highlight).
- **Full-screen transcript**: Sử dụng CSS `height: calc(100vh - Xpx)` thay vì `max-h-[...]` cố định.

### 1.10 Vocabulary — "thêm từ từ reading/listening"
- **Quyết định**: Thêm "Save to Vocabulary" button trong Reading/Listening review pages khi user select text.
- **Implementation**: Dùng `VocabPopup` component đã tồn tại trong Reading, extend cho Listening review.
- **Context**: Từ được lưu vào topic mặc định "Từ bài nghe/đọc" nếu user chưa chọn topic.

---

## 2. Thay đổi so với yêu cầu gốc

| Yêu cầu | Thay đổi | Lý do |
|---------|----------|-------|
| "Sắp xếp file theo chuẩn SOLID" | File đã ở đúng vị trí (`fronted/public/`). Xóa file tại root project. | DRY principle |
| "Đặt cảnh báo streak" | Toast notification khi gap > 1 ngày, không phải real-time alert | Less intrusive UX |
| "Getting Started reset lại theo 00:00" | Không reset Getting Started; chỉ daily study count reset | Giải thích ở 1.8 |
| "Process by skill cập nhật từ backend" | Đã kết nối với `/progress` và `/skill-radar` endpoints | Đã có, chỉ cần fix mock data |

---

## 3. Tradeoff

### 3.1 Streak accuracy
- **Tradeoff**: Streak update xảy ra cả khi load app (activity ping) lẫn khi submit bài. Có thể double-count nếu activity ping gọi trước submit cùng ngày.
- **Giải quyết**: Logic `last_activity_date == today` → skip update, nên không bị double-count.

### 3.2 Leaderboard privacy vs. motivation
- **Tradeoff**: Hiển thị tên thật vs. giữ privacy.
- **Quyết định**: Hiển thị `full_name || email_prefix`. Users được thông báo trong onboarding rằng tên có thể public trên leaderboard.

### 3.3 EXP inflation qua thời gian
- **Tradeoff**: Users lâu năm sẽ có XP rất cao, làm mất cân bằng leaderboard.
- **Chưa xử lý**: Cần weekly/monthly leaderboard trong tương lai. Hiện tại chỉ có all-time.

### 3.4 Listening highlight performance
- **Tradeoff**: `ontimeupdate` event có thể gọi 4-10 lần/giây, gây re-render liên tục.
- **Giải quyết**: Debounce/throttle highlight update, chỉ update khi segment thực sự thay đổi.

### 3.5 Avatar upload size
- **Chưa có validation**: Backend chấp nhận bất kỳ kích thước file nào.
- **Frontend**: Thêm client-side validation 2MB max.

---

## 4. Anything Else

### 4.1 Database migration
- `UserProfile` đã có `streak`, `xp`, `last_activity_date` fields. Không cần migration.
- `History` đã có `duration_seconds` field. `practice_service.py` cần pass duration khi submit.
- **Issue**: `practice_service.py` submit không nhận `duration_seconds` từ frontend hiện tại. Cần add field vào submit request.

### 4.2 Dependency on `part_index` in practice details
- Backend `practice_service.py` cần expose `part_index` trong details response để Result.vue grouping work correctly.
- Hiện tại `_flatten_questions` có `part` dict nhưng không pass ra client.

### 4.3 Frontend service layer
- **Pattern**: Tất cả API calls đi qua `services/` layer → store → component. SOLID DIP compliance.
- **New services**: `leaderboardService.js` được tạo mới tuân theo pattern này.

### 4.4 Listening data structure
- `full_6366.json` structure: `{ id, type, parts: [{ id, order, title, audio_id, question_sets: [{ questions: [...] }], transcript: {...} }] }`
- Transcript per part có thể có `segments: [{ text, start_time, end_time }]` cho highlight.
- Cần verify với actual data file.

### 4.5 CSS color variables
- Project dùng CSS custom properties: `--green-l`, `--green`, `--ink`, `--ink2`, `--ink3`, `--border`, `--surface`, `--bg`, `--bg2`.
- Các component mới tuân theo convention này, không hardcode màu (trừ `#34d399` đã dùng khắp dự án).

---

## 5. Vocabulary CRUD — Per-User (Refactor 2026-05-19)

### 5.1 Quyết định lưu trữ
- **Lựa chọn: PostgreSQL/SQLite (database hiện tại)** — đây là lựa chọn đúng cho dữ liệu có cấu trúc, hỗ trợ query tìm kiếm, join, aggregate stats. Các lựa chọn thay thế đã cân nhắc:
  - *localStorage*: không chia sẻ giữa thiết bị, giới hạn dung lượng, không an toàn — loại bỏ.
  - *Redis/cache*: phù hợp dữ liệu tạm thời, không persistent — loại bỏ.
  - *Vector database (pgvector)*: tốt cho semantic search, nhưng quá phức tạp cho use-case này — để ngỏ cho tương lai.

### 5.2 Bug quan trọng đã fix
- **`vocabularyService.js` dùng axios instance riêng không có JWT**: Đây là bug nghiêm trọng — mọi API call đều bị 401 với user đã đăng nhập. Đã sửa sang dùng `apiClient` từ `@/api/client.js`.
- **Double commit**: `vocabulary.py` router gọi `await db.commit()` thủ công, trong khi `get_db` dependency đã auto-commit. Đã xóa tất cả manual commits trong router.

### 5.3 Kiến trúc mới (SOLID)
- Thêm `VocabRepository` (data access only) và `VocabService` (business logic + ownership checks).
- Router chỉ parse HTTP input, gọi service, trả response — không có logic DB.
- `_svc(db)` factory function trong router đảm bảo DIP.

### 5.4 Fields mới trong VocabWord
- `source_quiz_id`: lưu quiz_id khi từ được lưu từ Reading/Listening
- `source_type`: `'reading'` | `'listening'` | `'manual'`
- `updated_at`: timestamp tự động cập nhật khi mastery thay đổi
- Migration idempotent qua `ALTER TABLE ... ADD COLUMN` trong `lifespan()` — catch exception nếu column đã tồn tại.

### 5.5 Endpoints mới
- `GET /vocabulary/words/search?q=...` — tìm từ vựng across ALL topics của user
- `GET /vocabulary/stats` — trả về `{total, new, learning, mastered}` aggregate

### 5.6 Frontend stats
- `totalWords`/`masteredCount`/`newCount` trong header trước đây chỉ đếm trong topic đang chọn. Đã sửa để gọi `/vocabulary/stats` và hiển thị số liệu toàn bộ vocabulary của user.
- Context menu (`...`) trước đây không có tọa độ — đã fix dùng `getBoundingClientRect()`.

---

---

## 6. Thay đổi 2026-05-20

### 6.1 Speaking evaluate — fix 404 / timeout
- **Bug**: `QuizRunner.vue` đặt `Content-Type: multipart/form-data` thủ công khi POST FormData → xóa mất boundary → server không parse được form.
- **Fix**: Bỏ header thủ công, để browser/axios tự set đúng `multipart/form-data; boundary=...`.
- **Timeout**: Tăng từ 15s lên 120s để đủ cho pipeline Whisper + pronunciation + OpenRouter.

### 6.2 QuestionRenderer — nút đánh giá speaking
- Đổi từ `ct-btn` (white/border) sang nút xanh `#34d399` phù hợp template color chuẩn.

### 6.3 Leaderboard — sort order
- Fix `asc(xp)` → `desc(xp), desc(streak)`: người nhiều XP/streak nhất = rank 1.

### 6.4 DashboardHome — Skills quick access
- Thêm grid 5 ô (Reading, Listening, Writing, Speaking, Từ vựng) ngay trên Getting Started.

### 6.5 SpeakingResult — fetch từ API
- Hỗ trợ `state.fetchSummary = true` (navigate từ History): gọi `/speaking/attempt-summary?quiz_id=` để load kết quả.
- History.vue đã có filter speaking/writing; speaking items sẽ hiện sau khi evaluate fix được áp dụng.

### 6.6 Vocabulary — Spaced Repetition
- Tạo `VocabStudyModal.vue` với 4 chế độ: Flashcard, Trắc nghiệm, Gõ từ, Đọc hiểu.
- Thuật toán SRS đơn giản: đúng → lên mastery level, sai → xuống level.
- Nút "Luyện tập" hiện khi topic có ≥2 từ, gọi `updateWord` để persist mastery thay đổi.

### 6.7 Quiz.vue — margin
- Tăng padding trái/phải: 1.5rem (mobile) → 2rem (sm) → 3rem (lg).

### 6.8 Practice layout — padding & Speaking (2026-05-20)
- Thêm class `.exam-container` (max-width 1400px + padding responsive) dùng chung `ExamHeader` + `QuizRunner`.
- Tách `SpeakingPracticePanel.vue` cho layout Speaking practice (max-w-3xl, progress bar, nav trong card).
- `QuestionRenderer`: prop `speakingCompact` — bố cục ghi âm dọc, nút micro lớn hơn.

---

## 7. Listening Review & History (2026-05-20)

### 7.1 Cấu trúc giải thích trong JSON Listening
- File mẫu `part_1_6459.json` (Orange 11): mỗi câu có `listen_from`, `locate_info.paragraph_ranges`, `correct_answers`; **không** có trường `explain` HTML (khác Reading).
- Một số đề khác (Orange 18–20): có `explain: ""` (rỗng).
- Part level: `explanations: []` (thường rỗng).
- **Quyết định**: Frontend `listeningExplain.js` — ưu tiên `explain`/`explanation` nếu có; nếu không, fallback: đáp án đúng + đoạn transcript từ `vocabs` + `locate_info` + gợi ý thời gian `listen_from`.

### 7.2 ReviewAnswer — Listening / Reading (chi tiết đáp án)
- Icon giải thích (nút tròn `?`) khi `canExplain`; popup chỉ nội dung HTML giải thích — **không** còn icon play / nút «Đi tới» (tránh lệch thời gian so với data).
- Cột trái: `ReadingToolbar` (tô màu, tra từ, ghi chú) + `ReadingPassage` cho cả Reading và Listening transcript; đổi Part → `:key` re-mount passage để highlight/session đồng bộ đúng block.
- Lưu session review: `getAnnotation` / `saveAnnotation` với `persistKey` = `?annotationSession=` hoặc `review_{quizId}_{historyId}`; debounce 800ms; `annotationHydrating` tắt persist khi vừa load từ server (tránh ghi đè ngay sau fetch).
- Route `/review/...`: `App.vue` ẩn sidebar/topbar giống chế độ làm bài full-width.

### 7.2b Listening — đoạn thời gian / paragraph khớp `backend/data`
- **Fix** `mockQuiz.js` → `buildParagraphsFromVocabs`: chỉ số `paragraph` trong metadata (và `locate_info`) map đúng **thứ tự block gốc** trong `vocabs` (có `children`), không re-index sau `filter` — hết bug mọi gợi ý ~`02:16` sai.

### 7.3 History — Listening xem lại bài
- **Bug**: `History.vue` chỉ cho Reading dùng `ReviewAnswerByQuiz`; Listening chỉ có nút "Xem lại" vô hiệu. API history không trả `session_id`.
- **Fix backend**:
  - Cột `history.practice_session_id` (FK `practice_sessions`), ghi khi submit practice.
  - `GET /practice/history` trả `session_id` từ cột này.
  - `GET /practice/history/quiz/{quiz_id}` — lần làm gần nhất + `details` tái tạo từ `answers` + quiz JSON.
  - `get_session_result` bổ sung `details` (trước chỉ có `answers` → Review không hiện đúng/sai).
- **Fix frontend**: History mở review cho `listening` giống `reading`; `practiceStore.fetchResultByQuiz`.

### 7.4 Lưu ý dữ liệu
- Bài Orange 11 Listening chưa có HTML giải thích từ builder — UI vẫn hiện giải thích fallback (transcript + đáp án). Khi JSON có `explain` đầy đủ, không cần đổi code.

### 7.5 Practice Listening — công cụ trên transcript
- Trong `QuizRunner.vue` chế độ practice: bên transcript Listening dùng cùng stack `ReadingToolbar` + `ReadingPassage` như Reading để bật highlight, tra từ, ghi chú.

### 7.6 Speaking — chatbot AI
- Frontend `SpeakingChatbot.vue`: gọi `apiClient.post('/speaking/chat', …, { timeout: 90000 })` (đồng bộ auth/baseURL với app).
- Backend `speaking.py`: timeout `httpx` gọi OpenRouter tăng (vd. 60s) để tránh lỗi khi model chậm; cần `OPENROUTER_API_KEY` trong môi trường server.

### 7.7 Speaking evaluation — 4 IELTS criteria + advice (2026-05-20)
- Backend `POST /speaking/evaluate` chuẩn hoá output theo 4 tiêu chí IELTS:
  - `fluency_coherence_score`
  - `lexical_resource_score`
  - `grammar_range_accuracy_score`
  - `pronunciation` (acoustic model) + `pronunciation_text_score` (LLM text impression)
- LLM prompt bắt buộc thêm:
  - `task_response_score`, `is_off_topic`, `task_response_comment` (kiểm tra bám đề / lạc đề).
  - `band_boost_tips` + `criteria_feedback` (strengths/issues/advice theo từng tiêu chí).
- Band cuối vẫn tính bởi backend; nếu `is_off_topic=true` có cap điểm để tránh tăng band sai do trả lời lạc đề.
- Fallback an toàn: nếu thiếu API key hoặc LLM lỗi, backend vẫn trả `overall_comment`, `improvements`, `band_boost_tips`, `criteria_feedback` mặc định để frontend luôn có lời khuyên hành động.
- `SpeakingResult.vue` hiển thị rõ 4 tiêu chí trên màn hình (FC/LR/GRA/Pronunciation), kèm điểm từng tiêu chí và section:
  - `Band Boost Tips`
  - `Bài nói nâng band (sample)` từ `upgraded_sample_answer`.

## 8. History pagination, Leaderboard, Vocabulary study (2026-05-20)

### 8.1 History — phân trang (không giới hạn/xóa bài)

- **Vấn đề**: `History.vue` gọi `ielts.fetchHistory()` → trước đây dùng `/practice/history` mặc định `page_size=10`, chỉ thấy ~10 bài dù DB còn nhiều hơn.
- **Backend** `GET /history`:
  - `page`, `page_size` (mặc định 15, tối đa 100), `subject` (lọc Reading/Listening/Writing/Speaking).
  - `HistoryService` enrich `title` từ quiz JSON (`MockDataService`), `session_id` = `practice_session_id`.
  - Schema `HistoryListItem` + `PaginatedHistory`.
- **Frontend**:
  - `historyService.js` + `History.vue`: state phân trang riêng, `Paginator`, lọc skill gọi API (server-side).
  - Dashboard/Profile vẫn dùng `ielts.fetchHistory()` với `page_size=100` qua `/history` (preview, không thay trang History).

### 8.2 Leaderboard — Top 10 + hạng user hiện tại

- **Backend** `LeaderboardService` + `GET /leaderboard?top=10`:
  - `top`: 10 user XP cao nhất.
  - `current_user_rank`: hạng toàn cục (1 + số user có XP lớn hơn).
  - `current_user`: entry riêng nếu user **không** nằm trong top 10.
- **Frontend** `Leaderboard.vue`: podium top 3, danh sách hạng 4–10, banner hạng của bạn nếu ngoài top.

### 8.3 Vocabulary — SRS (SM-2), luyện tập trang riêng, lưu từ Reading/Listening

- **Mô hình DB** `vocab_words`: `meaning_en`, `meaning_vi`, `phonetic`, `example`, `example_vi`, `source_type`, `source_quiz_id`, SRS (`srs_ease`, `srs_interval_days`, `srs_repetitions`, `srs_next_review_at`, `srs_last_review_at`), `mastery`.
- **Backend**:
  - CRUD topic/từ như trước; `POST .../words` nhận đủ 4 phần nghĩa + ví dụ.
  - `GET /vocabulary/topics/{id}/study-queue` — hàng đợi ôn (ưu tiên từ đến hạn SRS).
  - `POST /vocabulary/topics/{id}/words/{word_id}/review` body `{ quality: 0–5 }` — SM-2 (`vocab_srs.py`).
  - `GET .../words/{id}/mcq` — trắc nghiệm 4 đáp án từ từ cùng topic (không cần AI).
- **Reading/Listening tra từ** (`useVocabPopup.js`): dictionaryapi.dev + dịch VI; trả `meaning_en`, `meaning_vi`, `phonetic`, `example`, `example_vi`. `SaveWordDialog` preview đủ 4 phần; `ReadingPassage` gửi `source_type` + `source_quiz_id` từ `QuizRunner` / `ReviewAnswer`.
- **Frontend**:
  - `Vocabulary.vue`: tab **Luyện tập** — `VocabStudyLauncher` (dropdown topic + mode → `/vocabulary/practice/:topicId?mode=...`); tab **Quản lý từ** — cột SRS (đến hạn, interval).
  - `VocabPractice.vue` — trang luyện (không popup): Flashcard, Trắc nghiệm, Đọc hiểu, Nghe chép (TTS câu ví dụ có chỗ trống).
- **Luồng**: Tra từ trong bài → Lưu (chọn/tạo topic, đủ 4 field) → Vocabulary → Luyện tập → trang practice → SRS cập nhật sau mỗi câu trả lời.

*Last updated: 2026-05-20*
