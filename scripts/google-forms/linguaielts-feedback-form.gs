/**
 * LinguaIELTS — User Feedback Form (Google Apps Script)
 * ─────────────────────────────────────────────────────
 * Cách dùng:
 * 1. Mở https://script.google.com → New project
 * 2. Dán toàn bộ file này vào Code.gs
 * 3. Chạy hàm `createFeedbackForm` (lần đầu cần Authorize)
 * 4. Xem log (View → Logs) để lấy link Form + Sheet
 * 5. Chạy `installSubmitTrigger` một lần để bật email thông báo
 *
 * Tuỳ chọn: đổi NOTIFY_EMAIL trước khi chạy.
 */

const NOTIFY_EMAIL = 'your-email@vku.edu.vn'; // ← đổi email nhận thông báo
const FORM_TITLE = 'LinguaIELTS — Khảo sát phản hồi người dùng';
const FORM_DESCRIPTION = [
  'Cảm ơn bạn đã dùng thử LinguaIELTS!',
  '',
  'Khảo sát này mất khoảng 5 phút. Phản hồi của bạn giúp nhóm phát triển cải thiện sản phẩm cho đồ án tốt nghiệp.',
  '',
  'Lưu ý: Điểm AI trên website chỉ mang tính luyện tập (formative), không phải band IELTS chính thức.',
].join('\n');

/** Danh sách tính năng — dùng cho checkbox */
const FEATURES = [
  'Dashboard (Tổng quan)',
  'Dashboard — Tab Forecast (Dự báo điểm)',
  'Dashboard — Tab Study Plan (Kế hoạch học)',
  'Placement test (Kiểm tra trình độ đầu vào)',
  'Reading (Đọc hiểu)',
  'Listening (Nghe hiểu)',
  'Writing IELTS (Viết Task 1/2)',
  'Translation (Dịch Việt → Anh)',
  'Speaking (Nói + chấm AI)',
  'Shadowing (Luyện nói theo video)',
  'Conversation (Hội thoại mô phỏng)',
  'Từ vựng (Vocabulary / Flashcard)',
  'Full Mock Exam (Thi thử 4 kỹ năng)',
  'Lịch sử làm bài',
  'Bảng xếp hạng',
  'Hồ sơ / Huy hiệu (Profile & Badges)',
];

/**
 * Tạo Form + Sheet mới. Chạy một lần.
 */
