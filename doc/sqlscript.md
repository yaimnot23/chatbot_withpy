### [Module A] 유저 관리 (User Management)

학생과 멘토를 구분하되, 공통 정보는 하나로 관리

* **Users (사용자 통합)**
  * `user_id` (PK): UUID 또는 Auto Increment
  * `email`, `password`, `name`, `nickname`
  * `role`: 구분값 ('STUDENT', 'MENTOR', 'ADMIN')
  * `created_at`: 가입일 (코호트 분석용 - 가입 시점을 기준으로 공통 특성 묶어서 패턴 분석 예를 들어 3월 가입자는 내신 성적으로 조회를, 11월 가입자는 정시 성적 조회를 많이함)
* **Student_Profile (학생 상세)**
  * `user_id` (FK, PK): Users 테이블과 1:1 관계
  * `target_university`: 목표 대학 (텍스트 혹은 FK)
  * `target_major`: 목표 학과
  * `region_preference`: 선호 지역 (서울, 수도권, 지방 등 - 필터링용)
* **Mentor_Profile (멘토 상세 - 대학생)**
  * `user_id` (FK, PK)
  * `univ_id` (FK): 재학 중인 대학
  * `dept_id` (FK): 재학 중인 학과
  * `student_card_img`: 학생증 인증 이미지 경로
  * `is_verified`: 인증 여부 (Boolean)
  * `introduction`: 멘토 한줄 소개
  * `average_rating` : 평점(선택사항)
  * `point` : 포인트(현금으로 출금)
  * `exp` : 경험치(레벨표시, 랭킹 구하기 등)
* Mentor_Availability (멘토 활동 가능 시간, 요일별, 시간별 자세하게 설정 가능)
  * `avail_id`: (PK)
  * `mentor_id` (FK):User.user_id
  * `day_of_week` : 요일. 0: 일요일, 1: 월요일 ... 6: 토요일
  * `block` : 0~11 (0: 00:00~02:00, 1: 02:00~04:00 ...)
* Favorite (멘토 즐겨찾기, 찜)
  * `favorite_id`(PK)
  * `student_id`(FK): User.user_id
  * `mentor_id`(FK): User.user_id

### [Module B] 문제 풀이 방(Quiz Room)

