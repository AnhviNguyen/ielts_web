"""
Translation Practice seed data.
Progressive curriculum: Band 5.0 → Band 8.0+
"""
from __future__ import annotations

TRANSLATION_SEED: list[dict] = [
    # ────────────────────────────────────────────────────────────────────────
    # BƯỚC 1 – Cấu trúc câu cơ bản
    # ────────────────────────────────────────────────────────────────────────
    {
        "title": "Cấu trúc câu cơ bản",
        "description": "Luyện dịch các câu đơn từ Việt sang Anh. Tập trung vào việc sử dụng đúng thì, mạo từ và cấu trúc câu S-V-O cơ bản.",
        "badge_label": None,
        "badge_color": "gray",
        "icon_emoji": "✏️",
        "topics": [
            {
                "title": "Hiện tại đơn (Simple Present)",
                "description": "Diễn tả thói quen, sự thật hiển nhiên, lịch trình cố định.",
                "sentences": [
                    {"vi": "Tôi học tiếng Anh mỗi ngày.", "en": "I study English every day.", "explain": "Dùng Simple Present với 'every day'. Với 'I' không thêm -s/-es vào động từ."},
                    {"vi": "Cô ấy dạy toán ở trường tiểu học.", "en": "She teaches Mathematics at a primary school.", "explain": "'She' → thêm -es vào 'teach'. 'Mathematics' viết hoa."},
                    {"vi": "Họ không thích ăn đồ ăn cay.", "en": "They do not like eating spicy food.", "explain": "Phủ định dùng 'do not' với they/we/I/you."},
                    {"vi": "Anh ấy thường đi làm bằng xe buýt.", "en": "He usually goes to work by bus.", "explain": "'He' → goes (thêm -es). 'usually' đặt trước động từ chính."},
                    {"vi": "Chúng tôi sống ở Hà Nội.", "en": "We live in Hanoi.", "explain": "Dùng 'in' cho thành phố, không dùng 'at'."},
                    {"vi": "Con mèo ngủ trên ghế sofa mỗi buổi chiều.", "en": "The cat sleeps on the sofa every afternoon.", "explain": "Dùng 'the' cho danh từ cụ thể đã biết. 'on' cho bề mặt."},
                    {"vi": "Em gái tôi chơi đàn piano rất hay.", "en": "My younger sister plays the piano very well.", "explain": "Nhạc cụ dùng với mạo từ 'the'. 'very well' là trạng từ."},
                    {"vi": "Nhà máy này sản xuất hàng nghìn sản phẩm mỗi năm.", "en": "This factory produces thousands of products every year.", "explain": "'thousands of' = hàng nghìn. 'products' số nhiều."},
                    {"vi": "Anh ấy không bao giờ uống cà phê vào buổi tối.", "en": "He never drinks coffee in the evening.", "explain": "'never' đặt trước động từ chính. 'in the evening' dùng 'the'."},
                    {"vi": "Giáo viên luôn giải thích bài học một cách rõ ràng.", "en": "The teacher always explains the lesson clearly.", "explain": "'always' đặt trước động từ chính. 'clearly' = trạng từ."},
                ],
            },
            {
                "title": "Hiện tại tiếp diễn (Present Continuous)",
                "description": "Diễn tả hành động đang xảy ra tại thời điểm nói hoặc xu hướng hiện tại.",
                "sentences": [
                    {"vi": "Tôi đang học bài cho kỳ thi tuần tới.", "en": "I am studying for next week's exam.", "explain": "am/is/are + V-ing. 'next week's exam' dùng sở hữu cách."},
                    {"vi": "Cô ấy đang nấu bữa tối trong bếp.", "en": "She is cooking dinner in the kitchen.", "explain": "'is cooking' = đang nấu. 'in the kitchen' dùng 'in'."},
                    {"vi": "Họ đang xây dựng một tòa nhà mới ở trung tâm thành phố.", "en": "They are building a new building in the city centre.", "explain": "'a new building' dùng mạo từ 'a'. 'city centre' = trung tâm."},
                    {"vi": "Tại sao em lại khóc vậy?", "en": "Why are you crying?", "explain": "Câu hỏi Present Continuous: Why + are/is/am + S + V-ing?"},
                    {"vi": "Trời đang mưa rất to.", "en": "It is raining heavily.", "explain": "Thời tiết dùng 'It'. 'heavily' = to, mạnh."},
                    {"vi": "Công ty chúng tôi đang mở rộng sang thị trường châu Á.", "en": "Our company is expanding into the Asian market.", "explain": "'expand into' = mở rộng sang. 'Asian market' viết hoa."},
                    {"vi": "Thế giới đang thay đổi rất nhanh nhờ vào công nghệ.", "en": "The world is changing very rapidly due to technology.", "explain": "'due to' = nhờ vào / do. 'rapidly' = nhanh chóng."},
                    {"vi": "Nhiều người trẻ đang chọn làm việc từ xa thay vì đến văn phòng.", "en": "Many young people are choosing to work remotely rather than come to the office.", "explain": "'rather than' = thay vì. 'remotely' = từ xa."},
                ],
            },
            {
                "title": "Hiện tại hoàn thành (Present Perfect)",
                "description": "Diễn tả hành động đã xảy ra với kết quả còn liên quan đến hiện tại.",
                "sentences": [
                    {"vi": "Tôi đã học tiếng Anh được ba năm rồi.", "en": "I have studied English for three years.", "explain": "have/has + V3. 'for + khoảng thời gian'."},
                    {"vi": "Cô ấy vừa mới hoàn thành luận văn tiến sĩ.", "en": "She has just completed her doctoral thesis.", "explain": "'just' đặt giữa have và V3. 'doctoral thesis' = luận văn TS."},
                    {"vi": "Họ chưa bao giờ đến thăm Việt Nam.", "en": "They have never visited Vietnam.", "explain": "'never' đặt giữa have và V3 khi dùng Present Perfect."},
                    {"vi": "Anh ấy đã sống ở nước ngoài kể từ năm 2020.", "en": "He has lived abroad since 2020.", "explain": "'since + mốc thời gian'. 'abroad' = ở nước ngoài."},
                    {"vi": "Chính phủ đã ban hành nhiều chính sách mới để bảo vệ môi trường.", "en": "The government has issued many new policies to protect the environment.", "explain": "'issue policies' = ban hành chính sách. 'to protect' = để bảo vệ."},
                    {"vi": "Bao nhiêu lần bạn đã đọc cuốn sách này?", "en": "How many times have you read this book?", "explain": "Câu hỏi PP: How many times + have/has + S + V3?"},
                    {"vi": "Khoa học đã đạt được nhiều tiến bộ đáng kể trong thập kỷ qua.", "en": "Science has made significant progress in the past decade.", "explain": "'make progress' = đạt tiến bộ. 'past decade' = thập kỷ qua."},
                    {"vi": "Họ đã hoàn thành dự án trước thời hạn.", "en": "They have completed the project ahead of schedule.", "explain": "'ahead of schedule' = trước thời hạn (cụm cố định)."},
                ],
            },
            {
                "title": "Quá khứ đơn (Simple Past)",
                "description": "Diễn tả hành động đã hoàn tất trong quá khứ tại một thời điểm xác định.",
                "sentences": [
                    {"vi": "Tôi đã đến Hà Nội vào năm ngoái.", "en": "I went to Hanoi last year.", "explain": "'went' = quá khứ bất quy tắc của 'go'. 'last year' xác định thời điểm."},
                    {"vi": "Cô ấy đã tốt nghiệp đại học năm 2022.", "en": "She graduated from university in 2022.", "explain": "'graduate from' = tốt nghiệp từ. 'in 2022' = năm cụ thể."},
                    {"vi": "Chúng tôi đã gặp nhau lần đầu tại một hội nghị quốc tế.", "en": "We met for the first time at an international conference.", "explain": "'met' = quá khứ bất quy tắc của 'meet'. 'for the first time' = lần đầu."},
                    {"vi": "Anh ấy không đến buổi họp hôm qua vì bị ốm.", "en": "He did not attend the meeting yesterday because he was ill.", "explain": "Phủ định quá khứ: did not + V nguyên thể. 'ill' = bệnh (formal hơn 'sick')."},
                    {"vi": "Công ty đó được thành lập vào năm 1995.", "en": "That company was founded in 1995.", "explain": "Bị động quá khứ: was/were + V3. 'found → founded'."},
                    {"vi": "Trận động đất xảy ra vào lúc 3 giờ sáng.", "en": "The earthquake occurred at 3 o'clock in the morning.", "explain": "'occur' = xảy ra (formal). 'at' dùng với giờ cụ thể."},
                    {"vi": "Chính sách mới được thông qua sau nhiều tháng tranh luận.", "en": "The new policy was passed after months of debate.", "explain": "'pass a policy' = thông qua chính sách. 'months of debate' = nhiều tháng."},
                    {"vi": "Cô ấy đã cảm thấy rất hồi hộp trước buổi thuyết trình đó.", "en": "She felt very nervous before that presentation.", "explain": "'felt' = quá khứ bất quy tắc của 'feel'. 'nervous' = hồi hộp, lo lắng."},
                ],
            },
            {
                "title": "Câu bị động (Passive Voice)",
                "description": "Dùng khi muốn nhấn mạnh đối tượng bị tác động thay vì chủ thể hành động.",
                "sentences": [
                    {"vi": "Bức thư này được viết bằng tiếng Pháp.", "en": "This letter is written in French.", "explain": "Bị động hiện tại: is/are + V3. 'in French' = bằng tiếng Pháp."},
                    {"vi": "Tòa nhà đó đã được xây dựng vào thế kỷ 19.", "en": "That building was constructed in the 19th century.", "explain": "Bị động quá khứ: was/were + V3. '19th century' viết tắt đúng."},
                    {"vi": "Nhiều cây xanh đang bị chặt phá để xây dựng khu đô thị mới.", "en": "Many trees are being cut down to build new residential areas.", "explain": "Bị động tiếp diễn: are being + V3. 'cut down' = chặt phá."},
                    {"vi": "Bộ phim này đã được trao giải Oscar.", "en": "This film has been awarded an Oscar.", "explain": "Bị động hoàn thành: has/have been + V3. 'award' = trao."},
                    {"vi": "Rác thải nhựa cần được xử lý đúng cách để bảo vệ đại dương.", "en": "Plastic waste needs to be disposed of properly to protect the oceans.", "explain": "'dispose of' = xử lý (phrasal verb). 'properly' = đúng cách."},
                    {"vi": "Thuốc này phải được bảo quản ở nhiệt độ thấp.", "en": "This medicine must be stored at a low temperature.", "explain": "Modal passive: must be + V3. 'stored at' = bảo quản ở."},
                    {"vi": "Kết quả thi sẽ được công bố vào tuần tới.", "en": "The exam results will be announced next week.", "explain": "Bị động tương lai: will be + V3. 'announce' = công bố."},
                    {"vi": "Hệ thống giao thông đang được hiện đại hóa ở nhiều thành phố lớn.", "en": "The transportation system is being modernised in many major cities.", "explain": "'modernise' = hiện đại hóa (British spelling). 'major cities' = thành phố lớn."},
                ],
            },
            {
                "title": "Câu so sánh (Comparison)",
                "description": "So sánh hơn, so sánh nhất và so sánh bằng — nền tảng cho IELTS Task 1.",
                "sentences": [
                    {"vi": "Đọc sách có ích hơn xem tivi.", "en": "Reading books is more beneficial than watching television.", "explain": "'more + adj + than' cho tính từ dài. 'beneficial' = có ích."},
                    {"vi": "Hà Nội đông dân hơn Đà Nẵng nhiều.", "en": "Hanoi is much more densely populated than Da Nang.", "explain": "'much more' nhấn mạnh mức độ hơn. 'densely populated' = đông dân."},
                    {"vi": "Học trực tuyến là phương pháp tiện lợi nhất hiện nay.", "en": "Online learning is the most convenient method available today.", "explain": "'the most + adj' = so sánh nhất. 'available' bổ nghĩa cho 'method'."},
                    {"vi": "Tình trạng ô nhiễm không khí ngày càng nghiêm trọng hơn.", "en": "Air pollution is becoming increasingly serious.", "explain": "'becoming increasingly + adj' = ngày càng. Không cần 'than' ở đây."},
                    {"vi": "Không có gì quý giá hơn sức khỏe.", "en": "Nothing is more valuable than health.", "explain": "'Nothing is more + adj than' = cấu trúc nhấn mạnh so sánh hơn."},
                    {"vi": "Phương pháp này đơn giản hơn nhưng kém hiệu quả hơn.", "en": "This method is simpler but less effective.", "explain": "'less + adj' = kém hơn. 'simpler' = tính từ ngắn thêm -er."},
                    {"vi": "Công nghệ ngày nay tiên tiến hơn nhiều so với hai mươi năm trước.", "en": "Technology today is far more advanced than it was twenty years ago.", "explain": "'far more' nhấn mạnh mức độ. 'than it was' = so với khi đó."},
                    {"vi": "Kỹ năng mềm quan trọng không kém gì kiến thức chuyên môn.", "en": "Soft skills are just as important as professional knowledge.", "explain": "'just as + adj + as' = so sánh bằng. 'soft skills' = kỹ năng mềm."},
                ],
            },
            {
                "title": "Mệnh đề quan hệ (Relative Clauses)",
                "description": "Bổ nghĩa cho danh từ bằng who, which, that, where, whose — rất quan trọng trong IELTS.",
                "sentences": [
                    {"vi": "Người phụ nữ mà bạn vừa gặp là giám đốc công ty.", "en": "The woman whom you just met is the director of the company.", "explain": "'whom' = who (formal) cho tân ngữ. 'director of' = giám đốc của."},
                    {"vi": "Đây là thành phố nơi tôi sinh ra.", "en": "This is the city where I was born.", "explain": "'where' bổ nghĩa cho địa danh. 'was born' = bị động quá khứ."},
                    {"vi": "Những học sinh đạt điểm cao sẽ nhận học bổng.", "en": "Students who achieve high scores will receive scholarships.", "explain": "'who' bổ nghĩa cho người. 'scholarships' = học bổng (số nhiều)."},
                    {"vi": "Đây là giải pháp mà các chuyên gia khuyến nghị.", "en": "This is the solution that experts recommend.", "explain": "'that' cho người hoặc vật (informal). 'recommend' = khuyến nghị."},
                    {"vi": "Lý do tại sao anh ấy từ chối lời mời vẫn còn là bí ẩn.", "en": "The reason why he declined the invitation remains a mystery.", "explain": "'the reason why' = lý do tại sao. 'decline' = từ chối (formal)."},
                    {"vi": "Cuốn sách mà tôi đang đọc rất thú vị.", "en": "The book that I am reading is very interesting.", "explain": "Mệnh đề quan hệ xác định (defining RC) không có dấu phẩy."},
                    {"vi": "Nhà khoa học này, người đã phát minh ra vắc-xin, đã đoạt giải Nobel.", "en": "This scientist, who invented the vaccine, was awarded the Nobel Prize.", "explain": "Mệnh đề quan hệ không xác định (non-defining) có dấu phẩy."},
                    {"vi": "Những quốc gia có nền giáo dục tốt thường có mức sống cao hơn.", "en": "Countries whose education systems are strong tend to have higher living standards.", "explain": "'whose' = có (sở hữu). 'tend to' = có xu hướng."},
                ],
            },
            {
                "title": "Câu điều kiện (Conditionals)",
                "description": "If-clauses loại 0, 1, 2, 3 — thiết yếu cho IELTS Writing Task 2.",
                "sentences": [
                    {"vi": "Nếu bạn chăm chỉ học, bạn sẽ đạt điểm cao.", "en": "If you study hard, you will achieve high scores.", "explain": "Loại 1: If + present simple, will + V. Khả năng có thể xảy ra."},
                    {"vi": "Nếu chúng ta không hành động ngay bây giờ, ô nhiễm sẽ trở nên tồi tệ hơn.", "en": "If we do not act now, pollution will become worse.", "explain": "Loại 1. 'act now' = hành động ngay. 'become worse' = trở nên tồi tệ."},
                    {"vi": "Nếu tôi giàu hơn, tôi sẽ du lịch vòng quanh thế giới.", "en": "If I were richer, I would travel around the world.", "explain": "Loại 2: If + were/V-ed, would + V. Tình huống không có thật ở hiện tại."},
                    {"vi": "Nếu chính phủ đầu tư nhiều hơn vào giáo dục, chất lượng cuộc sống sẽ được cải thiện.", "en": "If the government invested more in education, the quality of life would improve.", "explain": "Loại 2. 'invest in' = đầu tư vào. 'quality of life' = chất lượng cuộc sống."},
                    {"vi": "Nếu anh ấy đã học chăm hơn, anh ấy đã không thi trượt.", "en": "If he had studied harder, he would not have failed the exam.", "explain": "Loại 3: If + had V3, would have V3. Hối tiếc về quá khứ."},
                    {"vi": "Trừ khi chúng ta giảm lượng khí thải carbon, biến đổi khí hậu sẽ tiếp tục leo thang.", "en": "Unless we reduce carbon emissions, climate change will continue to escalate.", "explain": "'Unless' = if not. 'carbon emissions' = khí thải carbon. 'escalate' = leo thang."},
                    {"vi": "Miễn là bạn có quyết tâm, bạn có thể đạt được bất kỳ mục tiêu nào.", "en": "As long as you have determination, you can achieve any goal.", "explain": "'As long as' = miễn là (điều kiện). 'determination' = quyết tâm."},
                    {"vi": "Giả sử chính sách này được thực thi, nền kinh tế sẽ phục hồi nhanh hơn.", "en": "Supposing this policy were implemented, the economy would recover more quickly.", "explain": "'Supposing' = giả sử (formal). Loại 2. 'implement' = thực thi."},
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────
    # BƯỚC 2 – Collocations & Từ vựng học thuật
    # ────────────────────────────────────────────────────────────────────────
    {
        "title": "Collocations & Từ vựng học thuật",
        "description": "Dịch các câu sử dụng collocations IELTS phổ biến. Nắm vững các cụm từ này giúp bài thi đạt Band 7+.",
        "badge_label": "VOCAB",
        "badge_color": "blue",
        "icon_emoji": "📚",
        "topics": [
            {
                "title": "Collocations: Giáo dục (Education)",
                "description": "Các cụm từ thiết yếu về chủ đề Giáo dục cho IELTS.",
                "sentences": [
                    {"vi": "Giáo dục đóng vai trò then chốt trong việc xây dựng một xã hội văn minh.", "en": "Education plays a pivotal role in building a civilised society.", "explain": "'play a pivotal role' = đóng vai trò then chốt (collocation mạnh)."},
                    {"vi": "Nhiều học sinh phải vật lộn với áp lực học tập trong suốt những năm học phổ thông.", "en": "Many students struggle with academic pressure throughout their secondary school years.", "explain": "'struggle with' = vật lộn với. 'academic pressure' = áp lực học tập."},
                    {"vi": "Tư duy phản biện là kỹ năng thiết yếu mà hệ thống giáo dục cần bồi dưỡng.", "en": "Critical thinking is an essential skill that the education system needs to cultivate.", "explain": "'critical thinking' = tư duy phản biện. 'cultivate' = bồi dưỡng/nuôi dưỡng."},
                    {"vi": "Việc học ngoại ngữ từ sớm mang lại lợi ích lớn cho sự phát triển nhận thức của trẻ.", "en": "Learning foreign languages from an early age brings significant benefits to children's cognitive development.", "explain": "'cognitive development' = phát triển nhận thức. 'from an early age' = từ sớm."},
                    {"vi": "Chính sách giáo dục toàn diện cần đáp ứng nhu cầu của tất cả học sinh, kể cả người khuyết tật.", "en": "Inclusive education policies need to address the needs of all students, including those with disabilities.", "explain": "'inclusive education' = giáo dục toàn diện. 'address needs' = đáp ứng nhu cầu."},
                    {"vi": "Sự chênh lệch về chất lượng giáo dục giữa thành thị và nông thôn cần được thu hẹp.", "en": "The disparity in educational quality between urban and rural areas needs to be narrowed.", "explain": "'disparity' = sự chênh lệch (academic). 'narrowed' = thu hẹp."},
                    {"vi": "Các trường đại học nên trang bị cho sinh viên những kỹ năng thực tiễn phù hợp với yêu cầu thị trường lao động.", "en": "Universities should equip students with practical skills relevant to the demands of the labour market.", "explain": "'equip with' = trang bị. 'relevant to' = phù hợp với. 'labour market' = thị trường lao động."},
                    {"vi": "Học tập suốt đời là yếu tố quan trọng để thích nghi với những thay đổi nhanh chóng của xã hội.", "en": "Lifelong learning is an essential factor in adapting to the rapid changes in society.", "explain": "'lifelong learning' = học tập suốt đời. 'adapt to' = thích nghi với."},
                ],
            },
            {
                "title": "Collocations: Môi trường (Environment)",
                "description": "Các cụm từ quan trọng về chủ đề Môi trường — chủ đề xuất hiện thường xuyên trong IELTS.",
                "sentences": [
                    {"vi": "Biến đổi khí hậu là mối đe dọa nghiêm trọng nhất đối với sự tồn tại của nhân loại.", "en": "Climate change poses the most serious threat to the survival of humanity.", "explain": "'pose a threat' = đặt ra mối đe dọa. 'survival of humanity' = sự tồn tại của nhân loại."},
                    {"vi": "Nạn phá rừng đang phá hủy các hệ sinh thái quý giá và đẩy nhanh quá trình mất đa dạng sinh học.", "en": "Deforestation is destroying precious ecosystems and accelerating the loss of biodiversity.", "explain": "'deforestation' = nạn phá rừng. 'biodiversity' = đa dạng sinh học. 'accelerate' = đẩy nhanh."},
                    {"vi": "Năng lượng tái tạo đang dần thay thế nhiên liệu hóa thạch ở nhiều quốc gia.", "en": "Renewable energy is gradually replacing fossil fuels in many countries.", "explain": "'renewable energy' = năng lượng tái tạo. 'fossil fuels' = nhiên liệu hóa thạch."},
                    {"vi": "Phát triển bền vững đòi hỏi sự cân bằng giữa tăng trưởng kinh tế và bảo tồn thiên nhiên.", "en": "Sustainable development requires a balance between economic growth and the conservation of nature.", "explain": "'sustainable development' = phát triển bền vững. 'conservation' = bảo tồn."},
                    {"vi": "Các chính phủ cần áp đặt các quy định nghiêm ngặt hơn đối với các ngành công nghiệp gây ô nhiễm.", "en": "Governments need to impose stricter regulations on polluting industries.", "explain": "'impose regulations' = áp đặt quy định. 'stricter' = so sánh hơn của 'strict'."},
                    {"vi": "Ô nhiễm không khí làm trầm trọng thêm các bệnh về đường hô hấp và làm giảm tuổi thọ.", "en": "Air pollution exacerbates respiratory diseases and reduces life expectancy.", "explain": "'exacerbate' = làm trầm trọng thêm (C2). 'life expectancy' = tuổi thọ."},
                    {"vi": "Ý thức bảo vệ môi trường của người dân đã được nâng cao đáng kể trong những năm gần đây.", "en": "Public awareness of environmental protection has grown considerably in recent years.", "explain": "'public awareness' = ý thức cộng đồng. 'grow considerably' = tăng đáng kể."},
                    {"vi": "Việc giảm lượng khí thải carbon dioxide là ưu tiên hàng đầu trong cuộc chiến chống biến đổi khí hậu.", "en": "Reducing carbon dioxide emissions is a top priority in the fight against climate change.", "explain": "'top priority' = ưu tiên hàng đầu. 'in the fight against' = trong cuộc chiến chống lại."},
                ],
            },
            {
                "title": "Collocations: Công nghệ (Technology)",
                "description": "Từ vựng và cụm từ về chủ đề Công nghệ — Band 7+ topic.",
                "sentences": [
                    {"vi": "Trí tuệ nhân tạo đang biến đổi cơ bản cách chúng ta làm việc và giao tiếp.", "en": "Artificial intelligence is fundamentally transforming the way we work and communicate.", "explain": "'fundamentally transform' = biến đổi cơ bản. 'the way we' = cách chúng ta."},
                    {"vi": "Sự bùng nổ của mạng xã hội đã có tác động sâu sắc đến hành vi của người tiêu dùng.", "en": "The proliferation of social media has had a profound impact on consumer behaviour.", "explain": "'proliferation' = sự bùng nổ/lan rộng (formal). 'profound impact' = tác động sâu sắc."},
                    {"vi": "Tự động hóa có thể thay thế nhiều công việc lao động tay chân, dẫn đến thất nghiệp quy mô lớn.", "en": "Automation may replace many manual jobs, leading to large-scale unemployment.", "explain": "'automation' = tự động hóa. 'manual jobs' = công việc chân tay. 'large-scale' = quy mô lớn."},
                    {"vi": "Khoảng cách số giữa các quốc gia phát triển và đang phát triển ngày càng mở rộng.", "en": "The digital divide between developed and developing nations is widening.", "explain": "'digital divide' = khoảng cách số (cụm quan trọng). 'widening' = đang mở rộng."},
                    {"vi": "Đổi mới công nghệ phải đi đôi với bảo đảm quyền riêng tư và an ninh dữ liệu.", "en": "Technological innovation must go hand in hand with ensuring data privacy and security.", "explain": "'go hand in hand' = đi đôi với (idiom). 'data privacy' = quyền riêng tư dữ liệu."},
                    {"vi": "Internet vạn vật đang tạo ra các thành phố thông minh nơi mọi thiết bị đều được kết nối.", "en": "The Internet of Things is creating smart cities where every device is interconnected.", "explain": "'Internet of Things (IoT)' = internet vạn vật. 'interconnected' = kết nối với nhau."},
                    {"vi": "Công nghệ giáo dục đang mở ra cơ hội học tập cho hàng triệu người ở vùng sâu vùng xa.", "en": "Educational technology is opening up learning opportunities for millions of people in remote areas.", "explain": "'open up opportunities' = mở ra cơ hội. 'remote areas' = vùng sâu vùng xa."},
                    {"vi": "Phụ thuộc quá mức vào thiết bị kỹ thuật số có thể gây ra những hậu quả tiêu cực về mặt tâm lý.", "en": "Excessive reliance on digital devices can have negative psychological consequences.", "explain": "'excessive reliance on' = phụ thuộc quá mức vào. 'psychological' = thuộc về tâm lý."},
                ],
            },
            {
                "title": "Collocations: Sức khỏe & Xã hội",
                "description": "Từ vựng học thuật về sức khỏe cộng đồng và các vấn đề xã hội.",
                "sentences": [
                    {"vi": "Béo phì là mối quan tâm sức khỏe cộng đồng ngày càng nghiêm trọng ở nhiều quốc gia.", "en": "Obesity is an increasingly pressing public health concern in many countries.", "explain": "'pressing concern' = mối lo ngại cấp bách. 'public health' = sức khỏe cộng đồng."},
                    {"vi": "Sức khỏe tâm thần đã được nhìn nhận là một phần không thể tách rời của sức khỏe tổng thể.", "en": "Mental health has been recognised as an integral part of overall well-being.", "explain": "'integral part' = phần không thể tách rời. 'well-being' = sức khỏe tổng thể/hạnh phúc."},
                    {"vi": "Bất bình đẳng thu nhập ngày càng gia tăng đe dọa nghiêm trọng đến sự gắn kết xã hội.", "en": "Growing income inequality poses a significant threat to social cohesion.", "explain": "'income inequality' = bất bình đẳng thu nhập. 'social cohesion' = sự gắn kết xã hội."},
                    {"vi": "Đại dịch COVID-19 đã phơi bày những điểm yếu nghiêm trọng trong hệ thống y tế toàn cầu.", "en": "The COVID-19 pandemic exposed serious weaknesses in the global healthcare system.", "explain": "'expose weaknesses' = phơi bày điểm yếu. 'healthcare system' = hệ thống y tế."},
                    {"vi": "Đô thị hóa nhanh chóng dẫn đến việc hình thành các khu ổ chuột ở vùng ngoại ô của nhiều thành phố.", "en": "Rapid urbanisation leads to the emergence of slums on the outskirts of many cities.", "explain": "'urbanisation' = đô thị hóa. 'slums' = khu ổ chuột. 'outskirts' = ngoại ô."},
                    {"vi": "Áp lực công việc cường độ cao có thể dẫn đến kiệt sức và các vấn đề sức khỏe nghiêm trọng.", "en": "High-intensity work pressure can lead to burnout and serious health problems.", "explain": "'lead to burnout' = dẫn đến kiệt sức. 'burnout' = tình trạng kiệt sức (thuật ngữ)."},
                    {"vi": "Trách nhiệm xã hội của doanh nghiệp đã trở thành yếu tố quan trọng trong chiến lược kinh doanh hiện đại.", "en": "Corporate social responsibility has become a crucial factor in modern business strategy.", "explain": "'corporate social responsibility (CSR)' = trách nhiệm xã hội doanh nghiệp."},
                    {"vi": "Tình nguyện và từ thiện là biểu hiện quan trọng của trách nhiệm công dân và tinh thần cộng đồng.", "en": "Volunteering and philanthropy are vital expressions of civic responsibility and community spirit.", "explain": "'philanthropy' = hoạt động từ thiện. 'civic responsibility' = trách nhiệm công dân."},
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────
    # BƯỚC 3 – Dịch đoạn văn Band 6.5
    # ────────────────────────────────────────────────────────────────────────
    {
        "title": "Dịch đoạn văn Band 6.5",
        "description": "Luyện dịch các đoạn văn ngắn từ Việt sang Anh với mục tiêu đạt độ chính xác và mạch lạc ở mức Band 6.5.",
        "badge_label": "BAND 6.5",
        "badge_color": "green",
        "icon_emoji": "🎯",
        "topics": [
            {
                "title": "Đoạn văn: Vai trò của Giáo dục",
                "description": "Dịch các đoạn văn bàn về tầm quan trọng của giáo dục.",
                "sentences": [
                    {"vi": "Giáo dục là nền tảng của một xã hội thịnh vượng. Đầu tư vào giáo dục không chỉ nâng cao chất lượng nguồn nhân lực mà còn thúc đẩy sự phát triển kinh tế bền vững.", "en": "Education is the foundation of a prosperous society. Investing in education not only improves the quality of the workforce but also promotes sustainable economic development.", "explain": "'not only ... but also ...' = không chỉ ... mà còn. 'workforce' = lực lượng lao động. 'sustainable' = bền vững."},
                    {"vi": "Khoảng cách về cơ hội học tập giữa học sinh thành thị và nông thôn vẫn là vấn đề đáng lo ngại. Học sinh ở vùng nông thôn thường thiếu tiếp cận với cơ sở hạ tầng giáo dục hiện đại và giáo viên có trình độ chuyên môn cao.", "en": "The gap in educational opportunities between urban and rural students remains a concerning issue. Students in rural areas often lack access to modern educational infrastructure and highly qualified teachers.", "explain": "'lack access to' = thiếu tiếp cận với. 'infrastructure' = cơ sở hạ tầng. 'qualified' = có chuyên môn."},
                    {"vi": "Trong thế giới ngày càng toàn cầu hóa, khả năng giao tiếp bằng tiếng Anh là lợi thế cạnh tranh quan trọng. Những người thành thạo ngoại ngữ thường có cơ hội nghề nghiệp tốt hơn và thu nhập cao hơn so với những người chỉ biết tiếng mẹ đẻ.", "en": "In an increasingly globalised world, the ability to communicate in English is a significant competitive advantage. Those who are proficient in foreign languages tend to have better career opportunities and higher incomes compared to those who only speak their native language.", "explain": "'proficient in' = thành thạo. 'competitive advantage' = lợi thế cạnh tranh. 'native language' = tiếng mẹ đẻ."},
                    {"vi": "Một hệ thống giáo dục chất lượng cao cần phải cân bằng giữa việc truyền đạt kiến thức lý thuyết và phát triển kỹ năng thực hành. Chỉ học thuộc lòng mà không hiểu bản chất vấn đề sẽ cản trở khả năng tư duy sáng tạo của học sinh.", "en": "A high-quality education system needs to strike a balance between imparting theoretical knowledge and developing practical skills. Rote memorisation without genuine understanding will hinder students' capacity for creative thinking.", "explain": "'strike a balance' = cân bằng. 'rote memorisation' = học vẹt. 'hinder' = cản trở."},
                    {"vi": "Nhiều chuyên gia lập luận rằng hệ thống giáo dục truyền thống đang lỗi thời trước sự phát triển nhanh chóng của thị trường lao động. Thay vào đó, các trường học nên ưu tiên phát triển tư duy phản biện, kỹ năng giải quyết vấn đề và khả năng thích nghi.", "en": "Many experts argue that the traditional education system is becoming outdated in the face of the rapidly evolving labour market. Instead, schools should prioritise developing critical thinking, problem-solving skills, and adaptability.", "explain": "'argue that' = lập luận rằng. 'outdated' = lỗi thời. 'adaptability' = khả năng thích nghi."},
                ],
            },
            {
                "title": "Đoạn văn: Môi trường và Con người",
                "description": "Dịch các đoạn văn về các vấn đề môi trường — chủ đề Band 6.5 phổ biến.",
                "sentences": [
                    {"vi": "Ô nhiễm môi trường đang ngày càng trở thành mối lo ngại toàn cầu. Các hoạt động công nghiệp và giao thông vận tải thải ra lượng lớn khí CO₂, góp phần làm tăng nhiệt độ trái đất và gây ra những biến đổi khí hậu nghiêm trọng.", "en": "Environmental pollution is becoming an increasingly global concern. Industrial activities and transportation emit large amounts of CO₂, contributing to rising global temperatures and causing severe climate changes.", "explain": "'emit' = thải ra. 'contributing to' = góp phần vào. 'severe' = nghiêm trọng."},
                    {"vi": "Một trong những nguyên nhân chính gây ra ô nhiễm nguồn nước là việc xả thải chất thải công nghiệp chưa qua xử lý ra các con sông và hồ. Điều này không chỉ ảnh hưởng đến hệ sinh thái thủy sinh mà còn đe dọa sức khỏe của cộng đồng dân cư sống xung quanh.", "en": "One of the primary causes of water pollution is the discharge of untreated industrial waste into rivers and lakes. This not only affects aquatic ecosystems but also threatens the health of communities living nearby.", "explain": "'discharge' = xả thải. 'untreated' = chưa qua xử lý. 'aquatic ecosystems' = hệ sinh thái thủy sinh."},
                    {"vi": "Việc sử dụng năng lượng tái tạo như điện mặt trời và điện gió đang ngày càng trở nên phổ biến hơn nhờ vào chi phí ngày càng giảm và hiệu quả ngày càng tăng. Nhiều quốc gia đang đặt ra các mục tiêu đầy tham vọng để đạt mức phát thải ròng bằng không vào năm 2050.", "en": "The use of renewable energy sources such as solar and wind power is becoming increasingly popular due to falling costs and rising efficiency. Many countries are setting ambitious targets to achieve net-zero emissions by 2050.", "explain": "'net-zero emissions' = phát thải ròng bằng 0. 'ambitious targets' = mục tiêu đầy tham vọng."},
                    {"vi": "Ý thức bảo vệ môi trường cần được giáo dục từ khi còn nhỏ. Khi trẻ em được dạy về tầm quan trọng của việc tiết kiệm năng lượng, phân loại rác thải và bảo vệ thiên nhiên, chúng sẽ lớn lên với tinh thần trách nhiệm cao hơn đối với hành tinh của mình.", "en": "Environmental awareness needs to be taught from an early age. When children are educated about the importance of saving energy, sorting waste, and protecting nature, they will grow up with a stronger sense of responsibility towards their planet.", "explain": "'environmental awareness' = ý thức bảo vệ MT. 'sense of responsibility' = tinh thần trách nhiệm."},
                    {"vi": "Nhiều thành phố lớn trên thế giới đang áp dụng mô hình thành phố xanh nhằm giảm lượng khí thải và cải thiện chất lượng cuộc sống của người dân. Các giải pháp như giao thông công cộng bằng điện, không gian xanh và tòa nhà tiết kiệm năng lượng đang được triển khai rộng rãi.", "en": "Many major cities around the world are adopting the green city model to reduce emissions and improve residents' quality of life. Solutions such as electric public transport, green spaces, and energy-efficient buildings are being widely implemented.", "explain": "'adopt a model' = áp dụng mô hình. 'energy-efficient' = tiết kiệm năng lượng. 'implement' = triển khai."},
                ],
            },
            {
                "title": "Đoạn văn: Công nghệ & Xã hội",
                "description": "Các đoạn văn thảo luận tác động của công nghệ đến cuộc sống hiện đại.",
                "sentences": [
                    {"vi": "Cuộc cách mạng công nghiệp 4.0 đang thay đổi căn bản mọi lĩnh vực của cuộc sống, từ sản xuất công nghiệp cho đến dịch vụ y tế và giáo dục. Những công nghệ như trí tuệ nhân tạo, blockchain và internet vạn vật đang tái định hình nền kinh tế toàn cầu.", "en": "The Fourth Industrial Revolution is fundamentally changing every aspect of life, from industrial production to healthcare and education services. Technologies such as artificial intelligence, blockchain, and the Internet of Things are reshaping the global economy.", "explain": "'reshape' = tái định hình. 'every aspect of' = mọi lĩnh vực của. 'fundamentally' = căn bản."},
                    {"vi": "Mặc dù công nghệ mang lại nhiều lợi ích to lớn, nhưng nó cũng tạo ra những thách thức mới. Vấn đề quyền riêng tư dữ liệu và an ninh mạng ngày càng trở nên cấp bách trong bối cảnh ngày càng có nhiều thông tin cá nhân được lưu trữ và xử lý trực tuyến.", "en": "Although technology brings many significant benefits, it also creates new challenges. The issues of data privacy and cybersecurity are becoming increasingly urgent as more personal information is stored and processed online.", "explain": "'Although' nhượng bộ. 'cybersecurity' = an ninh mạng. 'urgent' = cấp bách."},
                    {"vi": "Sự phát triển của truyền thông xã hội đã tạo ra cả những cơ hội và nguy cơ mới. Một mặt, nó cho phép mọi người kết nối và chia sẻ thông tin nhanh chóng hơn bao giờ hết. Mặt khác, nó cũng là mảnh đất màu mỡ cho việc lan truyền thông tin sai lệch và ngôn từ thù hận.", "en": "The development of social media has created both new opportunities and new risks. On the one hand, it enables people to connect and share information faster than ever before. On the other hand, it has also become a fertile ground for the spread of misinformation and hate speech.", "explain": "'On the one hand ... On the other hand' = Một mặt ... Mặt khác. 'misinformation' = thông tin sai lệch. 'fertile ground' = mảnh đất màu mỡ (ẩn dụ)."},
                    {"vi": "Làm việc từ xa đã trở nên phổ biến hơn đáng kể kể từ đại dịch COVID-19. Mô hình làm việc linh hoạt này mang lại nhiều lợi ích như tiết kiệm thời gian đi lại và tăng sự cân bằng giữa công việc và cuộc sống, nhưng cũng đặt ra những thách thức trong việc duy trì sự gắn kết nhóm và quản lý năng suất.", "en": "Remote working has become significantly more prevalent since the COVID-19 pandemic. This flexible working model offers several benefits such as saving commuting time and improving work-life balance, but also poses challenges in maintaining team cohesion and managing productivity.", "explain": "'prevalent' = phổ biến. 'work-life balance' = cân bằng công việc-cuộc sống. 'team cohesion' = sự gắn kết nhóm."},
                    {"vi": "Tự động hóa và trí tuệ nhân tạo đang thay thế ngày càng nhiều công việc lặp đi lặp lại trong nhiều ngành. Điều này đặt ra câu hỏi cấp bách về việc đào tạo lại lực lượng lao động và đảm bảo rằng những lợi ích của tiến bộ công nghệ được phân bổ công bằng trong xã hội.", "en": "Automation and artificial intelligence are replacing an increasing number of repetitive jobs across many industries. This raises an urgent question about retraining the workforce and ensuring that the benefits of technological progress are equitably distributed across society.", "explain": "'retraining' = đào tạo lại. 'equitably distributed' = phân bổ công bằng. 'across society' = trong toàn xã hội."},
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────
    # BƯỚC 4 – Dịch đoạn văn Band 8.0
    # ────────────────────────────────────────────────────────────────────────
    {
        "title": "Dịch đoạn văn Band 8.0",
        "description": "Thử thách dịch các đoạn văn phức tạp, yêu cầu sử dụng từ vựng ít phổ biến và cấu trúc câu linh hoạt của Band 8.0.",
        "badge_label": "BAND 8.0",
        "badge_color": "orange",
        "icon_emoji": "🏆",
        "topics": [
            {
                "title": "Luận điểm nâng cao: Giáo dục & Xã hội",
                "description": "Dịch các đoạn lập luận phức tạp về giáo dục và xã hội ở mức Band 8.0.",
                "sentences": [
                    {"vi": "Có một quan điểm ngày càng phổ biến rằng các phương pháp sư phạm truyền thống, vốn đặt giáo viên làm trung tâm và nhấn mạnh vào việc tiếp thu kiến thức thụ động, đang ngăn cản học sinh phát triển tư duy độc lập và kỹ năng giải quyết vấn đề — những năng lực thiết yếu trong thế kỷ 21.", "en": "There is a growing consensus that traditional pedagogical approaches, which are teacher-centred and emphasise passive knowledge acquisition, are inhibiting students from developing independent thinking and problem-solving abilities — competencies that are indispensable in the twenty-first century.", "explain": "'pedagogical' = thuộc sư phạm. 'inhibiting' = ngăn cản. 'indispensable' = thiết yếu/không thể thiếu (C2)."},
                    {"vi": "Mặc dù nhiều người lập luận rằng toàn cầu hóa đã thúc đẩy trao đổi văn hóa và hiểu biết lẫn nhau, nhưng không thể phủ nhận rằng nó cũng đã làm xói mòn bản sắc văn hóa địa phương và gia tăng sự phụ thuộc kinh tế của các quốc gia đang phát triển vào các nền kinh tế phát triển.", "en": "While many argue that globalisation has promoted cultural exchange and mutual understanding, it cannot be denied that it has also eroded local cultural identities and increased the economic dependence of developing nations on developed economies.", "explain": "'erode' = xói mòn (hình tượng). 'mutual understanding' = hiểu biết lẫn nhau. 'economic dependence' = phụ thuộc kinh tế."},
                    {"vi": "Cuộc khủng hoảng khí hậu không đơn thuần là một vấn đề môi trường mà còn là một cuộc khủng hoảng công bằng xã hội sâu sắc. Những cộng đồng dễ bị tổn thương nhất, đặc biệt là ở các nước đang phát triển, phải gánh chịu những hậu quả nặng nề nhất của một vấn đề mà họ chỉ đóng góp rất ít vào nguyên nhân gây ra.", "en": "The climate crisis is not merely an environmental issue but also a profound social justice crisis. The most vulnerable communities, particularly in developing nations, bear the heaviest consequences of a problem to which they have contributed the least.", "explain": "'profound' = sâu sắc. 'bear the consequences' = gánh chịu hậu quả. 'vulnerable' = dễ bị tổn thương."},
                    {"vi": "Trong khi những tiến bộ trong y học đã kéo dài đáng kể tuổi thọ con người, vẫn còn những câu hỏi đạo đức phức tạp xung quanh việc phân bổ nguồn lực y tế khan hiếm. Câu hỏi liệu có nên ưu tiên các biện pháp điều trị kéo dài sự sống tốn kém hay tập trung vào chăm sóc sức khỏe phòng ngừa chi phí thấp cho đông đảo dân số hơn vẫn còn là chủ đề tranh luận gay gắt.", "en": "While advances in medicine have significantly extended human lifespans, complex ethical questions remain surrounding the allocation of scarce medical resources. Whether priority should be given to expensive life-prolonging treatments or to low-cost preventive healthcare for a larger proportion of the population remains a contentious subject.", "explain": "'scarce resources' = nguồn lực khan hiếm. 'allocation' = phân bổ. 'contentious' = gây tranh cãi (C2)."},
                    {"vi": "Một số nhà kinh tế học lập luận rằng sự gia tăng của bất bình đẳng kinh tế ở các xã hội hiện đại không phải là một hiện tượng ngẫu nhiên mà là kết quả tất yếu của các chính sách thuế ưu đãi cho vốn hơn lao động, sự suy yếu của công đoàn và việc tự động hóa ưu tiên thay thế lao động giản đơn.", "en": "Some economists argue that the rise of economic inequality in modern societies is not a random phenomenon but rather an inevitable consequence of tax policies favouring capital over labour, the weakening of trade unions, and automation that disproportionately displaces low-skilled workers.", "explain": "'disproportionately' = không cân xứng. 'trade unions' = công đoàn. 'inevitable consequence' = hậu quả tất yếu."},
                ],
            },
            {
                "title": "Phân tích chuyên sâu: Khoa học & Đổi mới",
                "description": "Dịch các đoạn văn mang tính học thuật cao về khoa học và công nghệ ở Band 8.0.",
                "sentences": [
                    {"vi": "Sự hội tụ của trí tuệ nhân tạo, điện toán lượng tử và công nghệ sinh học đang mở ra những khả năng mà trước đây chỉ tồn tại trong lĩnh vực khoa học viễn tưởng. Tuy nhiên, tốc độ phát triển của những công nghệ này đang vượt xa khả năng của các khung pháp lý hiện hành trong việc giải quyết các rủi ro và tác động đạo đức liên quan.", "en": "The convergence of artificial intelligence, quantum computing, and biotechnology is unlocking possibilities that previously existed only in the realm of science fiction. However, the pace of development of these technologies is far outstripping the capacity of existing regulatory frameworks to address the associated risks and ethical implications.", "explain": "'convergence' = sự hội tụ. 'outstrip' = vượt xa. 'regulatory frameworks' = khung pháp lý."},
                    {"vi": "Dữ liệu lớn đã trở thành nguồn tài nguyên chiến lược quan trọng nhất của thế kỷ 21, đôi khi được ví như dầu mỏ của kỷ nguyên số. Sức mạnh kinh tế và chính trị ngày càng tập trung vào tay các công ty công nghệ khổng lồ có khả năng thu thập, phân tích và khai thác lượng dữ liệu khổng lồ về hành vi của hàng tỷ người dùng.", "en": "Big data has become the most strategically important resource of the twenty-first century, often likened to the oil of the digital era. Economic and political power is increasingly concentrated in the hands of technology giants with the capacity to collect, analyse, and exploit vast amounts of data about the behaviour of billions of users.", "explain": "'likened to' = được ví như. 'strategically important' = quan trọng về mặt chiến lược. 'exploit' = khai thác."},
                    {"vi": "Cuộc tranh luận về vai trò của nhà nước trong việc quản lý các nền tảng truyền thông xã hội phản ánh sự căng thẳng cơ bản giữa hai giá trị cốt lõi của xã hội dân chủ: tự do ngôn luận và bảo vệ cộng đồng khỏi nội dung có hại. Không có giải pháp nào hoàn hảo cho sự đánh đổi này, và mọi can thiệp đều kéo theo những rủi ro không lường trước được.", "en": "The debate over the role of the state in regulating social media platforms reflects a fundamental tension between two core values of democratic society: freedom of expression and the protection of communities from harmful content. No perfect solution exists for this trade-off, and every intervention carries unforeseen risks.", "explain": "'trade-off' = sự đánh đổi. 'unforeseen' = không lường trước được. 'fundamental tension' = sự căng thẳng cơ bản."},
                    {"vi": "Mặc dù cải cách giáo dục thường được coi là chìa khóa giải quyết bất bình đẳng kinh tế, nhưng bằng chứng thực nghiệm cho thấy tác động của giáo dục đến tính di động xã hội bị hạn chế đáng kể bởi các yếu tố cấu trúc rộng hơn như sự tập trung của cải, sự phân tầng địa lý và phân biệt đối xử có hệ thống.", "en": "Although educational reform is often regarded as the key to addressing economic inequality, empirical evidence suggests that education's impact on social mobility is significantly constrained by broader structural factors such as wealth concentration, geographical stratification, and systemic discrimination.", "explain": "'empirical evidence' = bằng chứng thực nghiệm. 'social mobility' = tính di động xã hội. 'systemic' = có hệ thống."},
                    {"vi": "Khủng hoảng đa dạng sinh học mà hành tinh chúng ta đang phải đối mặt — với tốc độ tuyệt chủng ước tính cao hơn 1.000 lần so với mức nền tự nhiên — là minh chứng bi thảm nhất cho tác động của hoạt động con người đến hệ sinh thái toàn cầu. Mất mát không thể khắc phục này không chỉ là thảm họa sinh thái mà còn đe dọa trực tiếp đến an ninh lương thực, sức khỏe cộng đồng và sự ổn định của khí hậu.", "en": "The biodiversity crisis facing our planet — with extinction rates estimated to be 1,000 times higher than natural background levels — is the most tragic testament to the impact of human activity on global ecosystems. This irreversible loss is not merely an ecological catastrophe but also poses a direct threat to food security, public health, and climate stability.", "explain": "'testament to' = minh chứng cho. 'irreversible' = không thể khắc phục. 'ecological catastrophe' = thảm họa sinh thái."},
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────
    # BƯỚC 5 – Dịch Essay hoàn chỉnh (IELTS Task 2 style)
    # ────────────────────────────────────────────────────────────────────────
    {
        "title": "Dịch Essay hoàn chỉnh",
        "description": "Luyện dịch nguyên một đoạn bài Essay từ dàn ý tiếng Việt sang bài viết tiếng Anh học thuật hoàn chỉnh ở mức Band 8.0+.",
        "badge_label": "PREMIUM",
        "badge_color": "purple",
        "icon_emoji": "🎓",
        "topics": [
            {
                "title": "Essay Task 2: Mở bài & Thân bài — Giáo dục",
                "description": "Dịch từng phần của bài IELTS Task 2 về chủ đề giáo dục.",
                "sentences": [
                    {"vi": "Ngày nay, câu hỏi liệu chính phủ có nên chịu trách nhiệm chính trong việc tài trợ cho giáo dục đại học hay chi phí này nên được chuyển sang cho cá nhân sinh viên là một chủ đề gây tranh luận sôi nổi. Mặc dù có lập luận thuyết phục cho cả hai quan điểm, tôi tin rằng một hệ thống lai kết hợp tài trợ công và đóng góp của sinh viên là giải pháp thực tế nhất.", "en": "In today's world, the question of whether governments should bear the primary responsibility for funding higher education, or whether this cost should be shifted to individual students, is a hotly contested topic. While there are compelling arguments on both sides, I believe that a hybrid system combining public funding and student contributions represents the most pragmatic solution.", "explain": "'hotly contested' = gây tranh cãi gay gắt. 'compelling arguments' = lập luận thuyết phục. 'pragmatic' = thực tế, thực dụng."},
                    {"vi": "Những người ủng hộ giáo dục đại học miễn phí lập luận rằng đây là điều kiện cần thiết để đảm bảo bình đẳng cơ hội trong xã hội. Khi chi phí học phí cao cản trở những sinh viên có tài năng nhưng xuất thân từ các gia đình thu nhập thấp, điều đó không chỉ là bất công với cá nhân mà còn là sự lãng phí tiềm năng nhân lực to lớn của quốc gia.", "en": "Proponents of free higher education argue that it is a prerequisite for ensuring equality of opportunity within society. When high tuition fees deter talented students from low-income backgrounds, this constitutes not only an injustice to the individual but also a significant waste of a nation's human potential.", "explain": "'proponents' = những người ủng hộ. 'prerequisite' = điều kiện tiên quyết. 'deter' = cản trở, làm nản lòng."},
                    {"vi": "Tuy nhiên, quan điểm cho rằng gánh nặng chi phí giáo dục đại học chỉ nên do người nộp thuế chịu là không hoàn toàn thuyết phục. Những cá nhân có bằng đại học thường thu nhập cao hơn đáng kể so với những người không có bằng, điều đó có nghĩa là họ sẽ đóng góp nhiều hơn vào ngân sách nhà nước thông qua thuế thu nhập. Do đó, có cơ sở hợp lý để yêu cầu những người hưởng lợi trực tiếp nhất đóng góp một phần chi phí.", "en": "However, the view that the cost of higher education should be borne entirely by taxpayers is not entirely convincing. University graduates typically earn significantly more than those without degrees, meaning they will contribute more to public finances through income tax. There is therefore a reasonable basis for requiring those who benefit most directly to contribute towards the cost.", "explain": "'bear the cost' = chịu gánh nặng chi phí. 'taxpayers' = người nộp thuế. 'reasonable basis' = cơ sở hợp lý."},
                    {"vi": "Từ quan điểm thực tiễn, một mô hình học phí hoãn nợ — trong đó sinh viên chỉ bắt đầu hoàn trả sau khi thu nhập của họ vượt ngưỡng nhất định — có thể giải quyết được cả mối lo ngại về bình đẳng lẫn tính bền vững tài chính. Mô hình này, được áp dụng thành công ở Úc và Vương quốc Anh, đảm bảo rằng gánh nặng tài chính không bao giờ trở nên không thể chịu đựng được đối với bất kỳ cá nhân nào.", "en": "From a practical standpoint, a deferred tuition model — in which students begin repayments only once their income exceeds a certain threshold — can address both concerns of equity and financial sustainability. This model, successfully implemented in Australia and the United Kingdom, ensures that the financial burden never becomes unbearable for any individual.", "explain": "'deferred' = hoãn lại. 'threshold' = ngưỡng. 'equity' = sự công bằng (formal, ≠ equality)."},
                    {"vi": "Tóm lại, mặc dù giáo dục đại học hoàn toàn miễn phí là một lý tưởng hấp dẫn, nhưng trong bối cảnh nguồn lực công hạn chế, một hệ thống phân chia chi phí công bằng và linh hoạt sẽ phục vụ xã hội tốt hơn. Điều quan trọng nhất là đảm bảo rằng không có sinh viên tài năng nào bị loại ra khỏi giáo dục đại học chỉ vì lý do tài chính.", "en": "In conclusion, while entirely free higher education is an appealing ideal, a fair and flexible cost-sharing system would serve society better given limited public resources. The most important objective is to ensure that no talented student is excluded from higher education purely on financial grounds.", "explain": "'on financial grounds' = vì lý do tài chính. 'appealing ideal' = lý tưởng hấp dẫn. 'cost-sharing' = phân chia chi phí."},
                ],
            },
            {
                "title": "Essay Task 2: Mở bài & Thân bài — Môi trường",
                "description": "Dịch từng phần của bài IELTS Task 2 về biến đổi khí hậu và trách nhiệm cá nhân vs. chính phủ.",
                "sentences": [
                    {"vi": "Biến đổi khí hậu là thách thức nghiêm trọng nhất mà nhân loại đang phải đối mặt trong thế kỷ này. Trong khi một số người cho rằng chính phủ phải chịu trách nhiệm chính trong việc giải quyết vấn đề này thông qua chính sách và quy định, những người khác lại khẳng định rằng hành động của mỗi cá nhân là yếu tố then chốt để tạo ra sự thay đổi thực sự. Quan điểm của tôi là cả hai đều không thể thiếu và phải hành động song song.", "en": "Climate change is the most formidable challenge facing humanity in this century. While some contend that governments bear the primary responsibility for tackling this issue through policy and regulation, others maintain that individual action is the pivotal factor in bringing about genuine change. My view is that both are indispensable and must act in concert.", "explain": "'formidable' = ghê gớm, đáng sợ. 'contend' = cho rằng, lập luận. 'in concert' = song song, phối hợp."},
                    {"vi": "Không thể phủ nhận rằng các chính phủ có đòn bẩy chính sách mà không một cá nhân nào có thể sở hữu. Các cơ chế như thuế carbon, quy định về tiêu chuẩn phát thải và đầu tư vào cơ sở hạ tầng năng lượng tái tạo có thể tạo ra thay đổi có hệ thống ở quy mô mà hành vi cá nhân không bao giờ có thể đạt được. Nếu không có sự can thiệp của nhà nước, thị trường sẽ không tự nhiên chuyển hướng sang các giải pháp thân thiện với môi trường.", "en": "It is undeniable that governments possess policy levers that no individual can wield. Mechanisms such as carbon taxes, emission standards regulations, and investment in renewable energy infrastructure can drive systemic change at a scale that individual behaviour can never achieve. Without state intervention, markets will not naturally transition towards environmentally friendly solutions.", "explain": "'levers' = đòn bẩy (ẩn dụ). 'wield' = sử dụng, thi hành. 'systemic change' = thay đổi có hệ thống."},
                    {"vi": "Đồng thời, hành động tập thể của hàng tỷ cá nhân có sức mạnh biến đổi không thể xem thường. Khi người tiêu dùng thay đổi thói quen — giảm tiêu thụ thịt, chọn phương tiện giao thông xanh, ủng hộ các thương hiệu có trách nhiệm với môi trường — họ gửi tín hiệu thị trường mạnh mẽ và góp phần xây dựng áp lực chính trị để buộc các chính phủ hành động quyết liệt hơn.", "en": "At the same time, the collective action of billions of individuals has a transformative power that cannot be underestimated. When consumers change their habits — reducing meat consumption, choosing green transportation, supporting environmentally responsible brands — they send powerful market signals and contribute to building political pressure that compels governments to take more decisive action.", "explain": "'collective action' = hành động tập thể. 'compel' = buộc phải. 'decisive' = quyết liệt, dứt khoát."},
                    {"vi": "Điều quan trọng cần nhận ra là trách nhiệm cá nhân và chính sách chính phủ không phải là hai lựa chọn đối lập mà là hai trụ cột bổ trợ cho nhau trong cuộc chiến chống biến đổi khí hậu. Các chính phủ cần tạo ra môi trường chính sách thuận lợi, trong khi cá nhân cần đưa ra những lựa chọn có trách nhiệm hơn trong phạm vi mà chính sách đó cho phép.", "en": "It is crucial to recognise that individual responsibility and government policy are not opposing alternatives but rather two complementary pillars in the fight against climate change. Governments need to create a favourable policy environment, while individuals need to make more responsible choices within the space that such policies enable.", "explain": "'complementary pillars' = các trụ cột bổ trợ. 'favourable policy environment' = môi trường chính sách thuận lợi."},
                    {"vi": "Để kết luận, cuộc khủng hoảng khí hậu đòi hỏi một phản ứng đồng bộ ở mọi cấp độ của xã hội. Trong khi chính phủ phải dẫn đầu thông qua các chính sách táo bạo và bắt buộc, mỗi cá nhân cũng phải nhận thức được rằng những lựa chọn hàng ngày của mình có hệ quả thực sự đối với thế giới mà các thế hệ tương lai sẽ thừa hưởng.", "en": "To conclude, the climate crisis demands a coordinated response at every level of society. While governments must take the lead through bold and mandatory policies, individuals must also recognise that their everyday choices have genuine consequences for the world that future generations will inherit.", "explain": "'coordinated response' = phản ứng đồng bộ. 'bold and mandatory' = táo bạo và bắt buộc. 'inherit' = thừa hưởng."},
                ],
            },
        ],
    },
]
