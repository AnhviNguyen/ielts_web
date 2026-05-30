# Implementation Notes — LinguaIELTS

> **Git:** File này nằm trong `.gitignore` — chỉ lưu local, không push remote.  
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

---

## 9. Shadowing — YouTube transcript pipeline

### 9.1 Kiến trúc (SOLID)

| Lớp | File | Trách nhiệm |
|-----|------|-------------|
| Router | `backend/app/routers/shadowing.py` | HTTP: process, get, translate |
| Service | `backend/app/services/shadowing_service.py` | Pipeline orchestration |
| Transcript | `youtube_transcript_service.py` | Caption YouTube (`youtube-transcript-api`) |
| Fallback | `shadowing_whisper_service.py` | `yt-dlp` + Whisper khi không có phụ đề |
| Translate | `translate_service.py` | Google Translate public endpoint (không API key) |
| Segments | `backend/app/utils/segment_utils.py` | Gộp câu, tách >10s, làm tròn 0.1s |
| Repository | `shadowing_repository.py` | Cache DB `shadowing_videos` |
| Frontend service | `fronted/src/services/shadowingService.js` | API client |
| Session | `useShadowingSession.js` + `useYoutubePlayer.js` | IFrame API, auto-pause, segment |

### 9.2 API

- `POST /shadowing/video/process` — body `{ url, level?, translate? }` → extract + lưu DB + trả `VideoData` (JWT).
- `GET /shadowing/video/{video_id}` — cache theo `video_id` YouTube (11 ký tự).
- `POST /shadowing/translate` — `{ text, from_lang, to_lang }` → `{ translation }`.

### 9.3 Pipeline transcript

1. Parse `video_id` từ URL (`segment_utils.extract_youtube_video_id`).
2. Thử `YouTubeTranscriptApi` (ưu tiên en → vi → generated).
3. Nếu không có caption: `yt-dlp` tải audio → Whisper (`ml/model_registry`) → raw segments.
4. `normalize_segments`: cấp câu, `duration` ≤ 10s, `start`/`duration` 1 chữ số thập phân.
5. Tùy chọn dịch từng câu sang VI (batch tuần tự qua `translate_service`).
6. `ShadowingRepository.upsert` — cache global theo `video_id` (không per-user).

### 9.4 Frontend

- Route: `/shadowing` (nhập URL), `/shadowing/:videoId` (studio full-bleed, ẩn sidebar).
- Nav: **AppSidebar** → Luyện tập → Shadowing (stroke icon).
- 3 tab: **Shadowing** (đọc theo + auto-pause), **Dictation** (gõ + `scoreAnswer`), **Pronunciation** (Web Speech API + `scorePronunciation`).
- Progress: `localStorage` key `shadowing-progress` — `currentSegment`, `dictationScores`, `pronunciationScores`, `flaggedSegments`.
- Phím tắt: Space play/pause, R replay, ←/→ câu trước/sau.
- UI: `ct-btn` / `ct-btn-accent`, transcript panel có thể thu gọn.

### 9.5 Phụ thuộc & vận hành

- Python: `youtube-transcript-api`, `yt-dlp` (thêm vào `requirements.txt`).
- Whisper fallback: cần `ffmpeg` trên PATH (tùy chọn convert wav); tải model lần đầu có thể chậm.
- Timeout `processVideo` frontend: 300s.

### 9.6 Tradeoff

- Cache transcript **chung** mọi user — tiết kiệm xử lý, không lưu progress server-side (chỉ localStorage).
- Dịch Google public endpoint — không đảm bảo SLA; có thể rate-limit.
- Pronunciation tab dùng **browser SpeechRecognition**, không dùng backend `/speaking/evaluate` (nhẹ hơn, không upload audio).

### 9.7 UI studio (2026-05-21)

