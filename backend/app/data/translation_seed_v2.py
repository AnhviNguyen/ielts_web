"""
Additional Translation Practice content — IELTS Band 5.0 → 7.5.
Merged into DB via TranslationService.sync_seed_content() (idempotent).
"""
from __future__ import annotations

# ── New steps (inserted after existing curriculum on sync) ─────────────────────

TRANSLATION_SEED_V2: list[dict] = [
    {
        "title": "Band 5.0 — Khởi động",
        "description": "Câu đơn giản nhất: chủ ngữ + động từ + bổ ngữ. Phù hợp người mới bắt đầu luyện dịch Việt → Anh.",
        "badge_label": "BAND 5.0",
        "badge_color": "gray",
        "icon_emoji": "🌱",
        "topics": [
            {
                "title": "Gia đình & Cuộc sống hàng ngày",
                "description": "Từ vựng cơ bản về gia đình, nhà cửa, thói quen hàng ngày.",
                "sentences": [
                    {"vi": "Tôi có hai anh trai và một em gái.", "en": "I have two older brothers and one younger sister.", "explain": "older/younger sister — dùng tính từ, không dùng 'big/small'."},
                    {"vi": "Bố mẹ tôi sống ở nông thôn.", "en": "My parents live in the countryside.", "explain": "'countryside' = nông thôn. 'live in' + địa điểm."},
                    {"vi": "Hàng ngày tôi thức dậy lúc 6 giờ sáng.", "en": "Every day I wake up at 6 a.m.", "explain": "'wake up' = thức dậy. 'at' + giờ cụ thể."},
                    {"vi": "Buổi tối cả nhà ăn cơm cùng nhau.", "en": "In the evening, the whole family eats dinner together.", "explain": "'the whole family' = cả nhà. 'together' = cùng nhau."},
                    {"vi": "Tôi thích uống trà nóng vào buổi sáng.", "en": "I like drinking hot tea in the morning.", "explain": "like + V-ing. 'in the morning' dùng 'the'."},
                    {"vi": "Nhà tôi gần trường học.", "en": "My house is near the school.", "explain": "'near' = gần. 'the school' vì trường cụ thể."},
                    {"vi": "Cuối tuần tôi thường dọn dẹp nhà cửa.", "en": "At weekends I usually clean the house.", "explain": "'At weekends' (BrE) hoặc 'On weekends' (AmE)."},
                    {"vi": "Em trai tôi đang học lớp 10.", "en": "My younger brother is in grade 10.", "explain": "'in grade 10' = học lớp 10 (AmE). BrE: 'in Year 10'."},
                ],
            },
            {
                "title": "Trường học & Bạn bè",
                "description": "Câu cơ bản về học tập và mối quan hệ bạn bè.",
                "sentences": [
                    {"vi": "Tôi đi học bằng xe đạp.", "en": "I go to school by bicycle.", "explain": "'by bicycle' = bằng xe đạp (không dùng 'with')."},
                    {"vi": "Môn học yêu thích của tôi là tiếng Anh.", "en": "My favourite subject is English.", "explain": "BrE: favourite. AmE: favorite."},
                    {"vi": "Thầy giáo giải bài rất dễ hiểu.", "en": "The teacher explains the lesson very clearly.", "explain": "'clearly' = trạng từ. 'explain' không có giới từ 'for'."},
                    {"vi": "Chúng tôi làm bài tập về nhà sau giờ học.", "en": "We do homework after school.", "explain": "'do homework' (không có 's'). 'after school' không cần 'the'."},
                    {"vi": "Bạn thân nhất của tôi rất hài hước.", "en": "My best friend is very funny.", "explain": "'best friend' = bạn thân nhất. 'funny' = hài hước."},
                    {"vi": "Kỳ thi sẽ diễn ra vào tháng tới.", "en": "The exam will take place next month.", "explain": "'take place' = diễn ra. 'next month' không cần 'in'."},
                    {"vi": "Thư viện trường mở cửa từ 7 giờ sáng.", "en": "The school library opens at 7 a.m.", "explain": "'opens' = mở cửa. 'at' + giờ."},
                    {"vi": "Học sinh cần mang theo sách và vở.", "en": "Students need to bring books and notebooks.", "explain": "'need to + V'. 'bring' = mang theo."},
                ],
            },
            {
                "title": "Thành phố & Giao thông",
                "description": "Mô tả nơi chốn và phương tiện di chuyển — chủ đề IELTS Speaking Part 1.",
                "sentences": [
                    {"vi": "Thành phố này rất đông đúc vào giờ cao điểm.", "en": "This city is very crowded during rush hour.", "explain": "'rush hour' = giờ cao điểm. 'during' = trong lúc."},
                    {"vi": "Có nhiều xe buýt chạy qua trung tâm thành phố.", "en": "Many buses run through the city centre.", "explain": "'run through' = chạy qua. BrE: centre."},
                    {"vi": "Tôi mất khoảng 30 phút để đi làm.", "en": "It takes me about 30 minutes to get to work.", "explain": "It takes + time + to V = mất bao lâu để..."},
                    {"vi": "Gần nhà tôi có một công viên nhỏ.", "en": "There is a small park near my house.", "explain": "There is/are = có (tồn tại). 'near' = gần."},
                    {"vi": "Đường phố hôm nay rất trơn vì mưa.", "en": "The streets are very slippery today because of the rain.", "explain": "'slippery' = trơn. 'because of' + danh từ."},
                    {"vi": "Nhiều người đi bộ để tập thể dục buổi sáng.", "en": "Many people walk to exercise in the morning.", "explain": "'walk' = đi bộ. 'exercise' = tập thể dục."},
                    {"vi": "Bãi đậu xe luôn đầy vào cuối tuần.", "en": "The car park is always full at weekends.", "explain": "'car park' (BrE) = bãi đậu xe. AmE: parking lot."},
                    {"vi": "Khách du lịch thích thăm khu phố cổ.", "en": "Tourists like visiting the old quarter.", "explain": "'tourists' = khách du lịch. 'old quarter' = phố cổ."},
                ],
            },
            {
                "title": "Thời tiết & Sở thích",
                "description": "Câu mô tả thời tiết và hoạt động giải trí đơn giản.",
                "sentences": [
                    {"vi": "Hôm nay trời nắng và ấm.", "en": "It is sunny and warm today.", "explain": "Thời tiết dùng 'It is'. 'sunny' = nắng."},
                    {"vi": "Mùa hè ở Việt Nam rất nóng và ẩm.", "en": "Summer in Vietnam is very hot and humid.", "explain": "'humid' = ẩm ướt/nóng ẩm."},
                    {"vi": "Tôi thích nghe nhạc khi làm bài tập.", "en": "I like listening to music while doing homework.", "explain": "'listen to' + music. 'while + V-ing'."},
                    {"vi": "Cuối tuần chúng tôi thường xem phim.", "en": "At weekends we usually watch films.", "explain": "'watch films' (BrE) hoặc 'watch movies' (AmE)."},
                    {"vi": "Anh ấy chơi bóng đá vào chiều thứ bảy.", "en": "He plays football on Saturday afternoons.", "explain": "'on Saturday afternoons' = vào các chiều thứ bảy."},
                    {"vi": "Trời mưa to nên tôi ở nhà.", "en": "It is raining heavily so I stay at home.", "explain": "'heavily' = to (mưa). 'so' = nên/vì vậy."},
                    {"vi": "Mùa thu là mùa đẹp nhất trong năm.", "en": "Autumn is the most beautiful season of the year.", "explain": "'the most beautiful' = so sánh nhất."},
                    {"vi": "Cô ấy thích đọc sách trước khi ngủ.", "en": "She likes reading books before going to sleep.", "explain": "'before + V-ing'. 'go to sleep' = đi ngủ."},
                ],
            },
        ],
    },
    {
        "title": "Band 5.5 — Liên từ & Câu ghép",
        "description": "Luyện dùng and, but, because, although, so — nền tảng cho câu phức IELTS.",
        "badge_label": "BAND 5.5",
        "badge_color": "teal",
        "icon_emoji": "🔗",
        "topics": [
            {
                "title": "Liên từ cơ bản (and, but, because, so)",
                "description": "Nối hai mệnh đề đơn giản bằng liên từ phổ biến.",
                "sentences": [
                    {"vi": "Tôi muốn đi du lịch nhưng chưa có đủ tiền.", "en": "I want to travel but I do not have enough money yet.", "explain": "'but' = nhưng. 'enough money' = đủ tiền."},
                    {"vi": "Cô ấy học chăm chỉ nên đạt điểm cao.", "en": "She studies hard so she gets high scores.", "explain": "'so' = nên/vì vậy (kết quả). 'hard' = chăm chỉ."},
                    {"vi": "Tôi đi bộ đến trường vì nhà khá gần.", "en": "I walk to school because my house is quite near.", "explain": "'because' = vì. 'quite' = khá."},
                    {"vi": "Anh ấy vừa giỏi tiếng Anh vừa giỏi toán.", "en": "He is good at both English and Maths.", "explain": "'both ... and ...' = vừa... vừa..."},
                    {"vi": "Trời mưa nên buổi picnic bị hủy.", "en": "It was raining so the picnic was cancelled.", "explain": "'was cancelled' = bị hủy (bị động)."},
                    {"vi": "Tôi thích cà phê nhưng không uống vào buổi tối.", "en": "I like coffee but I do not drink it in the evening.", "explain": "'it' thay thế 'coffee'."},
                    {"vi": "Họ mua một chiếc xe mới vì gia đình đông người.", "en": "They bought a new car because they have a large family.", "explain": "'bought' = quá khứ của buy. 'large family' = gia đình đông."},
                    {"vi": "Cô ấy mệt nên đi ngủ sớm.", "en": "She was tired so she went to bed early.", "explain": "'went to bed' = đi ngủ. 'early' = sớm."},
                ],
            },
            {
                "title": "Although / However / Therefore",
                "description": "Liên từ trình bày quan điểm — thường gặp trong IELTS Writing Task 2.",
                "sentences": [
                    {"vi": "Mặc dù trời lạnh, nhiều người vẫn đi tập thể dục.", "en": "Although it was cold, many people still exercised.", "explain": "Although + mệnh đề, + mệnh đề chính."},
                    {"vi": "Giá thuê nhà cao; tuy nhiên, nhu cầu vẫn tăng.", "en": "Rental prices are high; however, demand is still rising.", "explain": "'however' sau dấu chấm phẩy. 'demand' = nhu cầu."},
                    {"vi": "Ô nhiễm ngày càng nghiêm trọng, do đó cần hành động ngay.", "en": "Pollution is becoming more serious; therefore, immediate action is needed.", "explain": "'therefore' = do đó (formal). 'immediate action' = hành động ngay."},
                    {"vi": "Dù công nghệ phát triển, nhiều người vẫn thiếu kỹ năng số.", "en": "Although technology is advancing, many people still lack digital skills.", "explain": "'advancing' = phát triển. 'lack' = thiếu."},
                    {"vi": "Học tiếng Anh khó; tuy nhiên, kiên trì sẽ mang lại kết quả.", "en": "Learning English is difficult; however, persistence will bring results.", "explain": "'persistence' = sự kiên trì. 'bring results' = mang lại kết quả."},
                    {"vi": "Mặc dù giá cao, sản phẩm này vẫn bán chạy.", "en": "Although the price is high, this product still sells well.", "explain": "'sells well' = bán chạy."},
                    {"vi": "Nhiều người trẻ muốn làm việc từ xa; do đó, nhu cầu về không gian làm việc linh hoạt tăng.", "en": "Many young people want to work remotely; therefore, demand for flexible workspaces is increasing.", "explain": "'flexible workspaces' = không gian làm việc linh hoạt."},
                    {"vi": "Dù có nhiều thách thức, giáo dục trực tuyến vẫn phát triển mạnh.", "en": "Despite many challenges, online education continues to grow strongly.", "explain": "'Despite + N/V-ing' = mặc dù (không dùng 'Although + noun')."},
                ],
            },
            {
                "title": "Modal verbs (can, should, must, might)",
                "description": "Động từ khiếm khuyết — diễn tả khả năng, l lời khuyên, bắt buộc.",
                "sentences": [
                    {"vi": "Trẻ em nên ngủ ít nhất 8 tiếng mỗi đêm.", "en": "Children should sleep at least eight hours every night.", "explain": "'should' = nên. 'at least' = ít nhất."},
                    {"vi": "Mọi người phải tuân thủ luật giao thông.", "en": "Everyone must obey traffic laws.", "explain": "'must' = phải (bắt buộc). 'obey' = tuân thủ."},
                    {"vi": "Tôi có thể nói tiếng Anh cơ bản.", "en": "I can speak basic English.", "explain": "'can' = có thể. 'basic' = cơ bản."},
                    {"vi": "Ngày mai có thể mưa.", "en": "It might rain tomorrow.", "explain": "'might' = có thể (không chắc)."},
                    {"vi": "Bạn không nên ăn quá nhiều đồ ngọt.", "en": "You should not eat too much sugary food.", "explain": "'sugary food' = đồ ngọt."},
                    {"vi": "Sinh viên phải nộp bài đúng hạn.", "en": "Students must submit assignments on time.", "explain": "'submit' = nộp. 'on time' = đúng hạn."},
                    {"vi": "Internet giúp chúng ta có thể học mọi lúc mọi nơi.", "en": "The internet helps us learn anytime and anywhere.", "explain": "'anytime and anywhere' = mọi lúc mọi nơi."},
                    {"vi": "Chính phủ nên đầu tư nhiều hơn vào y tế công cộng.", "en": "The government should invest more in public healthcare.", "explain": "'public healthcare' = y tế công cộng."},
                ],
            },
        ],
    },
    {
        "title": "Band 6.0 — Câu phức & Mệnh đề",
        "description": "Luyện câu ghép, mệnh đề quan hệ và cấu trúc nâng cao hơn — mục tiêu Band 6.0 Writing.",
        "badge_label": "BAND 6.0",
        "badge_color": "blue",
        "icon_emoji": "📈",
        "topics": [
            {
                "title": "Mệnh đề danh từ (Noun clauses)",
                "description": "That-clause, whether, what — cấu trúc thường gặp trong bài luận.",
                "sentences": [
                    {"vi": "Điều quan trọng là chúng ta phải bảo vệ môi trường.", "en": "What matters is that we must protect the environment.", "explain": "'What matters is that...' = Điều quan trọng là..."},
                    {"vi": "Nhiều người tin rằng giáo dục thay đổi cuộc đời.", "en": "Many people believe that education changes lives.", "explain": "'believe that' + mệnh đề. 'changes lives' = thay đổi cuộc đời."},
                    {"vi": "Không rõ liệu chính sách mới có hiệu quả hay không.", "en": "It is unclear whether the new policy will be effective.", "explain": "'whether... or not' = liệu có... hay không."},
                    {"vi": "Vấn đề là nhiều sinh viên thiếu kỹ năng thực hành.", "en": "The problem is that many students lack practical skills.", "explain": "'The problem is that...' = Vấn đề là..."},
                    {"vi": "Tôi nghĩ rằng đọc sách giúp mở rộng vốn từ.", "en": "I think that reading books helps expand vocabulary.", "explain": "'expand vocabulary' = mở rộng vốn từ."},
                    {"vi": "Điều đáng lo ngại là tỷ lệ thất nghiệp đang tăng.", "en": "What is worrying is that the unemployment rate is rising.", "explain": "'unemployment rate' = tỷ lệ thất nghiệp."},
                ],
            },
            {
                "title": "Câu bị động nâng cao",
                "description": "Bị động với modal, hoàn thành, và reporting verbs.",
                "sentences": [
                    {"vi": "Người ta cho rằng giáo dục là quyền cơ bản của mọi công dân.", "en": "Education is considered to be a fundamental right of every citizen.", "explain": "Reporting passive: It is considered that / S is considered to be."},
                    {"vi": "Dự án đã được hoàn thành trước thời hạn.", "en": "The project has been completed ahead of schedule.", "explain": "Present perfect passive: has been + V3."},
                    {"vi": "Luật mới sẽ được thông qua vào tháng tới.", "en": "The new law will be passed next month.", "explain": "Future passive: will be + V3."},
                    {"vi": "Rác thải nhựa cần được giảm thiểu ngay lập tức.", "en": "Plastic waste needs to be reduced immediately.", "explain": "'needs to be + V3' = cần được."},
                    {"vi": "Sinh viên được khuyến khích tham gia hoạt động ngoại khóa.", "en": "Students are encouraged to take part in extracurricular activities.", "explain": "'encouraged to' = được khuyến khích. 'extracurricular' = ngoại khóa."},
                    {"vi": "Báo cáo cho biết nhiệt độ trung bình đã tăng 1,1°C.", "en": "The report indicates that average temperatures have risen by 1.1°C.", "explain": "'risen by' = tăng (mức). 'average temperatures' = nhiệt độ TB."},
                ],
            },
            {
                "title": "Cleft sentences & Emphasis",
                "description": "It is/was... that/who — nhấn mạnh thông tin (Band 6+).",
                "sentences": [
                    {"vi": "Chính giáo dục là chìa khóa để giảm nghèo.", "en": "It is education that is the key to reducing poverty.", "explain": "Cleft: It is + focus + that + clause."},
                    {"vi": "Chỉ khi chính phủ hành động thì vấn đề mới được giải quyết.", "en": "It is only when the government acts that the problem will be solved.", "explain": "It is only when... that... = Chỉ khi... thì..."},
                    {"vi": "Điều khiến tôi lo ngại nhất là sự gia tăng bất bình đẳng.", "en": "What worries me most is the growing inequality.", "explain": "What + V + most is... = Điều... nhất là..."},
                    {"vi": "Lý do chính khiến học sinh bỏ học là áp lực kinh tế.", "en": "The main reason why students drop out is financial pressure.", "explain": "'drop out' = bỏ học. 'financial pressure' = áp lực kinh tế."},
                    {"vi": "Không phải công nghệ mà là cách sử dụng công nghệ mới quan trọng.", "en": "It is not technology but the way technology is used that matters.", "explain": "It is not A but B that... = Không phải A mà là B..."},
                    {"vi": "Người đã đặt nền móng cho thành công của công ty là người sáng lập.", "en": "It was the founder who laid the foundation for the company's success.", "explain": "It was + person + who... = Chính... là người..."},
                ],
            },
            {
                "title": "Paraphrasing cơ bản (Task 1 & 2)",
                "description": "Diễn đạt lại ý bằng từ đồng nghĩa — kỹ năng thiết yếu IELTS.",
                "sentences": [
                    {"vi": "Số lượng người dùng internet tăng mạnh.", "en": "The number of internet users rose sharply.", "explain": "'rose sharply' = tăng mạnh. Task 1 vocabulary."},
                    {"vi": "Tỷ lệ thất nghiệp giảm đáng kể trong năm qua.", "en": "The unemployment rate fell considerably over the past year.", "explain": "'fell considerably' = giảm đáng kể."},
                    {"vi": "Ngày càng nhiều người chọn mua sắm trực tuyến.", "en": "An increasing number of people choose to shop online.", "explain": "'An increasing number of' = Ngày càng nhiều."},
                    {"vi": "Chi phí y tế leo thang trong thập kỷ qua.", "en": "Healthcare costs have escalated over the past decade.", "explain": "'escalated' = leo thang (formal synonym of 'increased')."},
                    {"vi": "Giá nhà ở các thành phố lớn vượt khả năng chi trả của người trẻ.", "en": "Housing prices in major cities exceed the affordability of young people.", "explain": "'exceed affordability' = vượt khả năng chi trả."},
                    {"vi": "Lượng khách du lịch nước ngoài đạt đỉnh vào mùa hè.", "en": "The volume of foreign tourists peaked in summer.", "explain": "'peaked' = đạt đỉnh. 'volume of' = lượng."},
                ],
            },
        ],
    },
    {
        "title": "Band 7.0 — Luận điểm & Phân tích",
        "description": "Câu lập luận học thuật, hedging language và cause-effect — chuẩn IELTS Writing Task 2 Band 7.",
        "badge_label": "BAND 7.0",
        "badge_color": "indigo",
        "icon_emoji": "💡",
        "topics": [
            {
                "title": "Cause & Effect (Nguyên nhân — Hệ quả)",
                "description": "Diễn đạt quan hệ nhân quả bằng từ nối học thuật.",
                "sentences": [
                    {"vi": "Do đô thị hóa nhanh, các thành phố phải đối mặt với tắc nghẽn giao thông nghiêm trọng.", "en": "Due to rapid urbanisation, cities have to cope with severe traffic congestion.", "explain": "'Due to' + N. 'cope with' = đối mặt với. 'urbanisation' (BrE)."},
                    {"vi": "Việc sử dụng mạng xã hội quá mức dẫn đến giảm khả năng tập trung.", "en": "Excessive use of social media leads to a decline in concentration ability.", "explain": "'leads to' = dẫn đến. 'a decline in' = sự giảm."},
                    {"vi": "Thiếu đầu tư vào giáo dục góp phần duy trì vòng luẩn quẩn nghèo đói.", "en": "Insufficient investment in education contributes to perpetuating the cycle of poverty.", "explain": "'contributes to + V-ing'. 'perpetuate' = duy trì (formal)."},
                    {"vi": "Hậu quả của biến đổi khí hậu đối với nông nghiệp là rất nghiêm trọng.", "en": "The consequences of climate change for agriculture are extremely serious.", "explain": "'consequences for' = hậu quả đối với."},
                    {"vi": "Một trong những nguyên nhân chính của ô nhiễm không khí là khí thải từ xe cộ.", "en": "One of the main causes of air pollution is emissions from vehicles.", "explain": "'emissions from' = khí thải từ. 'vehicles' = phương tiện."},
                    {"vi": "Kết quả là chất lượng cuộc sống ở nhiều khu vực đã được cải thiện.", "en": "As a result, the quality of life in many areas has improved.", "explain": "'As a result' = Kết quả là (formal)."},
                ],
            },
            {
                "title": "Hedging & Academic tone",
                "description": "Ngôn ngữ thận trọng học thuật: tend to, appear to, it seems that.",
                "sentences": [
                    {"vi": "Có vẻ như công nghệ AI sẽ thay đổi đáng kể thị trường lao động.", "en": "It appears that AI technology will significantly alter the labour market.", "explain": "'It appears that' = Có vẻ như (hedging). 'alter' = thay đổi."},
                    {"vi": "Nhiều nghiên cứu cho thấy tập thể dục thường xuyên có thể cải thiện sức khỏe tinh thần.", "en": "Numerous studies suggest that regular exercise may improve mental health.", "explain": "'Numerous studies suggest' = Nhiều nghiên cứu cho thấy. 'may' = có thể."},
                    {"vi": "Các chuyên gia cho rằng tình trạng này có xu hướng trở nên phổ biến hơn.", "en": "Experts believe that this phenomenon tends to become more widespread.", "explain": "'tends to' = có xu hướng. 'widespread' = phổ biến."},
                    {"vi": "Có thể lập luận rằng giáo dục kỹ thuật số mang lại lợi ích lớn.", "en": "It could be argued that digital education brings substantial benefits.", "explain": "'It could be argued that' = Có thể lập luận rằng."},
                    {"vi": "Dường như người trẻ ngày càng phụ thuộc vào thiết bị di động.", "en": "Young people seem to be increasingly dependent on mobile devices.", "explain": "'seem to be' = dường như. 'dependent on' = phụ thuộc vào."},
                    {"vi": "Theo quan điểm của tôi, chính phủ nên đóng vai trò điều tiết thị trường.", "en": "In my view, the government should play a regulatory role in the market.", "explain": "'In my view' = Theo quan điểm của tôi. 'regulatory role' = vai trò điều tiết."},
                ],
            },
            {
                "title": "Problem — Solution (Task 2)",
                "description": "Cấu trúc nêu vấn đề và đề xuất giải pháp.",
                "sentences": [
                    {"vi": "Một giải pháp khả thi là khuyến khích sử dụng phương tiện giao thông công cộng.", "en": "A feasible solution is to encourage the use of public transport.", "explain": "'feasible solution' = giải pháp khả thi."},
                    {"vi": "Để giải quyết vấn đề thiếu hụt nguồn nước, các quốc gia cần hợp tác quốc tế.", "en": "To address water scarcity, nations need to cooperate internationally.", "explain": "'address' = giải quyết (formal). 'water scarcity' = thiếu hụt nước."},
                    {"vi": "Một cách hiệu quả để giảm rác thải nhựa là áp dụng thuế môi trường.", "en": "An effective way to reduce plastic waste is to implement environmental taxes.", "explain": "'implement' = áp dụng/thực thi. 'environmental taxes' = thuế môi trường."},
                    {"vi": "Chính phủ có thể giải quyết tình trạng thất nghiệp bằng cách hỗ trợ đào tạo nghề.", "en": "Governments can tackle unemployment by supporting vocational training.", "explain": "'tackle' = giải quyết. 'vocational training' = đào tạo nghề."},
                    {"vi": "Cần có các biện pháp khẩn cấp để bảo vệ các loài đang bị đe dọa.", "en": "Urgent measures are needed to protect endangered species.", "explain": "'Urgent measures' = biện pháp khẩn cấp. 'endangered species' = loài bị đe dọa."},
                    {"vi": "Giáo dục công dân về tái chế có thể góp phần giảm ô nhiễm môi trường.", "en": "Public education on recycling can help reduce environmental pollution.", "explain": "'Public education on' = Giáo dục công dân về."},
                ],
            },
            {
                "title": "Advantages & Disadvantages",
                "description": "Cấu trúc bài Advantage/Disadvantage — dạng bài Task 2 phổ biến.",
                "sentences": [
                    {"vi": "Một lợi thế rõ ràng của du lịch là tạo việc làm cho cộng đồng địa phương.", "en": "A clear advantage of tourism is that it creates jobs for local communities.", "explain": "'A clear advantage of' = Một lợi thế rõ ràng của."},
                    {"vi": "Tuy nhiên, du lịch quá phát triển có thể gây hại cho môi trường tự nhiên.", "en": "However, overtourism can harm the natural environment.", "explain": "'overtourism' = du lịch quá tải (neologism IELTS-relevant)."},
                    {"vi": "Làm việc từ xa giúp tiết kiệm thời gian đi lại nhưng có thể gây cô lập xã hội.", "en": "Remote work saves commuting time but may cause social isolation.", "explain": "'commuting time' = thời gian đi lại. 'social isolation' = cô lập xã hội."},
                    {"vi": "Mạng xã hội giúp kết nối toàn cầu; mặt khác, nó lan truyền thông tin sai lệch.", "en": "Social media enables global connection; on the other hand, it spreads misinformation.", "explain": "'on the other hand' = mặt khác. 'misinformation' = thông tin sai lệch."},
                    {"vi": "Ưu điểm lớn nhất của học trực tuyến là tính linh hoạt về thời gian.", "en": "The greatest benefit of online learning is flexibility in scheduling.", "explain": "'The greatest benefit of' = Ưu điểm lớn nhất của."},
                    {"vi": "Nhược điểm đáng kể nhất là thiếu tương tác trực tiếp với giáo viên.", "en": "The most significant drawback is the lack of direct interaction with teachers.", "explain": "'drawback' = nhược điểm. 'significant' = đáng kể."},
                ],
            },
        ],
    },
]

