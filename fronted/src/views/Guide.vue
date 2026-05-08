<template>
  <div class="mx-auto max-w-[800px]">
    <div class="mb-6 flex items-center gap-5 rounded-[var(--r)] bg-[var(--ink)] px-8 py-7 text-white">
      <div class="shrink-0 text-5xl">📚</div>
      <div>
        <h1 class="font-display mb-1.5 text-2xl font-bold">Hướng dẫn sử dụng LinguaIELTS</h1>
        <p class="text-sm leading-6 text-white/65">Tìm hiểu cách sử dụng từng tính năng để tối ưu hành trình luyện thi IELTS của bạn.</p>
      </div>
    </div>

    <div class="mb-6 flex flex-wrap gap-2">
      <a v-for="s in sections" :key="s.id" :href="'#' + s.id" class="flex items-center gap-1.5 rounded-full border border-[var(--border2)] bg-[var(--surface)] px-3.5 py-1.5 text-xs font-medium text-[var(--ink2)] transition-colors hover:border-[var(--green-l)] hover:bg-[var(--green-bg)] hover:text-[var(--green)]">
        <span>{{ s.icon }}</span> {{ s.title }}
      </a>
    </div>

    <div class="flex flex-col gap-3">
      <div
        v-for="section in sections"
        :key="section.id"
        :id="section.id"
        class="overflow-hidden rounded-[var(--r)] border border-[var(--border)] bg-[var(--surface)]"
      >
        <div
          class="flex cursor-pointer items-center justify-between px-5.5 py-4.5 transition-colors hover:bg-[var(--bg)]"
          @click="toggleSection(section.id)"
        >
          <div class="flex items-center gap-2.5">
            <span class="text-xl">{{ section.icon }}</span>
            <h2 class="font-display m-0 text-base font-semibold text-[var(--ink)]">{{ section.title }}</h2>
            <span class="rounded-full bg-[var(--green-bg)] px-2 py-0.5 text-[10px] font-bold text-[var(--green)]" v-if="section.badge">{{ section.badge }}</span>
          </div>
          <span class="text-[var(--ink3)] transition-transform" :class="{ 'rotate-180': openSections[section.id] }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
          </span>
        </div>

        <Transition name="accordion">
          <div v-if="openSections[section.id]" class="border-t border-[var(--border)] px-5.5 pb-5.5">
            <div v-if="section.steps" class="mt-4.5 flex flex-col gap-3.5">
              <div v-for="(step, i) in section.steps" :key="i" class="flex items-start gap-3.5">
                <div class="font-display flex h-7.5 w-7.5 shrink-0 items-center justify-center rounded-full bg-[var(--ink)] text-sm font-bold text-white">{{ i + 1 }}</div>
                <div>
                  <div class="mb-0.5 text-sm font-semibold text-[var(--ink)]">{{ step.title }}</div>
                  <div class="text-[13px] leading-6 text-[var(--ink3)]">{{ step.desc }}</div>
                </div>
              </div>
            </div>

            <div v-if="section.tips" class="mt-4.5 grid grid-cols-1 gap-3 md:grid-cols-3">
              <div v-for="tip in section.tips" :key="tip.title" class="rounded-[var(--r-sm)] border border-[var(--border)] bg-[var(--bg2)] p-4">
                <div class="mb-2 text-2xl">{{ tip.icon }}</div>
                <div class="mb-1 text-[13px] font-semibold text-[var(--ink)]">{{ tip.title }}</div>
                <div class="text-xs leading-5 text-[var(--ink3)]">{{ tip.desc }}</div>
              </div>
            </div>

            <div v-if="section.table" class="mt-4.5 overflow-x-auto">
              <table class="w-full border-collapse text-[13px]">
                <thead>
                  <tr>
                    <th v-for="col in section.table.cols" :key="col" class="border-b-2 border-[var(--border)] bg-[var(--bg2)] px-3.5 py-2.5 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--ink3)]">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in section.table.rows" :key="row[0]">
                    <td v-for="(cell, ci) in row" :key="ci" class="border-b border-[var(--border)] px-3.5 py-2.5 text-[var(--ink2)]">{{ cell }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="section.note" class="mt-4 flex items-start gap-2 rounded-[var(--r-sm)] border border-[rgba(144,96,10,0.2)] bg-[var(--gold-bg)] px-4 py-3 text-[13px] text-[var(--gold)]">
              <span class="shrink-0">💡</span>
              {{ section.note }}
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <div class="mt-8 rounded-[var(--r)] bg-linear-to-br from-[var(--green)] to-[var(--blue)] px-5 py-10 text-center text-white">
      <div class="font-display mb-2 text-2xl font-bold">Sẵn sàng bắt đầu?</div>
      <div class="mb-5 text-sm text-white/80">Hãy bắt đầu luyện tập ngay hôm nay và chinh phục band điểm mục tiêu của bạn!</div>
      <router-link to="/dashboard" class="inline-block rounded-[var(--r-sm)] bg-white px-7 py-2.5 text-sm font-bold text-[var(--green)] transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.2)]">Về Dashboard →</router-link>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const openSections = reactive({
  start: true,
  dashboard: false,
  reading: false,
  listening: false,
  writing: false,
  speaking: false,
  vocabulary: false,
  tips: false,
})

function toggleSection(id) {
  openSections[id] = !openSections[id]
}

const sections = [
  {
    id: 'start',
    icon: '🚀',
    title: 'Bắt đầu với LinguaIELTS',
    steps: [
      { title: 'Đăng ký tài khoản', desc: 'Tạo tài khoản miễn phí với email của bạn. Tất cả dữ liệu học tập sẽ được lưu tự động.' },
      { title: 'Thiết lập mục tiêu', desc: 'Vào Profile → Chỉnh sửa band score mục tiêu và ngày thi dự kiến để kích hoạt đồng hồ đếm ngược.' },
      { title: 'Làm bài kiểm tra đầu vào', desc: 'Hoàn thành bài test thử để hệ thống gợi ý lộ trình học phù hợp với trình độ hiện tại.' },
      { title: 'Luyện tập hàng ngày', desc: 'Duy trì streak bằng cách luyện ít nhất 1 bài mỗi ngày. Streak càng dài, XP thưởng càng nhiều!' },
    ],
  },
  {
    id: 'dashboard',
    icon: '📊',
    title: 'Dashboard — Tổng quan học tập',
    steps: [
      { title: 'Band Score Grid', desc: '5 ô điểm hiển thị band score hiện tại và mục tiêu cho từng kỹ năng. Click vào ô để chỉnh sửa mục tiêu.' },
      { title: 'Biểu đồ chăm chỉ', desc: 'Calendar heatmap hiển thị ngày bạn đã luyện tập. Màu xanh đậm hơn = luyện nhiều bài hơn.' },
      { title: 'Đếm ngược lịch thi', desc: 'Số ngày còn lại đến kỳ thi IELTS. Cập nhật ngày thi trong phần Profile.' },
      { title: 'Thống kê tuần', desc: 'Bảng tổng hợp số bài đã làm và thời gian luyện tập từng kỹ năng trong tuần.' },
    ],
    note: 'Mẹo: Nhấp vào các skill card ở dưới Dashboard để chuyển nhanh đến trang luyện tập tương ứng.',
  },
  {
    id: 'reading',
    icon: '📖',
    title: 'Luyện Reading',
    steps: [
      { title: 'Chọn bài đọc', desc: 'Lọc theo Part (1/2/3), độ khó (Dễ/Trung bình/Khó) hoặc tìm kiếm theo tên bài.' },
      { title: 'Chọn chế độ', desc: 'Luyện tập (không giới hạn thời gian) hoặc Thi thật (20 phút, như điều kiện thực tế).' },
      { title: 'Đọc passage & làm câu hỏi', desc: 'Sử dụng thanh công cụ highlight để đánh dấu thông tin quan trọng trong bài đọc.' },
      { title: 'Xem kết quả', desc: 'Sau khi nộp bài, xem band score ước tính, câu trả lời đúng/sai và giải thích chi tiết.' },
    ],
    tips: [
      { icon: '⏱️', title: 'Quản lý thời gian', desc: 'Dành ~17 phút mỗi passage. Đừng dừng quá lâu ở một câu hỏi.' },
      { icon: '🔍', title: 'Kỹ thuật skimming', desc: 'Đọc lướt tiêu đề, từ khóa và câu đầu tiên của mỗi đoạn trước khi đọc kỹ.' },
      { icon: '📝', title: 'Highlight từ khóa', desc: 'Dùng tính năng highlight để đánh dấu thông tin quan trọng trong câu trả lời.' },
    ],
  },
  {
    id: 'listening',
    icon: '🎧',
    title: 'Luyện Listening',
    steps: [
      { title: 'Chọn Section', desc: 'IELTS Listening có 4 Section. Bắt đầu từ Section 1 (dễ nhất) và tăng dần độ khó.' },
      { title: 'Nghe và điền câu trả lời', desc: 'File audio chỉ phát 1 lần như thi thật. Sử dụng nút tua nhỏ (+/-5s) để ôn lại.' },
      { title: 'Điều chỉnh tốc độ', desc: 'Bắt đầu với 0.75x nếu cần, sau đó tăng dần lên 1x và 1.25x khi đã quen.' },
      { title: 'Nộp và xem kết quả', desc: 'Sau khi nộp bài, xem đáp án và transcript để học từ lỗi sai.' },
    ],
    note: 'Luyện nghe tiếng Anh mọi lúc mọi nơi — podcast, BBC, CNN giúp cải thiện khả năng nghe hiểu tự nhiên.',
  },
  {
    id: 'writing',
    icon: '✍️',
    title: 'Luyện Writing',
    steps: [
      { title: 'Task 1 — Biểu đồ', desc: 'Phân tích biểu đồ/sơ đồ được cung cấp. Tối thiểu 150 từ, thời gian đề xuất 20 phút.' },
      { title: 'Task 2 — Essay', desc: 'Viết essay theo đề bài. Tối thiểu 250 từ, thời gian đề xuất 40 phút.' },
      { title: 'AI Feedback', desc: 'Nộp bài để nhận band score ước tính (TA, CC, LR, GRA) và gợi ý cải thiện từ AI.' },
      { title: 'Học từ câu mẫu', desc: 'Xem câu được cải thiện để học cách diễn đạt tốt hơn và đa dạng từ vựng hơn.' },
    ],
    table: {
      cols: ['Tiêu chí', 'Ký hiệu', 'Trọng số'],
      rows: [
        ['Task Achievement / Response', 'TA/TR', '25%'],
        ['Coherence & Cohesion', 'CC', '25%'],
        ['Lexical Resource', 'LR', '25%'],
        ['Grammatical Range & Accuracy', 'GRA', '25%'],
      ],
    },
  },
  {
    id: 'speaking',
    icon: '🎤',
    title: 'Luyện Speaking',
    steps: [
      { title: 'Hiểu cấu trúc 3 Part', desc: 'Part 1: Q&A đơn giản (4-5 phút). Part 2: Monologue theo cue card (3-4 phút). Part 3: Thảo luận sâu (4-5 phút).' },
      { title: 'Xem câu hỏi', desc: 'Đọc kỹ câu hỏi và ghi chú ý tưởng trước khi ghi âm (đặc biệt Part 2 có 1 phút prep).' },
      { title: 'Ghi âm câu trả lời', desc: 'Nhấn nút mic để bắt đầu ghi âm. Cố gắng nói liên tục, tránh dừng quá lâu giữa câu.' },
      { title: 'Nhận phân tích AI', desc: 'Xem phân tích phát âm (màu xanh=tốt, vàng=khá, đỏ=cần cải thiện) và band score ước tính.' },
    ],
    tips: [
      { icon: '🗣️', title: 'Nói nhiều hơn', desc: 'Thực hành nói tiếng Anh mỗi ngày, dù chỉ 5-10 phút.' },
      { icon: '📱', title: 'Tự ghi âm', desc: 'Nghe lại recording để phát hiện lỗi phát âm và cải thiện.' },
      { icon: '🌍', title: 'Mở rộng vốn từ', desc: 'Học idioms và collocations để câu trả lời tự nhiên hơn.' },
    ],
  },
  {
    id: 'vocabulary',
    icon: '📚',
    title: 'Học Từ vựng với FSRS',
    steps: [
      { title: 'Flashcard mode', desc: 'Xem từ ở mặt trước (word + IPA), bấm để lật xem nghĩa và ví dụ ở mặt sau.' },
      { title: 'Đánh giá độ nhớ', desc: 'Sau khi lật card, chọn mức độ nhớ: Quên rồi / Khó / Ổn / Dễ.' },
      { title: 'Thuật toán FSRS', desc: 'Hệ thống tự động lên lịch ôn tập dựa trên đánh giá: từ dễ ôn ít, từ khó ôn nhiều hơn.' },
      { title: 'Word detail', desc: 'Sau khi lật card, xem thêm từ liên quan và ví dụ trong context IELTS thực tế.' },
    ],
    table: {
      cols: ['Mức đánh giá', 'Ý nghĩa', 'Lịch ôn tiếp'],
      rows: [
        ['😰 Quên rồi', 'Không nhớ gì', '1 ngày'],
        ['😓 Khó', 'Nhớ mờ mờ', '3 ngày'],
        ['😊 Ổn', 'Nhớ khá tốt', '7 ngày'],
        ['🎉 Dễ', 'Nhớ rất chắc', '14 ngày'],
      ],
    },
  },
  {
    id: 'tips',
    icon: '💡',
    title: 'Mẹo học hiệu quả',
    tips: [
      { icon: '📅', title: 'Học đều đặn', desc: 'Luyện 30-60 phút mỗi ngày hiệu quả hơn học nhồi nhiều giờ cuối tuần.' },
      { icon: '🎯', title: 'Tập trung điểm yếu', desc: 'Dựa vào band score mỗi kỹ năng, dành thêm 60% thời gian cho kỹ năng thấp điểm nhất.' },
      { icon: '🔥', title: 'Duy trì streak', desc: 'Streak là động lực học mỗi ngày. Đừng để đứt chuỗi — ngay cả 1 bài nhỏ cũng tính!' },
      { icon: '📖', title: 'Đọc tiếng Anh mỗi ngày', desc: 'BBC, The Guardian, National Geographic — đọc 1 bài/ngày để quen văn phong Academic.' },
      { icon: '🎧', title: 'Podcast tiếng Anh', desc: 'TED Talks, BBC Global News — nghe trong lúc đi lại để tận dụng thời gian rảnh.' },
      { icon: '✍️', title: 'Viết nhật ký', desc: 'Viết 100-150 từ về ngày hôm nay bằng tiếng Anh để duy trì kỹ năng writing.' },
    ],
  },
]
</script>