- Layout 3 cột giống app tham chiếu (JP): trái video + điều khiển, giữa nội dung tab, phải **Bản chép**.
- Màu chủ đạo: `--green-l` (#34d399), trắng, đen — class `.shadowing-studio`, `.sh-tab`, `.sh-btn-primary`.
- Tab: **Bắt chước phát âm** | **Nghe - Viết chính tả** | **Chỉnh phát âm** (tiếng Anh).
- `youtube-transcript-api` v1+: dùng `YouTubeTranscriptApi().fetch()` / `.list()`, không còn `list_transcripts` static.

*Last updated: 2026-05-21*

---

## 10. Production hardening (2026-05-24)

> Các thay đổi từ backlog `update_system.md` — PostgreSQL, Alembic, rate limit, upload validation, refresh token, Redis, Celery, observability, Docker.

### 10.1 TASK 1 — PostgreSQL + Alembic

**Đã làm:**
- `requirements.txt`: thêm `psycopg2-binary`, `slowapi`, `redis`, `celery`, `sentry-sdk`, `structlog`, `gunicorn`.
- `app/core/config.py`: `DATABASE_URL` mặc định `postgresql+asyncpg://linguaielts:password@localhost:5432/linguaielts` (vẫn override qua `.env`). SQLite demo: `sqlite+aiosqlite:///./linguaielts.db`.
- `app/db/database.py`: pool PostgreSQL `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`. Giữ nhánh SQLite + `check_same_thread`.
- `app/main.py` `lifespan()`: **xóa** toàn bộ `ALTER TABLE` thủ công → comment *Migrations managed by Alembic*.
- Thêm `backend/alembic.ini`, `alembic/env.py` (sync URL: `+asyncpg` → `+psycopg2`), `alembic/script.py.mako`, `alembic/versions/`.
- `backend/.env.example` cập nhật đầy đủ biến môi trường.

**Chạy migration:**
```bash
cd backend
set DATABASE_URL=postgresql+asyncpg://linguaielts:password@localhost:5432/linguaielts
alembic upgrade head
```

### 10.2 TASK 2 — Database indexes

**Đã làm:**
- `app/db/models.py`: `__table_args__` + `Index` trên `History`, `UserProfile`, `VocabWord`, `PracticeSession` (cột `started_at` cho practice — không có `created_at`).
- Migration `alembic/versions/001_add_indexes.py` (xem §10.13 — chain `20260524_initial` → `001_add_indexes`).

### 10.3 TASK 3 — Rate limiting (slowapi)

**Đã làm:**
- `app/core/rate_limit.py`: `Limiter` + handler 429 tiếng Việt.
- `app/main.py`: `app.state.limiter`, `SlowAPIMiddleware`, exception handler.
- `auth.py`: login `10/min`, register `5/min`, refresh `20/min` — `request: Request` param đầu tiên.
- `speaking.py`: `/evaluate` `5/min`.
- `shadowing.py`: `/video/process` `3/min`.

### 10.4 TASK 4 — Validate file upload

**Đã làm:**
- `app/core/upload.py`: MIME JPEG/PNG/WebP, max 2MB, `safe_filename` UUID.
- `users.py` `PUT /me/avatar`: dùng `validate_and_read_image`, lưu `uploads/avatars/`.

### 10.5 TASK 5 — Refresh token flow (frontend)

**Đã làm:**
- `ACCESS_TOKEN_EXPIRE_MINUTES = 30` (từ 10080).
- `fronted/src/stores/auth.js`: `setTokens(access, refresh)`, xóa cả `token` / `access_token` / `refresh_token` khi logout.
- `fronted/src/api/client.js`: interceptor refresh qua `POST /api/auth/refresh`, queue request khi đang refresh.
- `authService.uploadAvatar`: bỏ header `Content-Type: multipart` thủ công.

**Lưu ý:** Vẫn lưu `localStorage` (chưa httpOnly cookie) — cải thiện so với token 7 ngày.

### 10.6 TASK 6 — duration_seconds practice submit

**Đã làm:**
- `PracticeSubmitRequest.duration_seconds` (ge=0).
- `practice_service.submit()`: `xp_from_duration(duration_seconds)`, ghi `duration_seconds` vào `History`.
- `practice.js` store: `sessionStartedAt` khi `startSession`, gửi `duration_seconds` khi `submitSession`.

### 10.7 TASK 7 — Redis cache

**Đã làm:**
- `app/core/cache.py`: `CacheClient` fallback khi Redis down.
- `REDIS_URL` trong settings.
- `leaderboard_service`: cache `leaderboard:top{N}` TTL 300s (chỉ khi không có `current_user_id`).
- `mock_data_service.get_quiz_raw`: cache `quiz:meta:{id}` TTL 3600s.
- `invalidate_leaderboard_cache()` sau cập nhật XP: practice, history, vocab, speaking.

### 10.8 TASK 8 — Celery worker (ML tasks)

**Đã làm:**
- `app/core/celery_app.py`, `app/tasks/speaking_tasks.py`, `app/tasks/shadowing_tasks.py`, `app/tasks/notification_tasks.py`.
- `CELERY_ENABLED` (mặc định `false`) — khi `true`:
  - Speaking: `POST /speaking/evaluate` → `{task_id, status}`; poll `GET /speaking/evaluate/result/{task_id}`.
  - Shadowing: `POST /shadowing/video/process` → task; poll `GET /shadowing/video/process/result/{task_id}`.
- Refactor: `evaluate_speaking_core()` tách khỏi HTTP handler (dùng chung worker).
- Frontend: `utils/taskPolling.js`, `QuizRunner` speaking poll, `shadowingService.processVideo` poll.

**Bật Celery:**
```env
CELERY_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```
```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

### 10.9 TASK 9 — Security headers + Nginx

**Đã làm:**
- `SecurityHeadersMiddleware` trong `main.py` (nosniff, DENY frame, HSTS khi HTTPS).
- `nginx.conf` mẫu ở root repo (rate limit auth/api/ml, proxy API, SPA).

### 10.10 TASK 10 — Observability

**Đã làm:**
- `app/core/logging_config.py`: structlog JSON.
- Sentry init trong `main.py` khi `SENTRY_DSN` set.
- `GET /health`: kiểm tra DB `SELECT 1` + Redis `ping` → `degraded` nếu lỗi.
- Settings: `SENTRY_DSN`, `ENVIRONMENT`.

### 10.11 TASK 11 — Docker Compose

**Đã làm:**
- `backend/Dockerfile`, `fronted/Dockerfile`, `fronted/nginx-spa.conf`.
- `docker-compose.yml`: db, redis, api, worker, frontend.
- `.env.production.example` ở root.

### 10.12 TASK 12 — Cleanup legacy

**Tại sao xóa các file `.vue`?** (theo backlog TASK 12 — *chỉ xóa khi không còn được import*)

| File đã xóa | Lý do |
|-------------|--------|
| `views/Login.vue`, `views/Register.vue` | **Trùng** `views/auth/Login.vue` và `views/auth/Register.vue` — `router/index.js` chỉ trỏ tới `auth/`. |
| `views/Quiz.vue` | **Legacy** — không có route; luồng quiz thật dùng `mock-tests/QuizRunner.vue`. CSS ghi "legacy Quiz.vue". |
| `components/NavBar.vue` | **Dead code** — không file nào `import` NavBar (layout dùng `AppSidebar` + `AppTopbar`). |
| `components/skill/WritingEditor.vue` | **Dead code** — route `/writing/editor` dùng `views/WritingEditor.vue`. |
| `components/skill/AudioPlayer.vue`, `SpeakingRecorder.vue` | **Dead code** — không import; audio/recorder dùng `components/speaking/`. |

**Không bắt buộc xóa vĩnh viễn:** Nếu bạn vẫn cần tham khảo UI cũ, khôi phục bằng:
```bash
git checkout HEAD~1 -- fronted/src/views/Login.vue
# (hoặc commit trước TASK 12)
```

**Đã di chuyển:**
- `backend/model/ielts-speaking.ipynb` → `docs/notebooks/ielts-speaking.ipynb` (notebook R&D, không chạy runtime API).

### 10.13 Post-hardening fixes (2026-05-24)

#### FIX 1 — Alembic migration chain

**Vấn đề:** `001_add_indexes` có `down_revision = None` → conflict khi thêm `initial_schema` sau.

**Đã sửa:**
- Thêm `alembic/versions/20260524_initial_schema.py` (`revision=20260524_initial`, `create_all` từ `Base.metadata`).
- `001_add_indexes.down_revision = "20260524_initial"`.
- `create_index(..., if_not_exists=True)` trong 001 để tránh lỗi index trùng sau `create_all`.

**Chain:**
```
<base> -> 20260524_initial -> 001_add_indexes (head)
```

**Verify:**
```bash
cd backend
python -m alembic history
python -m alembic upgrade head
```

#### FIX 2 — Leaderboard cache + streak

**Vấn đề:** Sort `desc(xp), desc(streak)` nhưng `activity-ping` (chỉ đổi streak) không invalidate cache.

**Đã sửa:** `ProfileRepository.update_streak_and_xp()` gọi `invalidate_leaderboard_cache()` khi **streak hoặc xp** thay đổi — bao phủ:
- `POST /users/me/activity-ping`
- Submit practice (reading/listening)
- `POST /history/save` (history_service)
- Vocabulary session complete
- Speaking evaluate (persist)
- Writing: **không** cộng XP qua `update_streak_and_xp` hiện tại → không cần invalidate riêng.

Các chỗ gọi `invalidate_leaderboard_cache()` trực tiếp trong service vẫn giữ (idempotent).

#### FIX 3 — Health check Celery

**Đã sửa:** Khi `CELERY_ENABLED=true`, `GET /health` thêm key `celery` — `celery_app.control.ping(timeout=2)`. Worker chết → `status: degraded`, `celery: error`. Khi `CELERY_ENABLED=false` → **không** có key `celery`.

#### FIX 4 — `.gitignore` + notebook

**`.gitignore` root:** bổ sung `fronted/dist/`, `uploads/`, `.venv/`, `docs/notebooks/*.ipynb`.

**Notebook:** Đã grep `docs/notebooks/ielts-speaking.ipynb` — không thấy API key/password thật (chủ yếu output HuggingFace / `tokenizer`). **Không** chạy `git filter-branch`. File notebook ignore khỏi commit mới; nếu đã từng commit trước đó vẫn nằm trong history cũ.

---

## 11. Security & deploy fixes (2026-05-24) — từ `update_system.md` Sprint S1

### 11.1 AI endpoints — JWT + rate limit

**Đã làm:**
- `POST /writing/chat` — `Depends(get_current_user)`, `@limiter.limit("30/minute")`.
- `POST /speaking/chat` — JWT + `30/minute`.
- `POST /speaking/analyze-language` — JWT + `20/minute`.

**Frontend:** `WritingEditor.vue` dùng `writingService.js` + `apiClient` (Bearer tự động).

### 11.2 Production DB schema

- `AUTO_CREATE_TABLES` trong `config.py` (mặc định `true`).
- `main.py` `lifespan`: **không** gọi `create_all` khi `ENVIRONMENT=production` hoặc `AUTO_CREATE_TABLES=false`.
- Docker Compose: `AUTO_CREATE_TABLES=false`, chạy `alembic upgrade head` trước khi start API.

### 11.3 Rate limit multi-instance

- `app/core/rate_limit.py`: `storage_uri=REDIS_URL` khi `ENVIRONMENT=production`.

### 11.4 Celery task ownership

- `app/core/task_ownership.py`: Redis key `celery_task_owner:{task_id}` → `user_id`, TTL 1h.
- Đăng ký khi dispatch: speaking evaluate, shadowing process.
- Poll `GET .../result/{task_id}` → `403` nếu user không khớp.

### 11.5 Docker / gateway

- `docker-compose.yml`: service `gateway` (nginx), mount `nginx.docker.conf`; `api` + `frontend` chỉ `expose` nội bộ; volume `./backend/data:/app/data:ro`.
- `nginx.conf` (root): mẫu SSL cho bare-metal; Docker dùng `nginx.docker.conf`.

### 11.6 XSS — DOMPurify (frontend)

- Package `dompurify`; `utils/sanitizeHtml.js`.
- Áp dụng: `QuestionRenderer`, `ReadingPassage`, `GapFillingSet`, `GapFillingHtml`, `WritingEditor` prompt.

### 11.7 Cleanup dead code

- Xóa: `stores/quiz.js`, `stores/vocab.js`, `MockTestList.vue`, `migrate_add_missing_columns.py`.
- `Result.vue` chỉ dùng `practiceStore.lastResult`.
- Route `/guide` → `Guide.vue`.

### 11.8 Chưa làm (backlog P2+)

- httpOnly cookies, refactor `speaking.py` → service layer, Redis ZSET leaderboard, S3 media.

---

## 12. P1 sản phẩm & giới hạn (2026-05-24)

### 12.1 Writing submit + AI band

**API:** `POST /writing/submit` (JWT, rate limit 10/min)

**Body:** `topic_id`, `task_type` (1|2), `essay_text`, `word_count`, `duration_seconds`, `prompt_text?`

**Luồng** (`WritingService`):
1. Kiểm tra `daily_writing_used` < 5 (`ProfileRepository.ensure_writing_submit_allowed`)
2. OpenRouter chấm 4 tiêu chí → JSON `overall_band`, `task_achievement`, `coherence_cohesion`, `lexical_resource`, `grammar_accuracy`, `strengths`, `improvements`, `summary`
3. Fallback khi không có API key: band ước lượng theo word count
4. `HistoryService.save_practice_result` — subject `Writing`, `answers` chứa essay + evaluation
5. `increment_writing_submit` — tăng `daily_writing_used`

**Frontend:** `WritingEditor.vue` — nút «Nộp bài & chấm AI» → `writingService.submitWriting` → redirect `/history` với `state.writingResult`.

### 12.2 Đổi mật khẩu

**API:** `POST /users/me/change-password` — `current_password`, `new_password` (verify + `hash_password`).

**Frontend:** `Profile.vue` + `authService.changePassword` + `auth` store.

### 12.3 Giới hạn sử dụng AI

| Loại | Giới hạn | Lưu trữ |
|------|----------|---------|
| Nộp bài Writing | 5/ngày | `user_profiles.daily_writing_used` |
| Chat Writing coach | 40/ngày | Redis `usage:writing_chat:{user_id}:{date}` |
| Dashboard tutor + chat | 120/tháng | `tutor_questions_used_month` |

Reset ngày/tháng: `_reset_counters_if_period_changed` trong `ProfileRepository` (so sánh `last_activity_date`).

Hằng số: `app/core/limits.py`.

### 12.4 Badges (mở rộng 2026-05-24)

**API:** `GET /users/me/badges` → `BadgeService` (không bảng DB riêng — computed on read).

**32 huy hiệu** (id, title, description ngắn, **`hint`** chi tiết cách mở, **`icon`** = khóa stroke Lucide-style):

| Nhóm | Ví dụ id |
|------|----------|
| Kỹ năng | `reading_3/10`, `reading_perfect`, `listening_3/10`, `writer`, `writer_pro`, `speaker`, `speaker_star` |
| Từ vựng | `word_hunter`, `word_master` |
| Mở rộng | `shadowing_3`, `full_mock_1`, `plan_5` |
| Streak/XP | `streak_3/7/14/30`, `xp_50/100/500/1000` |
| Thành tích | `marathon`, `century`, `sharpshooter`, `band_6/7/8`, `all_rounder`, `balanced`, `dedicated` |

**Nguồn stats:** `user_profiles` + aggregate `history` + `shadowing_user_history` + `study_plan_tasks` (completed count).

**Phát hiện huy hiệu mới sau hoạt động:**
- `BadgeService.get_unlocked_ids()` snapshot **trước** submit
- `BadgeService.detect_new_badges(user, before_unlocked)` **sau** submit
- Trả `new_badges: list[BadgeItem]` trong: `PracticeSubmitResponse`, `WritingSubmitResponse`, `VocabSessionCompleteResponse`

**Frontend:**
- `components/ui/BadgeIcon.vue` — render stroke SVG theo `icon` key
- `views/Profile.vue` — grid + filter (all/unlocked/locked) + popup **hint** (click/hover)
- `stores/badgeCelebration.js` + `components/ui/BadgeCelebration.vue` — overlay confetti sau submit
- Gọi `enqueue(new_badges)` từ: `practice.js`, `WritingEditor.vue`, `useVocabPractice.js`, `FullExamWriting.vue`
- `localStorage` key `ieltstrainer_known_badges` — không popup lại badge đã biết khi load Profile

### 12.5 Leaderboard theo kỳ

**API:** `GET /leaderboard?period=all|weekly|monthly`

- `all`: XP tích lũy (cache Redis như cũ)
- `weekly` / `monthly`: điểm hoạt động = `attempts*10 + avg(band)*10` từ `history` trong 7/30 ngày; field `xp` trong response = điểm hiển thị.

**Frontend:** `Leaderboard.vue` — tab Tất cả / Tuần / Tháng.

### 12.6 Chưa làm (đã chuyển sang §13)

- ~~Forgot/reset password~~ → §13.1
- ~~Full mock exam~~ → §13.2

---

## 13. Forgot password + Full mock exam (2026-05-24)

### 13.1 Quên / đặt lại mật khẩu (SMTP)

**DB:** bảng `password_reset_tokens` (Alembic `002_password_reset`).

**API:**
- `POST /auth/forgot-password` — body `{ email }`, rate limit 5/min. Luôn trả message chung (không lộ email có tồn tại hay không).
- `POST /auth/reset-password` — body `{ token, new_password }`, rate limit 10/min. Revoke refresh tokens sau reset.

**Luồng:**
1. Tạo `secrets.token_urlsafe(32)`, lưu `hash_token` + `expires_at` (mặc định 24h).
2. Gửi email qua `email_service.send_password_reset_email` nếu có `SMTP_HOST` + `SMTP_FROM`.
3. Link: `{FRONTEND_ORIGIN}/reset-password?token=...`
4. Dev không SMTP: log URL trên server; `DEBUG=true` ghi chú trong response.

**Frontend:** `/forgot-password`, `/reset-password`, link trên `Login.vue`.

**Env:** `SMTP_*`, `PASSWORD_RESET_EXPIRE_HOURS`, `FRONTEND_ORIGIN`.

### 13.2 Full mock exam (4 kỹ năng)

**API:**
- `GET /mock-exams/sets` — danh sách bộ (JWT). Ghép Reading + Listening cùng `Orange Test N` + `Test M` từ đường dẫn file.
- `GET /mock-exams/sets/{set_id}` — chi tiết: `reading_quiz_id`, `listening_quiz_id`, `writing_task1_topic_id`, `writing_task2_topic_id`, `speaking_quiz_id`, `timers`, `total_minutes`.

**Speaking mặc định:** mock test speaking đầu tiên tìm thấy trong `backend/data/speaking/`.

**Frontend luồng:**
1. `/full-exam` — chọn bộ → `fullExam` store (sessionStorage).
2. Reading: `/quiz/{reading_quiz_id}?fullExam=1&session=...&stage=reading`
3. Listening: tương tự
4. `/full-exam/writing` — Task 1 → Task 2, nộp 2 lần `POST /writing/submit`
5. Speaking: `/quiz/{speaking_quiz_id}?fullExam=1&...`
6. `/full-exam/result` — tóm tắt band từng kỹ năng

**Màn nghỉ giữa các phần (`FullExamBreak.vue`):**
- Route `/full-exam/break?session=...&after=reading|listening|writing`
- Timer tùy chọn 2 phút; nút «Bỏ qua & tiếp tục» hoặc auto khi hết giờ
- Sau Reading/Listening/Speaking: `QuizRunner._advanceFullExam` → break → stage tiếp theo
- Sau Writing: `FullExamWriting` → break → Speaking
- App full-bleed (ẩn sidebar) cho `/full-exam/break`, `/full-exam/writing`

**Chọn đề Writing/Speaking:** `FullExamService._stable_index(set_id)` — cùng `set_id` luôn trả cùng topic/quiz (không random mỗi lần).

**QuizRunner:** khi `fullExam=1`, sau submit gọi `_advanceFullExam` thay vì trang result riêng.

**Timer:** Reading/Listening/Speaking dùng timer quiz; Writing gộp 20+40 phút.

**Dev email (MailHog):** `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` — UI http://localhost:8025; script `scripts/dev-up.ps1`.

**Hạn chế:** Thi thật không nghỉ giữa Reading và Listening — break chỉ cho luyện tập; Writing/Speaking không ghép đúng book từng Orange Test (chỉ stable hash theo catalog).

---

## 14. Sprint S3 — refactor Speaking + pytest (2026-05-24)

### 14.1 Tách service layer Speaking

| File | Trách nhiệm |
|------|-------------|
| `services/speaking_ai_helpers.py` | OpenRouter, parse JSON, normalize grammar/vocab |
| `services/speaking_audio_utils.py` | load/convert audio, Whisper, pronunciation |
| `services/speaking_eval_service.py` | `evaluate_speaking_core()` — pipeline đánh giá + persist |
| `routers/speaking.py` | HTTP thin (~320 dòng): chat, analyze-language, evaluate, attempt-summary |

**DIP fix:** `speaking_tasks.py` import `evaluate_speaking_core` từ `speaking_eval_service`, không còn từ router.

### 14.2 Pytest

- `backend/tests/`: scoring, history validation, password hash, AI JSON parse
- Chạy: `cd backend && SECRET_KEY=... python -m pytest tests/`

### 14.3 Frontend token

- `auth.js` / `client.js`: ghi `access_token` only; vẫn đọc legacy `token` khi load session cũ

### 14.4 Gộp API trùng (canonical `/users/me/*`, `/history/*`)

| Canonical | Legacy (deprecated headers) |
|-----------|----------------------------|
| `GET /users/me/progress` | `GET /progress` |
| `GET /users/me/stats` | `GET /user/stats` |
| `GET /history`, `/history/sessions/{id}`, `/history/quiz/{id}` | `GET /practice/history*` |

- `app/core/deprecation.py` — header `Deprecation: true` + `Link` successor
- Frontend: `ieltsService.js`, `practiceService.js`, `ielts.js` fetchPracticeAnalytics

### 14.5 Playwright E2E

- `fronted/playwright.config.js` — Vite dev server + global setup tạo user E2E
- `fronted/e2e/` — auth, dashboard, navigation specs
- Chạy: backend `:8000` trước, rồi `cd fronted && npm run test:e2e`
- Env tuỳ chọn: `E2E_USER_EMAIL` (mặc định `e2e@example.com`), `E2E_USER_PASSWORD`, `E2E_API_URL`, `PLAYWRIGHT_BASE_URL`
- Global setup lưu `e2e/.auth/user.json` (storageState) — tránh rate-limit login song song
- Navigation test: click link trong `nav` sidebar (tránh trùng link Reading trên dashboard)
- Fix backend local: bỏ `from __future__ import annotations` trong `speaking.py` (UploadFile + FastAPI)

---

## 15. Sprint S4 — scale (2026-05-24)

| Hạng mục | Chi tiết |
|----------|----------|
| Redis ZSET | `app/core/leaderboard_redis.py`, key `leaderboard:xp:all` |
| Sync XP | `ProfileRepository.update_streak_and_xp` → `sync_user_xp` |
| Cron rebuild | Celery `leaderboard.rebuild_zset` mỗi 6h + service `beat` |
| PgBouncer | `docker-compose.yml` service `pgbouncer`, `PGBOUNCER_ENABLED` |
| Redis prod | `REDIS_REQUIRED`, startup fail + `/health` 503 |
| Docs | `docs/SCALE.md` |

### 15.1 MinIO + Prometheus (tiếp)

| Hạng mục | Chi tiết |
|----------|----------|
| Storage | `app/core/storage.py` — local / S3 (boto3) |
| Avatar | `PUT /users/me/avatar` → `/media/avatars/...` (S3) hoặc `/uploads/...` (local) |
| MinIO | `docker-compose.yml`: `minio`, `minio-init`, nginx `/media/` |
| Metrics | `app/core/metrics.py`, `GET /metrics` |
| Monitoring | `docker-compose.monitoring.yml` — Prometheus + Grafana |

### 15.2 Quiz assets S3 + history archive + ML offload

| Hạng mục | Chi tiết |
|----------|----------|
| Media | `media_assets.py`, redirect `/audio` `/images` → `/media/assets/...` |
| Sync script | `scripts/sync_quiz_assets_to_s3.py` |
| Archive | `history_archive` + `history.archive_old` weekly |
| ML | `ML_PRELOAD_ON_STARTUP` — false on API; `ml-worker` queue speaking/shadowing |

### 15.3 httpOnly refresh + CSRF + CDN doc

| Hạng mục | Chi tiết |
|----------|----------|
| Cookies | `app/core/auth_cookies.py`, `AUTH_HTTPONLY_REFRESH` |
| CSRF | `CsrfMiddleware` + `X-CSRF-Token` |
| Frontend | `withCredentials`, không lưu refresh vào localStorage (prod) |
| CDN | `docs/CDN.md` — `S3_PUBLIC_BASE_URL` |

---

---

## 16. Adaptive Study Plan + SRS đa kỹ năng (2026-05-24)

### 16.1 Vấn đề spec

- Study plan trước đây: AI tạo **một lần** (`POST /users/me/study-plan/generate`), tĩnh — không đổi độ khó sau mỗi bài.
- Vocabulary đã có SM-2 (`vocab_srs.py`); cần **cùng ý tưởng** cho Reading, Listening, Writing, Speaking, Vocabulary.

### 16.2 Quyết định kiến trúc

| Thành phần | File | Trách nhiệm |
|------------|------|-------------|
| Bảng SRS | `skill_adaptive_states` | Per `(user_id, skill)`: ease, interval, repetitions, `srs_next_review_at`, `suggested_difficulty`, `avg_performance` |
| Service | `app/services/adaptive_study_service.py` | `record_activity`, `refresh_plan_priorities`, `get_next_task` |
| Cột plan | `study_plan_tasks.suggested_difficulty`, `priority_score` | Cập nhật sau mỗi hoạt động |

**Skills:** `reading`, `listening`, `writing`, `speaking`, `vocabulary` — map từ `History.subject`.

**Chất lượng → SM-2 quality (0–5):**
- Có `band_score`: map band 5–8+ → quality 1–5
- Không band: dùng `percentage` (50%→1 … 90%+→5)

**Độ khó gợi ý:** `easy` | `medium` | `hard` | `challenge` — từ repetitions + ease + quality lần cuối.

### 16.3 Hook sau mỗi lần làm bài

Gọi `AdaptiveStudyService.record_activity(user_id, subject, percentage=, band_score=)` từ:

| Luồng | File |
|-------|------|
| History canonical | `history_service.save_practice_result` (Writing + `/history/save`) |
| Practice R/L | `practice_service.submit` |
| Vocab session | `vocab_service.complete_study_session` |

Sau `record_activity` → `refresh_plan_priorities(user_id)` cập nhật `priority_score` + `suggested_difficulty` trên task **chưa hoàn thành**.

### 16.4 API next-task

**`GET /users/me/study-plan/next-task`** → `StudyPlanNextTaskResponse`:

| Field | Ý nghĩa |
|-------|---------|
| `source` | `study_plan` (có task trong DB) hoặc `adaptive` (gợi ý synthetic) |
| `task` | `StudyPlanTaskResponse` nếu có |
| `focus_skill`, `suggested_difficulty`, `difficulty_label` | Kỹ năng + mức độ |
| `reason` | Giải thích (hôm nay / SRS due / điểm thấp) |
| `route_path`, `synthetic_description`, `duration_minutes` | Khi chưa có plan |

**Ưu tiên task:** `priority_score` DESC (due SRS + weakness + task hôm nay).

**Side effect:** Gọi `NotificationService.maybe_streak_reminder` — tạo in-app notification nếu streak có nguy cơ mất.

### 16.5 Frontend

- `GET /users/me/study-plan/next-task` qua `notificationService.fetchNextStudyTask` / `ieltsService.getNextStudyTask`
- `DashboardStudyPlan.vue` — card **«Nhiệm vụ ưu tiên»** + nút «Bắt đầu ngay»
- Sau generate/extend plan: backend gọi `refresh_plan_priorities`

### 16.6 Tradeoff

- **Không** regenerate AI plan mỗi submit — chỉ cập nhật priority/difficulty (nhẹ, không tốn OpenRouter).
- Synthetic task khi user chưa generate plan — vẫn có gợi ý SRS.
- Speaking chưa hook riêng nếu không qua `History` — cần đảm bảo speaking evaluate ghi history.

### 16.7 Migration

`alembic/versions/004_adaptive_notifications.py` — `skill_adaptive_states`, cột study plan, bảng notifications (xem §17).

---

## 17. Hệ thống thông báo & nhắc nhở (2026-05-24)

### 17.1 Spec

- Streak + study plan đã có nhưng **không có** nhắc nhở tập trung.
- Cần: cấu hình giờ/kênh, in-app, email hàng ngày, chuẩn bị PWA push.

### 17.2 CSDL

| Bảng | Mục đích |
|------|----------|
| `notification_settings` | 1 row/user: `reminder_enabled`, `reminder_time`, `channel` (`in_app`\|`email`\|`both`), `email_daily_digest`, `push_enabled`, `timezone` |
| `notifications` | In-app: `type`, `title`, `body`, `link_path`, `is_read`, `created_at` |

### 17.3 API

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/users/me/notifications` | Danh sách + `unread_count` |
| PATCH | `/users/me/notifications/{id}/read` | Đánh dấu đã đọc |
| POST | `/users/me/notifications/read-all` | Đọc hết |
| GET | `/users/me/notifications/settings` | Lấy cấu hình |
| POST | `/users/me/notifications/settings` | Cập nhật (`NotificationSettingsRequest`) |

**Service:** `app/services/notification_service.py`

- `maybe_streak_reminder(user)` — tối đa 1 notification `streak_reminder`/ngày nếu streak > 0 và chưa active hôm nay
- `notify_badge_unlocked` — helper (có thể gọi từ badge flow sau này)
- `send_daily_reminders_for_all(db)` — email digest qua SMTP

### 17.4 Email hàng ngày

- `email_service.send_daily_study_reminder_email`
- Celery beat: `notifications.daily_reminders` (24h) — `app/tasks/notification_tasks.py`
- Chỉ gửi khi `reminder_enabled` + `email_daily_digest` + SMTP configured

### 17.5 Frontend

- `components/layout/NotificationBell.vue` — topbar, dropdown list + form settings
- `stores/notifications.js`, `services/notificationService.js`
- **PWA push:** `push_enabled` trong settings — UI disabled «sắp có»; chưa Web Push subscription

### 17.6 Tradeoff

- In-app streak reminder kích hoạt khi user gọi `next-task` (không background job riêng theo giờ — cần cron/worker nếu muốn đúng `reminder_time`).
- Email digest chạy Celery 1 lần/ngày — không theo timezone user chi tiết (backlog).

---

---

## 18. Git — file cần ignore khi push (2026-05-24)

> Cấu hình chính: **`.gitignore`** ở root repo. Không ignore theo *chức năng* (badges, study plan, …) — chỉ ignore **secret, build, data lớn, runtime**.

### 18.1 Bắt buộc ignore

| Pattern | Lý do |
|---------|--------|
| `.env`, `backend/.env`, `fronted/.env`, `.env.production`, `.env.local` | API keys, `SECRET_KEY`, DB/SMTP |
| `backend/data/` | ~1400+ JSON đề + audio/images — deploy riêng (Docker volume / S3) |
| `backend/uploads/`, `uploads/` | Avatar user upload |
| `*.db`, `*.sqlite`, `backend/temp_alembic.db` | SQLite dev / Alembic tạm |
| `fronted/node_modules/`, `fronted/dist/` | Cài lại / build lại |
| `__pycache__/`, `*.pyc`, `.pytest_cache/` | Python cache & test |
| `*.pt` | ML model weights |
| `docs/notebooks/*.ipynb` | Notebook lớn |

### 18.2 Ignore — tài liệu nội bộ (local only)

| File | Lý do |
|------|--------|
| `implementation-notes.md` | Spec/tradeoff nội bộ — **gitignore** |
| `update_system.md` | Đánh giá/review nội bộ — **gitignore** |
| `docs/HE_THONG.md` | Map hệ thống chi tiết — **gitignore** |

Giữ bản local / OneDrive / chia sẻ ngoài Git. Repo public chỉ cần `backend/README.md`, `docs/DEPLOY.md` (nếu có).

### 18.3 Nên commit (không ignore)

| Loại | Ví dụ |
|------|--------|
| Source | `backend/app/`, `fronted/src/` (mọi feature kể cả adaptive, notifications, badges) |
| Migration | `backend/alembic/versions/*.py` |
| Docs deploy | `docs/DEPLOY.md`, `backend/README.md` |
| Template env | `.env.production.example`, `backend/.env.example` |
| Infra | `docker-compose*.yml`, `Dockerfile`, `nginx*.conf`, `scripts/` |
| Tests | `backend/tests/`, `fronted/e2e/*.spec.js` (không commit `test-results/`) |

### 18.4 Trước khi `git push`

```bash
git status   # không thấy .env, backend/data/, node_modules/
```

Nếu từng commit nhầm `.env` → đổi toàn bộ secret + `git filter-repo` (không chỉ thêm `.gitignore`).

Clone mới cần: copy `backend/.env.example` → `.env`, sync `backend/data/` (hoặc volume Docker), `npm install` trong `fronted/`.

---

*Last updated: 2026-05-24 (§16–18)*
