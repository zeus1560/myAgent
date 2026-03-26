import ollama
import sys
import json
import re

from tools import search_web, search_namuwiki, read_file, append_file, write_file, modify_file
from prompts import system_prompt

JSON_PATTERN = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)

TOOL_FUNCTIONS = {
    "read_file": lambda args: read_file(args.get("filepath", "")),
    "write_file": lambda args: write_file(args.get("filepath", ""), args.get("content", "")),
    "append_file": lambda args: append_file(args.get("filepath", ""), args.get("content", "")),
    "modify_file": lambda args: modify_file(args.get("filepath", ""), args.get("old_str", ""), args.get("new_str", "")),
    "search_web": lambda args: search_web(args.get("query", "")),
    "search_namuwiki": lambda args: search_namuwiki(args.get("keyword", ""))
}

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
        max_steps = 5
        step_count = 0
        while step_count < max_steps:
            step_count += 1
            try:
                print("🤖 Qwen: ", end="", flush=True)
                
                response = ollama.chat(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    options={"num_ctx": 8192, "temperature": 0.3}
                )
                
                assistant_response = ""
                try:
                    for chunk in response:
                        if 'message' in chunk and 'content' in chunk['message']:
                            content = chunk['message']['content']
                            print(content, end="", flush=True)
                            assistant_response += content
                        
                        # Ollama 스트림의 마지막 chunk에서 성능 통계 추출
                        if chunk.get('done'):
                            eval_count = chunk.get('eval_count', 0)
                            eval_duration_ns = chunk.get('eval_duration', 0)
                            if eval_duration_ns > 0:
                                tps = eval_count / (eval_duration_ns / 1e9)
                                print(f"  [⚡ 생성 속도: {tps:.1f} Tokens/s]", end="")
                except Exception as stream_err:
                    print(f"\n[⚠️ 출력 중 연결 오류: 문맥이 너무 길어 로컬 모델이 크래시(메모리 초과)되었을 가능성이 큽니다.]")
                    
                print("\n")
                
                messages.append({'role': 'assistant', 'content': assistant_response})
                
                # 대화 기록 슬라이딩 윈도우 (시스템 프롬프트 유지하고 최근 30개만 유지)
                if len(messages) > 31:
                    messages = [messages[0]] + messages[-30:]
                    
                # JSON 도구 호출 파싱 (연속 호출 지원)
                matches = list(JSON_PATTERN.finditer(assistant_response))
                if matches:
                    tool_results_combined = []
                    for match in matches:
                        try:
                            tool_call = json.loads(match.group(1))
                            action = tool_call.get("action")
                            
                            # 출력용 정보
                            filepath = tool_call.get("filepath", "")
                            query = tool_call.get("query", "")
                            keyword = tool_call.get("keyword", "")
                            target_info = filepath or query or keyword
                            print(f"🛠️  시스템: '{action}' 도구 실행 중 ({target_info})...")
                            
                            # 도구 디스패치
                            if action in TOOL_FUNCTIONS:
                                tool_result = TOOL_FUNCTIONS[action](tool_call)
                            else:
                                tool_result = f"알 수 없는 액션: {action}"
                                
                            print(f"📄 도구 실행 결과:\n{tool_result}\n")
                            tool_results_combined.append(f"[{action} 실행 결과]\n{tool_result}")
                        except json.JSONDecodeError:
                            error_msg = "JSON 파싱 오류: 올바른 JSON 형식이 아닙니다."
                            print(f"⚠️ 시스템: {error_msg}\n")
                            tool_results_combined.append(f"[오류]\n{error_msg}")
                            
                    if step_count >= max_steps:
                        timeout_msg = "에이전트가 도구를 너무 많이 연속 호출하여 작업을 강제 종료합니다."
                        print(f"⚠️ 시스템: {timeout_msg}\n")
                        messages.append({'role': 'system', 'content': timeout_msg})
                        break
                        
                    # 모델에게 도구 결과 전달
                    combined_result_text = "\n\n".join(tool_results_combined)
                    messages.append({
                        'role': 'user',
                        'content': f"도구 실행 결과들:\n{combined_result_text}\n\n결과를 확인했습니다. 사용자의 추가 목표가 남아있다면 다음 도구를 사용하고, 모든 목표를 달성했다면 짧게 안내하고 응답을 종료하세요."
                    })
                    continue # 모델의 다음 응답 받기
                
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
