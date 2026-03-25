import ollama
import sys

def main():
    print("🤖 터미널 Qwen 챗봇에 오신 것을 환영합니다!")
    print("종료하려면 'quit', 'exit'를 입력하시거나 Ctrl+C를 누르세요.\n")
    
    # 사용할 모델 (시스템에 다운로드된 모델로 변경 가능)
    model_name = 'qwen2.5-coder:7b'
    
    messages = []
    
    while True:
        try:
            user_input = input("👤 당신: ")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 채팅을 종료합니다.")
            break
            
        if user_input.lower() in ['quit', 'exit']:
            print("👋 채팅을 종료합니다.")
            break
            
        if not user_input.strip():
            continue
            
        messages.append({'role': 'user', 'content': user_input})
        
        try:
            print("🤖 Qwen: ", end="", flush=True)
            
            # 스트리밍 방식 챗 요청
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
            
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"\n❌ 오류: '{model_name}' 모델을 찾을 수 없습니다.")
                print(f"터미널에서 'ollama run {model_name}' 명령어를 통해 모델을 다운로드해주세요.\n")
                messages.pop()
            else:
                print(f"\n❌ Ollama 응답 오류: {e}\n")
                messages.pop()
        except Exception as e:
            print(f"\n❌ 서버 연결 오류: Ollama 앱이 실행 중인지 확인해주세요. (오류: {e})\n")
            messages.pop()

if __name__ == "__main__":
    main()