function createFeedbackForm() {
  const ss = SpreadsheetApp.create('LinguaIELTS — Feedback Responses');
  const form = FormApp.create(FORM_TITLE);
  form.setDescription(FORM_DESCRIPTION);
  form.setConfirmationMessage(
    'Cảm ơn bạn! Phản hồi đã được ghi nhận. Chúc bạn ôn IELTS hiệu quả! 🎓'
  );
  form.setCollectEmail(true); // thu email Google (có thể tắt)
  form.setAllowResponseEdits(false);
  form.setShowLinkToRespondAgain(false);

  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // ── 1. Thông tin cơ bản ──────────────────────────────────────────────
  form.addSectionHeaderItem()
    .setTitle('Thông tin chung')
    .setHelpText('Phần này giúp nhóm hiểu bối cảnh sử dụng của bạn.');

  form.addTextItem()
    .setTitle('Họ tên (tuỳ chọn)')
    .setHelpText('Có thể để trống nếu muốn ẩn danh');

  form.addListItem()
    .setTitle('Bạn là ai?')
    .setChoices([
      form.createChoice('Sinh viên VKU / đại học'),
      form.createChoice('Sinh viên trường khác'),
      form.createChoice('Người đi làm / tự ôn IELTS'),
      form.createChoice('Giáo viên / trung tâm tiếng Anh'),
      form.createChoice('Khác'),
    ])
    .setRequired(true);

  form.addListItem()
    .setTitle('Bạn đã dùng LinguaIELTS bao lâu trong phiên này?')
    .setChoices([
      form.createChoice('Dưới 15 phút'),
      form.createChoice('15–30 phút'),
      form.createChoice('30–60 phút'),
      form.createChoice('Trên 1 giờ'),
      form.createChoice('Đã quay lại nhiều lần (>1 ngày)'),
    ])
    .setRequired(true);

  form.addTextItem()
    .setTitle('Link hoặc mô tả ngắn về phiên dùng thử (tuỳ chọn)')
    .setHelpText('VD: đã làm Writing Task 2 + Speaking Part 2');

  // ── 2. Tính năng đã thử ─────────────────────────────────────────────
  form.addSectionHeaderItem()
    .setTitle('Tính năng đã sử dụng')
    .setHelpText('Chọn tất cả mục bạn đã mở hoặc thử (có thể chọn nhiều).');

  form.addCheckboxItem()
    .setTitle('Bạn đã thử những tính năng nào?')
    .setChoices(FEATURES.map((f) => form.createChoice(f)))
    .setRequired(true);

  form.addListItem()
    .setTitle('Tính năng bạn dùng nhiều nhất')
    .setChoices(FEATURES.map((f) => form.createChoice(f)))
    .setRequired(true);

  // ── 3. Đánh giá Likert ───────────────────────────────────────────────
  form.addSectionHeaderItem()
    .setTitle('Đánh giá trải nghiệm')
    .setHelpText('1 = Rất không đồng ý · 5 = Rất đồng ý');

  const likert = (title, help) =>
    form.addScaleItem()
      .setTitle(title)
      .setBounds(1, 5)
      .setLabels('Rất không đồng ý', 'Rất đồng ý')
      .setHelpText(help || '')
      .setRequired(true);

  likert('Giao diện website dễ sử dụng, dễ tìm chức năng');
  likert('Website chạy ổn định, không bị lỗi / treo nhiều');
  likert('Tốc độ phản hồi AI (Writing / Speaking) chấp nhận được', 'Bỏ qua nếu chưa thử W/S');
  likert('Phản hồi AI Writing hữu ích và gần với rubric IELTS', 'Chỉ đánh giá nếu đã làm Writing');
  likert('Phản hồi AI Speaking hữu ích (band + nhận xét)', 'Chỉ đánh giá nếu đã làm Speaking');
  likert('Reading / Listening: đề bài và chấm điểm hợp lý', 'Chỉ đánh giá nếu đã làm R/L');
  likert('Dashboard / Forecast / Study Plan giúp biết nên ôn gì tiếp');
  likert('Từ vựng / Shadowing / Conversation hỗ trợ luyện nói tốt', 'Chỉ đánh giá nếu đã thử');
  likert('Tôi sẽ quay lại dùng LinguaIELTS để ôn IELTS');

  // ── 4. NPS ───────────────────────────────────────────────────────────
  form.addSectionHeaderItem()
    .setTitle('Khuyến nghị')
    .setHelpText('0 = Không bao giờ giới thiệu · 10 = Chắc chắn giới thiệu');

  form.addScaleItem()
    .setTitle('Bạn có khuyên bạn bè dùng thử LinguaIELTS không? (NPS)')
    .setBounds(0, 10)
    .setLabels('0 — Không', '10 — Chắc chắn')
    .setRequired(true);

  // ── 5. Câu hỏi mở ───────────────────────────────────────────────────
  form.addSectionHeaderItem()
    .setTitle('Ý kiến chi tiết');

  form.addParagraphTextItem()
    .setTitle('Điều bạn thích nhất về LinguaIELTS')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Tính năng hoặc phần cần cải thiện nhất')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Lỗi kỹ thuật bạn gặp (nếu có)')
    .setHelpText('VD: không ghi âm được, AI chậm, không load được đề…')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('Góp ý thêm cho nhóm phát triển')
    .setRequired(false);

  // ── Lưu link vào Properties (dùng cho trigger) ─────────────────────
  const props = PropertiesService.getScriptProperties();
  props.setProperties({
    FORM_ID: form.getId(),
    SHEET_ID: ss.getId(),
    FORM_URL: form.getPublishedUrl(),
    EDIT_URL: form.getEditUrl(),
  });

  Logger.log('✅ Đã tạo Form + Sheet');
  Logger.log('📋 Form (gửi người dùng): ' + form.getPublishedUrl());
  Logger.log('✏️  Form (sửa câu hỏi):   ' + form.getEditUrl());
  Logger.log('📊 Sheet (xem phản hồi):  ' + ss.getUrl());

  return {
    formUrl: form.getPublishedUrl(),
    sheetUrl: ss.getUrl(),
  };
}

/**
 * Gửi email khi có phản hồi mới. Chạy `installSubmitTrigger` một lần.
 */
function onFormSubmit(e) {
  if (!e || !e.values) return;

  const row = e.values;
  const timestamp = row[0] || '';
  const email = row[1] || '(không có email)';

  // Cột có thể lệch nếu Google thêm cột Email — lấy câu mở cuối làm preview
  const preview = row[row.length - 1] || row[row.length - 2] || '';

  if (NOTIFY_EMAIL && NOTIFY_EMAIL !== 'your-email@vku.edu.vn') {
  try {
    MailApp.sendEmail({
      to: NOTIFY_EMAIL,
      subject: '[LinguaIELTS] Phản hồi mới — ' + timestamp,
      body: [
        'Có phản hồi mới trên form LinguaIELTS.',
        '',
        'Thời gian: ' + timestamp,
        'Email: ' + email,
        '',
        'Xem trước:',
        String(preview).substring(0, 500),
        '',
        'Mở Sheet: ' + (PropertiesService.getScriptProperties().getProperty('SHEET_ID')
          ? 'https://docs.google.com/spreadsheets/d/' +
            PropertiesService.getScriptProperties().getProperty('SHEET_ID')
          : '(chạy createFeedbackForm trước)'),
      ].join('\n'),
    });
  } catch (err) {
    Logger.log('Không gửi được email: ' + err);
  }
  }

  appendSummaryRow_(e);
}