* Rooms (채팅 방)
  * `room_id` (PK)
  * `student_id`(FK): User.user_id
  * `mentor_id`(FK): User.user_id
  * `created_at` : 방 생성 날짜(시. 분. 초)
  * `is_public` : 공개 여부(공개 or 1대1)
  * `status`: 상태 ('PENDING', 'IN_PROGRESS’, 'COMPLETED')
  * `point` : 포인트
  * `subject_id` (FK): Subject.subject_id
  * `rating` : 만족도 (5점 만점)
* Subject (과목)
  * `subject_id` (PK)
  * `name` : 과목 명
* Messages (메시지)
  * `message_id` (PK)
  * `room_id` (FK): Rooms.room_id
  * `sender_id` (FK): User.user_id
  * `created_at` : 생성 날짜 (시. 분. 초)
  * `message_type` : ('TEXT', 'FILE’, 'IMAGE')
  * `content` : 메시지
  * `path` : 첨부 파일 경로
  * `is_read` : 읽음 여부
* Canvas : mongodb에 생성
  * `_id`(PK):ObjectId (자동 생성)
  * `x`: x좌표
  * `y`: y좌표
  * 나중에 데이터 추가

### [Module C] 대학 및 입시 데이터 (University Core Data)

작성자님이 크롤링하고 전처리한 데이터가 담길 곳입니다.  **분석의 기준점** .

* **Universities (대학 정보)**
  * `univ_id` (PK)
  * `univ_name`: 대학명 (예: 한국대학교)
  * `region`: 지역 (예: 서울)
  * `logo_url`: 로고 이미지
  * `site_url`: 입학처 홈페이지 링크
* **Departments (학과 정보)**
  * `dept_id` (PK)
  * `univ_id` (FK)
  * `dept_name`: 학과명 (예: 컴퓨터공학과)
  * `recruit_type`: 전형 (수시/정시/교과/종합) - *중요: 전형별로 커트라인이 다름*
  * `recruit_count`: 모집 인원
* **Admission_Stats (입시 결과 통계 - 분석용 핵심 테이블)**
  * *여기에 작년, 재작년 입시 결과 데이터를 넣습니다. Python이 이 데이터를 가져가서 학습/비교합니다.*
  * `stat_id` (PK)
  * `dept_id` (FK)
  * `year`: 입시 연도 (2024, 2025 등)
  * `avg_score`: 합격자 평균 점수 (내신 등급 or 수능 환산점수)
  * `cut_line_70`: 70% 컷 점수
  * `competition_rate`: 경쟁률

### [Module D] 학생 성적 및 AI 분석 (Input & Output)

사용자의 입력값과 Python AI 모델이 뱉어낸 결과값을 저장합니다.

* **Student_Scores (학생 성적 입력)**
  * `score_id` (PK)
  * `user_id` (FK)
  * `exam_type`: 시험 종류 (1학년1학기_중간, 6월_모의고사, 수능 등)
  * `korean_score`: 국어 점수 (표준점수 or 등급)
  * `math_score`: 수학 점수
  * `english_score`: 영어 점수
  * `history_score`: 한국사
  * `inquiry_score_1`: 탐구1
  * `inquiry_score_2`: 탐구2
  * *과목을 컬럼으로 박을지, 행으로 뺄지는 선택*
* **AI_Analysis_Results (AI 분석 결과 - 캐싱)**
  * *Python 서버에서 분석한 결과를 매번 다시 계산하지 않고 저장해둡니다.*
  * `result_id` (PK)
  * `user_id` (FK)
  * `dept_id` (FK): 추천된 학과
  * `admission_probability`: 합격 확률 (예: 85.5%)
  * `score_gap`: 내 점수와 커트라인의 차이 (예: +2.1점)
  * `analyzed_at`: 분석 시각

### [Module E] 부가 기능 (Features)

팀원들이 구현할 기능들입니다.

* **Mock_Applications (모의 지원 현황판)**
  * `application_id` (PK)
  * `user_id` (FK)
  * `dept_id` (FK): 지원한 학과
  * `priority`: 지망 순위 (1지망, 2지망...)
  * `created_at`: 지원 시각
  * *이 테이블을 `group by dept_id` 하면 실시간 우리 서비스 내부 경쟁률이 나옵니다.*
* **Mentoring_Requests (멘토링 매칭)**
  * `request_id` (PK)
  * `student_id` (FK): 요청한 학생
  * `mentor_id` (FK): 요청받은 멘토
  * `status`: 상태 ('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED')
  * `message`: 신청 메시지
* **Notifications (알림, 푸시 기능)**
  * `notification_id` (PK):
  * `user_id` (FK): User.user_id
  * `content` 알림 내용

### [Module F] 커뮤니티 (Community)

Spring Boot의 **기본 CRUD(생성, 조회, 수정, 삭제)**를 익히고 구현할 파트입니다.

**Posts (자유게시판)**

* `post_id` (PK)
* `user_id` (FK): 게시글 작성자
* `title`: 게시글 제목
* `content`: 게시글 본문 (TEXT 타입)
* `view_count`: 조회수 (인기글 선정 기준이 됨)
* `created_at`: 작성 시각
* `updated_at`: 수정 시각
* *설명: 가장 기본적인 게시판 테이블입니다. 작성자(`Users`)와 1:N 관계를 가집니다.*

**Comments (댓글)**

* `comment_id` (PK)
* `post_id` (FK): 댓글이 달린 원본 게시글
* `user_id` (FK): 댓글 작성자
* `content`: 댓글 내용
* `created_at`: 작성 시각
* *설명: 게시글 하나에 여러 댓글이 달리는 1:N 구조입니다. 게시글이 삭제되면 댓글도 함께 삭제되도록(Cascade) 로직*

`Universities`와 `Admission_Stats` 테이블은  **공공데이터나 대학 어디가 사이트에서 크롤링**해서 DB에 미리 밀어넣어야 하는(Seeding) 데이터

`Mock_Applications` 테이블에 데이터가 쌓이면, 이를 바탕으로 **"우리 서비스 유저들의 트렌드 분석"**

**AI 모델의 I/O :**

* 입력: `Student_Scores` + `Admission_Stats`
* 출력: `AI_Analysis_Results`
