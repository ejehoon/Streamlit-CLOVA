import base64
import json
import http.client
from private_key import api_credentials

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

# 인스턴스 생성
completion_executor = CompletionExecutor(
    host=api_credentials['host'],
    client_id=api_credentials['client_id'],
    client_secret=api_credentials['client_secret']
)
