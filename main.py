import ollama
import sys
import json
import re

# --- 파일 조작 함수 정의 ---
def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"읽기 오류: {e}"

def write_file(filepath, content):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"'{filepath}' 파일이 성공적으로 작성되었습니다."
    except Exception as e:
        return f"쓰기 오류: {e}"

def modify_file(filepath, old_str, new_str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if old_str not in content:
            return f"수정 오류: '{old_str}'을(를) 파일에서 찾을 수 없습니다."
        content = content.replace(old_str, new_str)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"'{filepath}' 파일이 성공적으로 수정되었습니다."
    except Exception as e:
        return f"수정 오류: {e}"

# --- 시스템 프롬프트 ---
system_prompt = """당신은 파일 시스템에 접근하여 파일을 읽고, 쓰고, 수정할 수 있는 능력을 갖춘 AI 에이전트입니다.
사용자의 요청을 해결하기 위해 파일 조작이 필요한 경우, 아래의 JSON 포맷을 코드 블록으로 출력하여 도구를 사용할 수 있습니다.

```json
{
  "action": "read_file" | "write_file" | "modify_file",
  "filepath": "대상 파일 경로",
  "content": "작성할 내용 (write_file 전용)",
  "old_str": "찾을 기존 문자열 (modify_file 전용)",
  "new_str": "바꿀 새로운 문자열 (modify_file 전용)"
}
```

🚨 도구 사용 규칙:
1. 'action'은 반드시 "read_file", "write_file", "modify_file" 3가지 중 하나만 사용해야 합니다. (delete_file, execute_file 등은 절대 금지)
2. 'modify_file' 사용 시, 'old_str'은 파일 내에 존재하는 내용과 띄어쓰기/줄바꿈까지 100% 동일해야 성공합니다.

예시 1 (파일 읽기):
```json
{
  "action": "read_file",
  "filepath": "example.txt"
}
```

예시 2 (새 파일 작성):
```json
{
  "action": "write_file",
  "filepath": "example.txt",
  "content": "이것은 새로운 내용입니다."
}
```

예시 3 (기존 파일 일부분 수정):
```json
{
  "action": "modify_file",
  "filepath": "example.txt",
  "old_str": "이것은 새로운 내용입니다.",
  "new_str": "이것은 수정된 내용입니다."
}
```

당신이 도구 사용 JSON을 출력하면, 시스템이 이를 실행한 결과를 다시 제공할 것입니다.
결과를 확인한 후, 목적을 달성했다면 사용자에게 짧게 안내하고 응답을 종료하세요.
절대로 사용자의 명시적인 지시 없이 혼자서 임의로 추가 도구 작업을 계속 진행하지 마세요.
도구를 사용할 필요가 없다면 JSON 없이 자연어로 평범하게 답변하면 됩니다.
"""

def main():
    print("🤖 터미널 Qwen 에이전트에 오신 것을 환영합니다!")
    print("종료하려면 'quit', 'exit'를 입력하시거나 Ctrl+C를 누르세요.\n")
    
    # 사용할 모델
    model_name = 'qwen2.5-coder:7b'
    
    # 시스템 프롬프트 적용
    messages = [{'role': 'system', 'content': system_prompt}]
    
    while True:
        try:
            user_input = input("👤 당신: ")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 에이전트를 종료합니다.")
            break
            
        if user_input.lower() in ['quit', 'exit']:
            print("👋 에이전트를 종료합니다.")
            break
            
        if not user_input.strip():
            continue
            
        messages.append({'role': 'user', 'content': user_input})
        
        # 모델이 도구를 호출할 수 있으므로 while 루프 사용 (ReAct 패턴)
        while True:
            try:
                print("🤖 Qwen: ", end="", flush=True)
                
                response = ollama.chat(
                    model=model_name,
                    messages=messages,
                    stream=True,
                )
                
                assistant_response = ""
                for chunk in response:
                    content = chunk['message']['content']
                    print(content, end="", flush=True)
                    assistant_response += content
                    
                print("\n")
                
                messages.append({'role': 'assistant', 'content': assistant_response})
                
                # JSON 도구 호출 파싱
                match = re.search(r'```json\s*(\{.*?\})\s*```', assistant_response, re.DOTALL)
                if match:
                    try:
                        tool_call = json.loads(match.group(1))
                        action = tool_call.get("action")
                        filepath = tool_call.get("filepath")
                        
                        tool_result = ""
                        print(f"🛠️  시스템: '{action}' 도구 실행 중 ({filepath})...")
                        
                        if action == "read_file":
                            tool_result = read_file(filepath)
                        elif action == "write_file":
                            content = tool_call.get("content", "")
                            tool_result = write_file(filepath, content)
                        elif action == "modify_file":
                            old_str = tool_call.get("old_str", "")
                            new_str = tool_call.get("new_str", "")
                            tool_result = modify_file(filepath, old_str, new_str)
                        else:
                            tool_result = f"알 수 없는 액션: {action}"
                            
                        print(f"📄 도구 실행 결과:\n{tool_result}\n")
                        
                        # 모델에게 도구 결과 전달
                        messages.append({
                            'role': 'user',
                            'content': f"도구 실행 결과:\n{tool_result}\n\n사용자에게 결과를 간략히 보고하고 대화를 마무리지으세요. 혼자서 임의로 추가 도구를 사용하지 마세요."
                        })
                        continue # 모델의 다음 응답 받기
                        
                    except json.JSONDecodeError:
                        error_msg = "JSON 파싱 오류: 올바른 JSON 형식이 아닙니다."
                        print(f"⚠️ 시스템: {error_msg}\n")
                        messages.append({'role': 'user', 'content': error_msg})
                        continue
                
                # 도구 호출이 없으면 내부 while 루프 탈출
                break
                
            except ollama.ResponseError as e:
                if e.status_code == 404:
                    print(f"\n❌ 오류: '{model_name}' 모델을 찾을 수 없습니다.")
                    if messages[-1]['role'] == 'user':
                        messages.pop()
                else:
                    print(f"\n❌ Ollama 응답 오류: {e}\n")
                    if messages[-1]['role'] == 'user':
                        messages.pop()
                break # 에러 시 내부 루프 탈출
            except Exception as e:
                print(f"\n❌ 서버 연결 오류: {e}\n")
                if messages[-1]['role'] == 'user':
                    messages.pop()
                break # 에러 시 내부 루프 탈출

if __name__ == "__main__":
    main()
