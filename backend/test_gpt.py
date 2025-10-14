import asyncio
import time
from app.agents.chat_agent import SimpleKetoCoachAgent

async def test_gpt():
    print("🔍 GPT 사용 여부 테스트 시작...")
    
    try:
        print("📱 ChatAgent 초기화 중...")
        agent = SimpleKetoCoachAgent()
        
        print("💬 테스트 메시지 전송 중...")
        start_time = time.time()
        
        result = await agent.process_message("안녕하세요")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ 응답 받음: {result['response'][:100]}...")
        print(f"⏱️ 응답 시간: {response_time:.2f}초")
        
        if response_time < 3:
            print("🚀 GPT 사용 중 (빠른 응답)")
        else:
            print("🐌 Gemini 사용 중 (느린 응답)")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_gpt())