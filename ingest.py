import pandas as pd
import os
import shutil
import time
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# 1. 환경설정 로드 (.env 파일의 GOOGLE_API_KEY 로드)
load_dotenv()

def ingest_data():
    # 2. 기존 DB 삭제 (깨끗하게 새로 만들기 위해)
    db_path = "./db"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        print(f"🧹 기존 DB 폴더('{db_path}')를 삭제했습니다.")

    # 3. 엑셀 파일 설정
    excel_file_path = "data/univer_data.xlsx"
    if not os.path.exists(excel_file_path):
        print(f"❌ '{excel_file_path}' 파일이 없습니다. 경로를 확인해주세요.")
        return

    documents = []
    print(f"📂 '{excel_file_path}' 파일을 읽는 중...")

    try:
        # 모든 시트 읽기
        xls = pd.ExcelFile(excel_file_path)
        
        for sheet_name in xls.sheet_names:
            print(f"📄 '{sheet_name}' 시트 처리 중...")
            # header=4는 사용자 이전 코드 기준 (데이터 시작 위치에 따라 조정 가능)
            df = pd.read_excel(xls, sheet_name=sheet_name, header=4)
            
            # NaN 데이터를 빈 문자열로 처리
            df = df.fillna("")

            for _, row in df.iterrows():
                # '대학교'와 '전공' 컬럼 찾기 (유연하게 대응)
                univ = str(row.get('대학교', row.get('대학', ''))).strip()
                major = str(row.get('전공', row.get('모집단위(전공)', row.get('모집단위', '')))).strip()
                
                if not univ or not major:
                    continue

                category = str(row.get('계열', ''))
                region = f"{row.get('시도','')} {row.get('시군','')}".strip()
                target_score = str(row.get('적정점수', '정보없음'))
                est_score = str(row.get('예상점수', '정보없음'))

                # 검색 시 사용될 텍스트 구성
                content = (
                    f"[{sheet_name}] {univ} {major} ({category}) 입시 정보. "
                    f"지역: {region}, 모집군: {row.get('모집군','')}, 정원: {row.get('정원','')}명. "
                    f"적정 점수: {target_score}점, 예상 점수: {est_score}점. "
                    f"반영비율: 국어 {row.get('국어구성비','')}, 수학 {row.get('수학구성비','')}, "
                    f"영어 {row.get('영어구성비','')}, 탐구 {row.get('탐구구성비','')}."
                )
                
                # 메타데이터 저장 (필터링 등에 활용 가능)
                metadata = {
                    "source": f"{univ} {major}",
                    "univ": univ,
                    "major": major,
                    "sheet": sheet_name
                }
                documents.append(Document(page_content=content, metadata=metadata))

        print(f"✅ 총 {len(documents)}개의 문서를 생성했습니다.")

        # 4. 벡터 DB 저장 (Batch Processing)
        print("💾 벡터 DB(Chroma)에 저장 중... (Rate Limit 방지를 위해 천천히 진행합니다)")
        
        embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
        
        vectorstore = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )

        batch_size = 50  # 조금 더 큰 단위로 처리
        for i in tqdm(range(0, len(documents), batch_size), desc="저장 진행률"):
            batch = documents[i : i + batch_size]
            
            # Rate Limit(429 에러) 발생 시 재시도 로직
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    vectorstore.add_documents(batch)
                    break 
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        wait_time = (attempt + 1) * 10 # 실패할수록 더 오래 대기 (10초, 20초...)
                        print(f"\n⚠️ Rate Limit 도달! {wait_time}초 후 재시도합니다... ({attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        raise e
            
            # 기본 휴식 시간 (API 안정성을 위해)
            time.sleep(1)

        print(f"🎉 모든 데이터가 '{db_path}' 폴더에 성공적으로 저장되었습니다!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    ingest_data()
