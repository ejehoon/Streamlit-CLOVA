import streamlit as st
import base64
import json
import http.client

# SlidingWindowExecutor 클래스 정의
class SlidingWindowExecutor:
    def __init__(self, host, client_id, client_secret, access_token=None):
        self._host = host
        self._client_id = client_id
        self._client_secret = client_secret
        self._encoded_secret = base64.b64encode('{}:{}'.format(self._client_id, self._client_secret).encode('utf-8')).decode('utf-8')
        self._access_token = access_token

    def _refresh_access_token(self):
        headers = {
            'Authorization': 'Basic {}'.format(self._encoded_secret)
        }

        conn = http.client.HTTPSConnection(self._host)
        conn.request('GET', '/v1/auth/token?existingToken=true', headers=headers)
        response = conn.getresponse()
        body = response.read().decode()
        conn.close()

        token_info = json.loads(body)
        self._access_token = token_info['result']['accessToken']

    def _send_request(self, completion_request):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer {}'.format(self._access_token)
        }

        conn = http.client.HTTPSConnection(self._host)
        conn.request('POST', '/v1/api-tools/sliding/chat-messages/HCX-003', json.dumps(completion_request), headers)
        response = conn.getresponse()
        result = json.loads(response.read().decode(encoding='utf-8'))
        conn.close()
        return result

    def execute(self, completion_request):
        if self._access_token is None:
            self._refresh_access_token()

        res = self._send_request(completion_request)
        if res['status']['code'] == '40103':
            self._access_token = None
            return self.execute(completion_request)
        elif res['status']['code'] == '20000':
            return res['result']['messages']
        else:
            return 'Error'


# CompletionExecutor 클래스 정의
class CompletionExecutor:
    def __init__(self, host, client_id, client_secret, access_token=None):
        self._host = host
        self._client_id = client_id
        self._client_secret = client_secret
        self._encoded_secret = base64.b64encode('{}:{}'.format(self._client_id, self._client_secret).encode('utf-8')).decode('utf-8')
        self._access_token = access_token

    def _refresh_access_token(self):
        headers = {
            'Authorization': 'Basic {}'.format(self._encoded_secret)
        }

        conn = http.client.HTTPSConnection(self._host)
        conn.request('GET', '/v1/auth/token?existingToken=true', headers=headers)
        response = conn.getresponse()
        body = response.read().decode()
        conn.close()

        token_info = json.loads(body)
        self._access_token = token_info['result']['accessToken']

    def _send_request(self, completion_request):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/event-stream',
            'Authorization': 'Bearer {}'.format(self._access_token)
        }

        conn = http.client.HTTPSConnection(self._host)
        conn.request('POST', '/v1/chat-completions/HCX-003', json.dumps(completion_request), headers)
        response = conn.getresponse()
        response_body = response.read().decode('utf-8')

        if response_body:
            events = response_body.strip().split("\n\n")
            for event in events:
                if "event:result" in event:
                    data_json = event.split("\n")[-1][len("data:"):].strip()
                    try:
                        data = json.loads(data_json)
                        result = {
                            'status': {'code': '20000'}, 
                            'result': {'message': data['message']['content']}
                        }
                        break
                    except json.JSONDecodeError as e:
                        print("JSON parsing error:", e)
                        result = {'status': {'code': 'error'}, 'result': {'message': 'JSON parsing error'}}
                else:
                    result = {"error": "No valid event found in response"}
        else:
            result = {"error" : "Empty response body"}
        
        conn.close()
        return result

    def execute(self, completion_request):
        if self._access_token is None:
            self._refresh_access_token()

        res = self._send_request(completion_request)
        if res['status']['code'] == '40103':
            self._access_token = None
            return self.execute(completion_request)
        elif res['status']['code'] == '20000':
            return res['result']['message']
        else:
            return 'Error'


# Streamlit 애플리케이션
st.set_page_config(page_title="CLOVA", page_icon="🤔")
st.title("😎 CLOVA")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "- HyperCLOVA X는 네이버 클라우드의 하이퍼스케일 AI입니다."},
    ]

# 사이드바 설정
with st.sidebar:
    st.sidebar.write("Settings are not available for this application.")

# 이전 대화기록 출력
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(f'{msg["content"]}')
    elif msg["role"] == "assistant" and "content" in msg:
        st.chat_message("assistant").write(f'{msg["content"]}')

# API 호출 함수
def call_clova_api(user_input):
    sliding_window_executor = SlidingWindowExecutor(
        host='api-hyperclova.navercorp.com',
        client_id='9c83b54c2d444125aa8e139d16ecb540',
        client_secret='a3f09e526b432bf47397682d05b076b3c5a41b4f1d639f7741c34837091e6472'
    )

    completion_executor = CompletionExecutor(
        host='api-hyperclova.navercorp.com',
        client_id='9c83b54c2d444125aa8e139d16ecb540',
        client_secret='a3f09e526b432bf47397682d05b076b3c5a41b4f1d639f7741c34837091e6472'
    )

    # 사용자 입력 추가
    st.session_state["messages"].append({"role": "user", "content": user_input})

    request_data = {
        "messages": st.session_state["messages"],
        "maxTokens": 3900
    }

    # Step 1: Adjust the messages using Sliding Window API
    adjusted_messages = sliding_window_executor.execute(request_data)
    print("Adjusted Messages:", adjusted_messages)  # Adjusted messages 출력

    # Step 2: Create the request data for Chat Completions API
    completion_request_data = {
        "messages": adjusted_messages,
        "maxTokens": 2000
    }

    # Step 3: Get the response from Chat Completions API
    response_message = completion_executor.execute(completion_request_data)
    print("AI:", response_message)

    # Update messages with the latest conversation turns
    st.session_state["messages"] = adjusted_messages
    st.session_state["messages"].append({"role": "assistant", "content": response_message})

    # 최신 대화 업데이트
    if response_message != 'Error':
        st.chat_message("assistant").write(f'{response_message}')

# 사용자 입력 처리
if user_input := st.chat_input("Enter your message:"):
    st.chat_message("user").write(f'{user_input}')  # 사용자 입력을 바로 출력
    message_placeholder = st.empty()
    with st.spinner("Thinking..."):
        call_clova_api(user_input)

