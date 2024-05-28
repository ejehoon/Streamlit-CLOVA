import os
from dotenv import load_dotenv
import streamlit as st
from sliding_window_executor import sliding_window_executor
from completion_executor import completion_executor

# .env 파일 로드
load_dotenv()

# 슬라이딩 윈도우 최대 토큰 수 설정
MAX_TOKENS_SLIDING = 3900

# CompletionExecutor 파라미터
COMPLETION_PARAMS = {
    "maxTokens": 256,
    "temperature": 0.5,
    "topK": 0,
    "topP": 0.8,
    "repeatPenalty": 5.0,
    "stopBefore": [],
    "includeAiFilters": True,
    "seed": 0
}

def main():
    st.set_page_config(page_title="CLOVA", page_icon="🍀")
    st.title("🍀 CLOVA")

    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": "- HyperCLOVA X는 네이버 클라우드의 하이퍼스케일 AI입니다."},
        ]

    # 이전 대화기록 출력
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.chat_message("user").write(f'{msg["content"]}')
        elif msg["role"] == "assistant" and "content" in msg:
            st.chat_message("assistant").write(f'{msg["content"]}')

    # 사용자 입력 처리
    if user_input := st.chat_input("Enter your message:"):
        st.chat_message("user").write(f'{user_input}')  # 사용자 입력을 바로 출력
        with st.spinner("Thinking..."):
            # 사용자 입력 추가
            st.session_state["messages"].append({"role": "user", "content": user_input})

            request_data = {
                "messages": st.session_state["messages"],
                "maxTokens": MAX_TOKENS_SLIDING  # 슬라이딩 윈도우에서 사용할 최대 토큰 수
            }

            # Step 1: 슬라이딩 윈도우 적용
            adjusted_messages = sliding_window_executor.execute(request_data)
            print("Adjusted Messages:", adjusted_messages)  # 조정된 메시지 출력

            # Step 2: Chat Completions API 요청
            completion_request_data = {
                "messages": adjusted_messages,
                **COMPLETION_PARAMS  # 새로운 CompletionExecutor 파라미터 사용
            }

            # Step 3: Chat Completions API 응답받기
            response_message = completion_executor.execute(completion_request_data)
            print("USER Input:", user_input)
            print("CLOVA Response:", response_message,"\n")

            # 최신 대화 상태로 업데이트
            if response_message and response_message != 'Error':
                st.session_state["messages"].append({"role": "assistant", "content": response_message})
            else:
                st.session_state["messages"].append({"role": "assistant", "content": "Error: No response from AI"})

            st.chat_message("assistant").write(f'{st.session_state["messages"][-1]["content"]}')  # 최신 응답만 출력

if __name__ == "__main__":
    main()