# ── Extra topics appended to existing steps (matched by step title) ───────────

TRANSLATION_EXTRA_TOPICS: dict[str, list[dict]] = {
    "Cấu trúc câu cơ bản": [
        {
            "title": "Tương lai (Future tenses)",
            "description": "Will, going to, present continuous for future — thì tương lai IELTS.",
            "sentences": [
                {"vi": "Tôi sẽ thi IELTS vào tháng tới.", "en": "I will take the IELTS exam next month.", "explain": "'will + V' = quyết định/tương lai. 'take an exam'."},
                {"vi": "Chúng tôi định mở một quán cà phê vào năm sau.", "en": "We are going to open a coffee shop next year.", "explain": "'be going to' = dự định có kế hoạch."},
                {"vi": "Máy bay cất cánh lúc 8 giờ tối nay.", "en": "The plane is taking off at 8 p.m. tonight.", "explain": "Present continuous for fixed future arrangements."},
                {"vi": "Tôi nghĩ trời sẽ mưa chiều nay.", "en": "I think it will rain this afternoon.", "explain": "'I think' + will (prediction)."},
                {"vi": "Họ sẽ không đến kịp buổi họp.", "en": "They will not arrive in time for the meeting.", "explain": "'in time for' = kịp (cho sự kiện)."},
                {"vi": "Chính phủ sẽ xây thêm nhiều bệnh viện công.", "en": "The government will build more public hospitals.", "explain": "'public hospitals' = bệnh viện công."},
            ],
        },
        {
            "title": "Quantifiers (some, many, much, few, little)",
            "description": "Lượng từ — thường gặp trong Task 1 và Speaking.",
            "sentences": [
                {"vi": "Có quá nhiều xe ô tô trong thành phố.", "en": "There are too many cars in the city.", "explain": "'too many' + countable. 'cars' = đếm được."},
                {"vi": "Không có nhiều nước sạch ở vùng này.", "en": "There is not much clean water in this area.", "explain": "'much' + uncountable (water)."},
                {"vi": "Ít sinh viên chọn ngành kỹ thuật.", "en": "Few students choose engineering majors.", "explain": "'Few' = ít (negative connotation)."},
                {"vi": "Cô ấy có ít thời gian rảnh vì bận rộn.", "en": "She has little free time because she is busy.", "explain": "'little' + uncountable. 'free time' = thời gian rảnh."},
                {"vi": "Hầu hết người dân đều ủng hộ chính sách mới.", "en": "Most citizens support the new policy.", "explain": "'Most' + plural noun. 'support' = ủng hộ."},
                {"vi": "Một số người cho rằng học phí nên miễn phí.", "en": "Some people believe that tuition fees should be free.", "explain": "'Some people believe that' = Một số người cho rằng."},
            ],
        },
    ],
    "Collocations & Từ vựng học thuật": [
        {
            "title": "Collocations: Kinh tế & Việc làm",
            "description": "Cụm từ học thuật về kinh tế — chủ đề IELTS Writing phổ biến.",
            "sentences": [
                {"vi": "Nền kinh tế đang phục hồi sau suy thoái.", "en": "The economy is recovering after the recession.", "explain": "'recover from' = phục hồi. 'recession' = suy thoái."},
                {"vi": "Tỷ lệ lạm phát tăng cao ảnh hưởng đến sức mua của người tiêu dùng.", "en": "High inflation rates affect consumers' purchasing power.", "explain": "'purchasing power' = sức mua. 'inflation rate' = tỷ lệ lạm phát."},
                {"vi": "Doanh nghiệp vừa và nhỏ đóng góp đáng kể vào GDP.", "en": "Small and medium enterprises contribute significantly to GDP.", "explain": "'SMEs' = doanh nghiệp vừa và nhỏ."},
                {"vi": "Thị trường lao động đang chuyển dịch sang nền kinh tế số.", "en": "The labour market is shifting towards a digital economy.", "explain": "'shift towards' = chuyển dịch sang. 'digital economy' = nền kinh tế số."},
                {"vi": "Đầu tư nước ngoài trực tiếp thúc đẩy tăng trưởng kinh tế.", "en": "Foreign direct investment drives economic growth.", "explain": "'FDI' = đầu tư nước ngoài trực tiếp. 'drives' = thúc đẩy."},
                {"vi": "Nhiều lao động trẻ gặp khó khăn trong việc tìm việc làm ổn định.", "en": "Many young workers struggle to find stable employment.", "explain": "'stable employment' = việc làm ổn định."},
            ],
        },
        {
            "title": "Collocations: Văn hóa & Xã hội",
            "description": "Từ vựng học thuật về văn hóa, truyền thống và xã hội.",
            "sentences": [
                {"vi": "Bảo tồn di sản văn hóa là trách nhiệm của mọi thế hệ.", "en": "Preserving cultural heritage is the responsibility of every generation.", "explain": "'cultural heritage' = di sản văn hóa. 'preserving' = bảo tồn."},
                {"vi": "Toàn cầu hóa làm phai nhạt bản sắc văn hóa địa phương.", "en": "Globalisation dilutes local cultural identity.", "explain": "'dilutes' = phai nhạt/làm loãng. 'cultural identity' = bản sắc văn hóa."},
                {"vi": "Gia đình đóng vai trò nền tảng trong hình thành giá trị xã hội.", "en": "The family plays a foundational role in shaping social values.", "explain": "'foundational role' = vai trò nền tảng. 'shaping' = hình thành."},
                {"vi": "Sự đa dạng văn hóa làm phong phú cuộc sống đô thị.", "en": "Cultural diversity enriches urban life.", "explain": "'cultural diversity' = đa dạng văn hóa. 'enriches' = làm phong phú."},
                {"vi": "Truyền thống lễ hội gắn kết cộng đồng địa phương.", "en": "Festival traditions bind local communities together.", "explain": "'bind together' = gắn kết. 'local communities' = cộng đồng địa phương."},
                {"vi": "Truyền thông đại chúng ảnh hưởng mạnh đến quan niệm xã hội.", "en": "Mass media strongly influences social perceptions.", "explain": "'mass media' = truyền thông đại chúng. 'perceptions' = quan niệm."},
            ],
        },
    ],
    "Dịch đoạn văn Band 6.5": [
        {
            "title": "Đoạn văn: Du lịch & Văn hóa",
            "description": "Chủ đề du lịch bền vững và trao đổi văn hóa — Band 6.5.",
            "sentences": [
                {"vi": "Du lịch bền vững ngày càng được ưa chuộng vì du khách quan tâm hơn đến tác động môi trường. Các khách sạn xanh và tour du lịch cộng đồng giúp giảm thiểu rác thải và hỗ trợ kinh tế địa phương.", "en": "Sustainable tourism is becoming increasingly popular as travellers become more concerned about environmental impact. Green hotels and community-based tours help reduce waste and support the local economy.", "explain": "'sustainable tourism' = du lịch bền vững. 'community-based tours' = tour cộng đồng."},
                {"vi": "Việc bảo tồn di tích lịch sử vừa thu hút du khách vừa giữ gìn bản sắc văn hóa. Tuy nhiên, lượng khách quá đông có thể gây hư hại cho các di tích cổ.", "en": "Preserving historical sites both attracts tourists and maintains cultural identity. However, excessive visitor numbers can damage ancient monuments.", "explain": "'ancient monuments' = di tích cổ. 'excessive' = quá mức."},
                {"vi": "Du lịch quốc tế tạo cơ hội giao lưu văn hóa giữa các quốc gia. Khi hiểu biết lẫn nhau tăng lên, các rào cản địa chính trị có thể được thu hẹp.", "en": "International tourism creates opportunities for cultural exchange between nations. As mutual understanding grows, geopolitical barriers may be narrowed.", "explain": "'cultural exchange' = giao lưu văn hóa. 'geopolitical barriers' = rào cản địa chính trị."},
            ],
        },
        {
            "title": "Đoạn văn: Sức khỏe & Lối sống",
            "description": "Chủ đề sức khỏe cộng đồng và thói quen sống lành mạnh.",
            "sentences": [
                {"vi": "Lối sống ít vận động và chế độ ăn nhiều đường, muối là nguyên nhân chính gây bệnh tim mạch và tiểu đường. Chính phủ cần tuyên truyền dinh dưỡng lành mạnh từ sớm.", "en": "Sedentary lifestyles and diets high in sugar and salt are major causes of cardiovascular disease and diabetes. Governments need to promote healthy nutrition from an early age.", "explain": "'sedentary lifestyle' = lối sống ít vận động. 'cardiovascular disease' = bệnh tim mạch."},
                {"vi": "Tập thể dục thường xuyên không chỉ cải thiện thể chất mà còn giảm căng thẳng và lo âu. Nhiều nghiên cứu chứng minh mối liên hệ giữa hoạt động thể chất và sức khỏe tinh thần.", "en": "Regular exercise not only improves physical health but also reduces stress and anxiety. Numerous studies demonstrate the link between physical activity and mental well-being.", "explain": "'mental well-being' = sức khỏe tinh thần. 'demonstrate the link' = chứng minh mối liên hệ."},
                {"vi": "Hệ thống y tế công cần được tăng cường để đảm bảo mọi người dân đều tiếp cận được dịch vụ chăm sóc sức khỏe cơ bản, bất kể thu nhập.", "en": "Public healthcare systems need to be strengthened to ensure all citizens have access to basic medical services regardless of income.", "explain": "'regardless of income' = bất kể thu nhập. 'strengthened' = được tăng cường."},
            ],
        },
    ],
    "Dịch đoạn văn Band 8.0": [
        {
            "title": "Phân tích: Toàn cầu hóa & Văn hóa",
            "description": "Đoạn văn học thuật Band 8 về toàn cầu hóa.",
            "sentences": [
                {"vi": "Toàn cầu hóa văn hóa, được thúc đẩy bởi truyền thông và thương mại quốc tế, đã tạo ra một nền văn hóa chung toàn cầu. Tuy nhiên, các nhà phê bình cho rằng quá trình này đồng thời làm suy yếu sự đa dạng văn hóa và dẫn đến sự đồng nhất hóa đáng lo ngại.", "en": "Cultural globalisation, driven by media and international trade, has created a shared global culture. However, critics argue that this process simultaneously erodes cultural diversity and leads to worrying homogenisation.", "explain": "'homogenisation' = sự đồng nhất hóa (C2). 'simultaneously' = đồng thời."},
                {"vi": "Sự lan tỏa của chuỗi nhà hàng thức fast food phương Tây là minh chứng cho việc thói quen ăn uống địa phương bị thay thế bởi mô hình tiêu dùng toàn cầu. Điều này gây lo ngại về sức khỏe cộng đồng và sự bền vững của nền nông nghiệp địa phương.", "en": "The spread of Western fast-food chains exemplifies how local eating habits are being replaced by global consumption patterns. This raises concerns about public health and the sustainability of local agriculture.", "explain": "'exemplifies' = là minh chứng. 'consumption patterns' = mô hình tiêu dùng."},
            ],
        },
    ],
    "Dịch Essay hoàn chỉnh": [
        {
            "title": "Essay Task 2: Công nghệ & Xã hội",
            "description": "Bài luận IELTS Task 2 về tác động công nghệ — Band 7.5+.",
            "sentences": [
                {"vi": "Trong thời đại số, câu hỏi liệu lợi ích của công nghệ có vượt trội hơn những rủi ro hay không đã trở thành chủ đề tranh luận then chốt. Quan điểm của tôi là mặc dù công nghệ mang lại tiến bộ vượt bậc, việc quản lý không đúng cách có thể gây hậu quả nghiêm trọng cho xã hội.", "en": "In the digital age, the question of whether the benefits of technology outweigh its risks has become a pivotal debate. My view is that while technology delivers remarkable progress, mismanagement can have serious consequences for society.", "explain": "'outweigh its risks' = vượt trội hơn rủi ro. 'pivotal debate' = tranh luận then chốt."},
                {"vi": "Những người ủng hộ công nghệ nhấn mạnh rằng nó đã cách mạng hóa giáo dục, y tế và giao tiếp. Họ lập luận rằng nhờ internet, tri thức nhân loại trở nên dễ tiếp cận hơn bao giờ hết, tạo cơ hội bình đẳng cho hàng triệu người ở vùng sâu vùng xa.", "en": "Technology proponents emphasise that it has revolutionised education, healthcare, and communication. They argue that through the internet, human knowledge has become more accessible than ever, creating equal opportunities for millions in remote areas.", "explain": "'proponents' = người ủng hộ. 'revolutionised' = cách mạng hóa."},
                {"vi": "Tuy nhiên, những rủi ro tiềm ẩn không thể bị bỏ qua. Sự phụ thuộc quá mức vào thiết bị số có thể làm suy giảm kỹ năng giao tiếp trực tiếp, trong khi thuật toán mạng xã hội tạo ra bong bóng thông tin và chia rẽ xã hội.", "en": "However, potential risks cannot be overlooked. Excessive dependence on digital devices may erode face-to-face communication skills, while social media algorithms create information bubbles and social division.", "explain": "'information bubbles' = bong bóng thông tin. 'social division' = chia rẽ xã hội."},
                {"vi": "Tóm lại, công nghệ vừa là công cụ vừa là thách thức. Điều then chốt là xây dựng khung pháp lý và giáo dục kỹ năng số để con người tận dụng lợi ích mà không bị chi phối bởi những tác hại tiềm ẩn.", "en": "In conclusion, technology is both a tool and a challenge. The key is to build regulatory frameworks and digital literacy education so that people can harness its benefits without being dominated by its potential harms.", "explain": "'harness its benefits' = tận dụng lợi ích. 'digital literacy' = kỹ năng số."},
            ],
        },
    ],
}