/**
 * Ghi dòng tóm tắt vào sheet "Summary" (TB Likert, NPS).
 */
function appendSummaryRow_(e) {
  const sheetId = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!sheetId) return;

  const ss = SpreadsheetApp.openById(sheetId);
  let summary = ss.getSheetByName('Summary');
  if (!summary) {
    summary = ss.insertSheet('Summary');
    summary.appendRow([
      'Cập nhật lúc',
      'Tổng phản hồi',
      'TB UI (cột 9)',
      'TB AI Writing (cột 12)',
      'TB AI Speaking (cột 13)',
      'TB Dashboard (cột 15)',
      'TB NPS (cột 18)',
    ]);
  }

  const responses = ss.getSheets()[0];
  const lastRow = responses.getLastRow();
  const total = Math.max(0, lastRow - 1);

  if (total === 0) return;

  // Cột Likert: 9–16 (1-based), NPS: 18 — điều chỉnh nếu đổi thứ tự câu hỏi
  const likertCols = [9, 10, 11, 12, 13, 14, 15, 16];
  const npsCol = 18;

  const avg = (col) => {
    const vals = responses.getRange(2, col, total, 1).getValues().flat()
      .map(Number).filter((n) => !isNaN(n) && n > 0);
    if (!vals.length) return '';
    return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2);
  };

  summary.appendRow([
    new Date(),
    total,
    avg(9),
    avg(12),
    avg(13),
    avg(15),
    avg(npsCol),
  ]);
}

/**
 * Cài trigger onFormSubmit. Chạy một lần sau createFeedbackForm.
 */
function installSubmitTrigger() {
  const formId = PropertiesService.getScriptProperties().getProperty('FORM_ID');
  if (!formId) {
    throw new Error('Chạy createFeedbackForm() trước!');
  }

  // Xóa trigger cũ trùng tên
  ScriptApp.getProjectTriggers().forEach((t) => {
    if (t.getHandlerFunction() === 'onFormSubmit') {
      ScriptApp.deleteTrigger(t);
    }
  });

  ScriptApp.newTrigger('onFormSubmit')
    .forForm(formId)
    .onFormSubmit()
    .create();

  Logger.log('✅ Đã cài trigger onFormSubmit');
}

/**
 * In lại link Form/Sheet từ Properties (không tạo mới).
 */
function showFormLinks() {
  const p = PropertiesService.getScriptProperties();
  Logger.log('Form:  ' + (p.getProperty('FORM_URL') || '(chưa tạo)'));
  Logger.log('Sheet: https://docs.google.com/spreadsheets/d/' + (p.getProperty('SHEET_ID') || ''));
}

/**
 * Tạo sheet phân tích cơ bản (pivot-friendly) trên tab "Analysis".
 */
function buildAnalysisSheet() {
  const sheetId = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!sheetId) throw new Error('Chạy createFeedbackForm() trước!');

  const ss = SpreadsheetApp.openById(sheetId);
  const data = ss.getSheets()[0];
  let analysis = ss.getSheetByName('Analysis');
  if (!analysis) analysis = ss.insertSheet('Analysis');
  analysis.clear();

  const lastRow = data.getLastRow();
  const total = Math.max(0, lastRow - 1);

  analysis.getRange('A1').setValue('LinguaIELTS — Tóm tắt phản hồi');
  analysis.getRange('A3').setValue('Tổng phản hồi');
  analysis.getRange('B3').setValue(total);

  const metrics = [
    ['Tiêu chí', 'TB (1–5)', 'Ghi chú'],
    ['Giao diện dễ dùng', avgCol_(data, 9, total), ''],
    ['Ổn định / ít lỗi', avgCol_(data, 10, total), ''],
    ['Tốc độ AI', avgCol_(data, 11, total), ''],
    ['AI Writing', avgCol_(data, 12, total), ''],
    ['AI Speaking', avgCol_(data, 13, total), ''],
    ['Reading/Listening', avgCol_(data, 14, total), ''],
    ['Dashboard / Forecast', avgCol_(data, 15, total), ''],
    ['Vocab / Shadowing / Conv', avgCol_(data, 16, total), ''],
    ['Sẽ quay lại dùng', avgCol_(data, 17, total), ''],
    ['NPS (0–10)', avgCol_(data, 18, total), 'Promoter−Detractor tính thủ công'],
  ];

  analysis.getRange(5, 1, metrics.length, 3).setValues(metrics);
  analysis.autoResizeColumns(1, 3);

  Logger.log('✅ Đã cập nhật sheet Analysis');
}

function avgCol_(sheet, col, total) {
  if (total <= 0) return '';
  const vals = sheet.getRange(2, col, total, 1).getValues().flat()
    .map(Number).filter((n) => !isNaN(n) && n > 0);
  if (!vals.length) return '';
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2);
}
