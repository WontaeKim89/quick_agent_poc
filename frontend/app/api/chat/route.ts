type AssistantMessage = {
  id?: string;
  role: string;
  content?:
    | string
    | Array<
        | { type: 'text'; text: string }
        | { type: 'input_text'; content?: { text?: string } }
        | Record<string, unknown>
      >;
  parts?: Array<
    | { type: 'text'; text: string }
    | Record<string, unknown>
  >;
  metadata?: Record<string, unknown>;
};

const coerceContentToString = (content: AssistantMessage['content']): string => {
  // 문자열인 경우 그대로 반환
  if (typeof content === 'string') {
    return content;
  }

  // null이나 undefined인 경우 빈 문자열 반환
  if (content == null) {
    return '';
  }

  // 배열이 아닌 경우 빈 문자열 반환
  if (!Array.isArray(content)) {
    // 객체인 경우 JSON.stringify로 변환 시도 (디버깅용)
    if (typeof content === 'object') {
      console.warn('Unexpected content format (object):', content);
    }
    return '';
  }

  // 빈 배열인 경우 빈 문자열 반환
  if (content.length === 0) {
    return '';
  }

  // 배열의 각 블록을 처리
  return content
    .map((block) => {
      if (block == null) {
        return '';
      }

      // 블록이 문자열인 경우
      if (typeof block === 'string') {
        return block;
      }

      // 블록이 객체인 경우
      if (typeof block === 'object') {
        // type: 'text' 형식
        if ('type' in block && block.type === 'text' && 'text' in block) {
          const textValue = block.text;
          return typeof textValue === 'string' ? textValue : '';
        }

        // type: 'input_text' 형식
        if (
          'type' in block &&
          block.type === 'input_text' &&
          'content' in block &&
          block.content &&
          typeof block.content === 'object' &&
          'text' in block.content
        ) {
          const textValue = (block.content as { text?: unknown }).text;
          return typeof textValue === 'string' ? textValue : '';
        }

        // 다른 형식의 객체인 경우 (디버깅용)
        console.warn('Unexpected block format:', block);
      }

      return '';
    })
    .filter((chunk) => chunk.length > 0)
    .join('\n');
};

export async function POST(req: Request) {
  try {
    const body = await req.json();
    console.log('[ROUTE] 1. 받은 body:', JSON.stringify(body, null, 2));

    const { messages = [] } = body as {
      messages?: AssistantMessage[];
    };
    console.log('[ROUTE] 2. 추출한 messages:', messages);

    const normalizedMessages = messages
      .map((message) => {
        // parts 배열이 있으면 parts를 content로 변환, 없으면 기존 content 사용
        const contentSource = message.parts || message.content;
        const content = coerceContentToString(contentSource);
        return {
          role: message.role,
          content: content,
        };
      })
      .filter((message) => message.content.trim().length > 0);

    console.log('[ROUTE] 3. 정규화 후 normalizedMessages:', normalizedMessages);
    console.log('[ROUTE] 4. 백엔드로 전송할 데이터:', JSON.stringify({ messages: normalizedMessages }, null, 2));

    const backendResponse = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages: normalizedMessages }),
    });

    if (!backendResponse.ok) {
      const detail = await backendResponse.text().catch(() => '');
      return new Response(
        JSON.stringify({ error: 'Backend API 호출 실패', detail }),
        {
          status: backendResponse.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    return new Response(backendResponse.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Chat API Error:', error);
    return new Response(
      JSON.stringify({ error: '서버 오류가 발생했습니다.' }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}