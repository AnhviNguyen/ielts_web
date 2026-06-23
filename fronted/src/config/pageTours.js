/** Spotlight tour steps — each step targets a [data-tour] element on the page. */

function skillSteps(skillLabel, pathLabel) {
  return {
    title: skillLabel,
    steps: [
      {
        target: '[data-tour="sidebar-nav"]',
        title: 'Menu luyện tập',
        description: `Chọn ${pathLabel} hoặc kỹ năng khác từ menu bên trái bất cứ lúc nào.`,
        side: 'right',
      },
      {
        target: '[data-tour="page-header"]',
        title: `Trang ${skillLabel}`,
        description: 'Xem tổng số đề và thông tin chung của kỹ năng này.',
        side: 'bottom',
      },
      {
        target: '[data-tour="page-search"]',
        title: 'Tìm đề',
        description: 'Gõ tên bài hoặc mã sách để lọc nhanh danh sách đề thi.',
        side: 'bottom',
      },
      {
        target: '[data-tour="test-grid"]',
        title: 'Chọn bài luyện',
        description: 'Nhấn "Full test" cho cả bài hoặc chọn từng Part. Sau đó chọn Luyện tập hoặc Thi thật.',
        side: 'top',
      },
    ],
  }
}

export const PAGE_TOURS = {
  dashboard: {
    title: 'Dashboard',
    steps: [
      {
        target: '[data-tour="sidebar-nav"]',
        title: 'Menu điều hướng',
        description: 'Truy cập Reading, Listening, Writing, Speaking và các tính năng khác từ đây.',
        side: 'right',
      },
      {
        target: '[data-tour="dashboard-header"]',
        title: 'Streak & mục tiêu',
        description: 'Theo dõi chuỗi ngày luyện tập và band mục tiêu. Cập nhật mục tiêu trong Profile.',
        side: 'bottom',
      },
      {
        target: '[data-tour="dashboard-tabs"]',
        title: 'Các tab Dashboard',
        description: 'Home, Reports, Dự báo điểm, Progress và Study Plan — mỗi tab một góc nhìn khác nhau.',
        side: 'bottom',
      },
      {
        target: '[data-tour="dashboard-catbot"]',
        title: 'Catbot — AI Coach',
        description: 'Hỏi mẹo IELTS, chiến lược luyện thi hoặc giải thích band score bất cứ lúc nào.',
        side: 'top',
      },
      {
        target: '[data-tour="dashboard-skills"]',
        title: 'Luyện nhanh theo kỹ năng',
        description: 'Nhấp vào từng ô để chuyển thẳng sang trang luyện tập tương ứng.',
        side: 'top',
      },
    ],
  },
  'dashboard-reports': {
    title: 'Reports',
    steps: [
      {
        target: '[data-tour="dashboard-tabs"]',
        title: 'Tab Reports',
        description: 'Bạn đang xem báo cáo tuần — chuyển tab để xem dự báo hoặc tiến độ.',
        side: 'bottom',
      },
      {
        target: '[data-tour="reports-bands"]',
        title: 'Band score hiện tại',
        description: '5 ô điểm Overall và từng kỹ năng — so sánh với mục tiêu band của bạn.',
        side: 'bottom',
      },
      {
        target: '[data-tour="reports-radar"]',
        title: 'Skill Radar',
        description: 'Biểu đồ radar cho thấy điểm mạnh/yếu — luyện thêm kỹ năng thấp nhất.',
        side: 'top',
      },
    ],
  },
  'dashboard-forecast': {
    title: 'Dự báo điểm',
    steps: [
      {
        target: '[data-tour="dashboard-tabs"]',
        title: 'Tab Dự báo',
        description: 'Mô hình AI dự đoán xu hướng band dựa trên lịch sử luyện tập hàng ngày.',
        side: 'bottom',
      },
      {
        target: '[data-tour="forecast-skills"]',
        title: 'Chọn kỹ năng',
        description: 'Xem dự báo Overall hoặc từng skill Reading, Listening, Writing, Speaking.',
        side: 'bottom',
      },
      {
        target: '[data-tour="forecast-chart"]',
        title: 'Biểu đồ dự báo',
        description: 'Đường liền = điểm thực tế; đường đứt + vùng xanh = dự báo 14 ngày tới. Cần ~14 ngày dữ liệu.',
        side: 'top',
      },
    ],
  },
  'dashboard-progress': {
    title: 'Progress',
    steps: [
      {
        target: '[data-tour="dashboard-tabs"]',
        title: 'Tab Progress',
        description: 'Theo dõi % hoàn thành bài tập và band trung bình từng kỹ năng.',
        side: 'bottom',
      },
      {
        target: '[data-tour="progress-skills"]',
        title: 'Tiến độ từng kỹ năng',
        description: 'Thanh tiến độ cho biết bạn đã làm bao nhiêu % ngân hàng đề.',
        side: 'top',
      },
    ],
  },
  'dashboard-study': {
    title: 'Study Plan',
    steps: [
      {
        target: '[data-tour="dashboard-tabs"]',
        title: 'Tab Study Plan',
        description: 'Lộ trình gợi ý bài luyện phù hợp mục tiêu band và điểm yếu của bạn.',
        side: 'bottom',
      },
      {
        target: '[data-tour="study-plan"]',
        title: 'Bài gợi ý hôm nay',
        description: 'Hoàn thành từng bài để cập nhật tiến độ, streak và dữ liệu dự báo.',
        side: 'top',
      },
    ],
  },
  reading: skillSteps('Reading', 'Reading'),
  listening: skillSteps('Listening', 'Listening'),
  speaking: skillSteps('Speaking', 'Speaking'),
  writing: skillSteps('Writing', 'Writing'),
  'writing-hub': {
    title: 'Writing',
    steps: [
      {
        target: '[data-tour="sidebar-nav"]',
        title: 'Menu',
        description: 'Writing gồm IELTS Writing và luyện dịch câu.',
        side: 'right',
      },
      {
        target: '[data-tour="writing-hub-cards"]',
        title: 'Chọn loại bài',
        description: 'IELTS Writing (Task 1/2) hoặc Translation — luyện dịch theo chủ đề.',
        side: 'top',
      },
    ],
  },
  'writing-translation': {
    title: 'Translation',
    steps: [
      {
        target: '[data-tour="page-header"]',
        title: 'Luyện dịch',
        description: 'Chọn chủ đề và làm tuần tự từng bước dịch Việt–Anh.',
        side: 'bottom',
      },
      {
        target: '[data-tour="test-grid"]',
        title: 'Danh sách chủ đề',
        description: 'Mỗi topic có nhiều bước — hoàn thành để mở khóa bước tiếp theo.',
        side: 'top',
      },
    ],
  },
  vocabulary: {
    title: 'Từ vựng',
    steps: [
      {
        target: '[data-tour="sidebar-nav"]',
        title: 'Menu',
        description: 'Quay lại Dashboard hoặc chuyển sang kỹ năng khác.',
        side: 'right',
      },
      {
        target: '[data-tour="page-header"]',
        title: 'Học từ vựng FSRS',
        description: 'Flashcard thông minh — hệ thống tự lên lịch ôn theo mức độ nhớ.',
        side: 'bottom',
      },
      {
        target: '[data-tour="vocab-topics"]',
        title: 'Chọn bộ từ',
        description: 'Mỗi topic là một chủ đề IELTS. Nhấp "Luyện tập" để bắt đầu flashcard.',
        side: 'top',
      },
    ],
  },
  'vocabulary-practice': {
    title: 'Flashcard',
    steps: [
      {
        target: '[data-tour="vocab-flashcard"]',
        title: 'Thẻ từ vựng',
        description: 'Xem từ + IPA, nhấp để lật xem nghĩa và ví dụ.',
        side: 'bottom',
      },
      {
        target: '[data-tour="vocab-rating"]',
        title: 'Đánh giá mức nhớ',
        description: 'Chọn Quên / Khó / Ổn / Dễ — thuật toán FSRS sẽ lên lịch ôn phù hợp.',
        side: 'top',
      },
    ],
  },
  shadowing: {
    title: 'Shadowing',
    steps: [
      {
        target: '[data-tour="page-header"]',
        title: 'Shadowing',
        description: 'Luyện phát âm bằng cách bắt chước video YouTube có transcript.',
        side: 'bottom',
      },
      {
        target: '[data-tour="shadowing-url"]',
        title: 'Dán link YouTube',
        description: 'Dán URL video, chọn trình độ và bấm Tải transcript để bắt đầu.',
        side: 'top',
      },
    ],
  },
  conversation: {
    title: 'Conversation',
    steps: [
      {
        target: '[data-tour="page-header"]',
        title: 'Hội thoại AI',
        description: 'Luyện nói theo chủ đề với trợ lý AI — mô phỏng tình huống thực tế.',
        side: 'bottom',
      },
      {
        target: '[data-tour="test-grid"]',
        title: 'Chọn chủ đề',
        description: 'Nhấp vào topic để vào phòng luyện tập hội thoại.',
        side: 'top',
      },
    ],
  },
  'full-exam': {
    title: 'Full Mock',
    steps: [
      {
        target: '[data-tour="page-header"]',
        title: 'Thi thử 4 kỹ năng',
        description: 'Làm bộ đề đầy đủ Reading → Listening → Writing → Speaking như thi thật.',
        side: 'bottom',
      },
      {
        target: '[data-tour="test-grid"]',
        title: 'Chọn bộ đề',
        description: 'Mỗi set gồm đủ 4 phần. Có giờ nghỉ giữa các kỹ năng.',
        side: 'top',
      },
    ],
  },
  history: {
    title: 'Lịch sử',
    steps: [
      {
        target: '[data-tour="page-header"]',
        title: 'Lịch sử luyện tập',
        description: 'Xem lại mọi bài đã làm và band score từng lần.',
        side: 'bottom',
      },
      {
        target: '[data-tour="history-filters"]',
        title: 'Lọc theo kỹ năng',
        description: 'Lọc Reading, Listening, Writing, Speaking hoặc xem tất cả.',
        side: 'bottom',
      },
      {
        target: '[data-tour="history-list"]',
        title: 'Danh sách bài làm',
        description: 'Nhấp vào bài để xem chi tiết đáp án hoặc kết quả chấm.',
        side: 'top',
      },
    ],
  },
  profile: {
    title: 'Hồ sơ',
    steps: [
      {
        target: '[data-tour="profile-avatar"]',
        title: 'Ảnh đại diện',
        description: 'Tải avatar và cập nhật thông tin cá nhân.',
        side: 'bottom',
      },
      {
        target: '[data-tour="profile-target"]',
        title: 'Mục tiêu & ngày thi',
        description: 'Đặt band mục tiêu và ngày thi — kích hoạt đếm ngược trên Dashboard.',
        side: 'top',
      },
    ],
  },
  leaderboard: {
    title: 'Bảng xếp hạng',
    steps: [
      {
        target: '[data-tour="page-header"]',
        title: 'Bảng xếp hạng',
        description: 'So sánh XP và streak với cộng đồng LinguaIELTS.',
        side: 'bottom',
      },
      {
        target: '[data-tour="leaderboard-table"]',
        title: 'Xếp hạng',
        description: 'Kiếm XP bằng cách luyện bài mỗi ngày và duy trì streak.',
        side: 'top',
      },
    ],
  },
  quiz: {
    title: 'Làm bài',
    steps: [
      {
        target: '[data-tour="quiz-header"]',
        title: 'Thanh điều khiển',
        description: 'Xem tên đề, thời gian còn lại và nút Submit khi hoàn thành.',
        side: 'bottom',
      },
      {
        target: '[data-tour="quiz-toolbar"]',
        title: 'Công cụ luyện tập',
        description: 'Thanh công cụ bên trái — chỉ có ở chế độ Luyện tập (Practice). Dùng T, N, S hoặc phím tắt tương ứng.',
        side: 'right',
      },
      {
        target: '[data-tour="quiz-tool-highlight"]',
        title: 'T — Tô màu (Highlight)',
        description: 'Bật công cụ tô màu, chọn màu rồi bôi đen đoạn quan trọng trong bài đọc hoặc câu hỏi. Nhấn T hoặc bấm lại để tắt.',
        side: 'right',
      },
      {
        target: '[data-tour="quiz-tool-note"]',
        title: 'N — Ghi chú',
        description: 'Mở panel ghi chú bên phải để viết ý tưởng, từ vựng hoặc nhắc nhở khi làm bài. Nhấn N để bật/tắt.',
        side: 'right',
      },
      {
        target: '[data-tour="quiz-tool-vocab"]',
        title: 'S — Tra từ',
        description: 'Bôi chọn từ/cụm từ trong bài để xem nghĩa, IPA và lưu vào sổ từ vựng. Nhấn S để bật/tắt.',
        side: 'right',
      },
      {
        target: '[data-tour="quiz-content"]',
        title: 'Nội dung bài',
        description: 'Đọc passage / nghe audio và trả lời câu hỏi. Chuyển câu bằng sidebar bên phải.',
        side: 'top',
      },
    ],
  },
  'mock-test': {
    title: 'Chọn chế độ',
    steps: [
      {
        target: '[data-tour="page-header"]',
        title: 'Mock test',
        description: 'Chọn bài và chế độ trước khi bắt đầu làm.',
        side: 'bottom',
      },
      {
        target: '[data-tour="test-grid"]',
        title: 'Danh sách Part',
        description: 'Chọn Full test hoặc từng Part, rồi Luyện tập hoặc Thi thật.',
        side: 'top',
      },
    ],
  },
}
