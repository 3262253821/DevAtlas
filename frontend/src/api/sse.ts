const TOKEN_KEY = "dev_atlas_access_token";

export type SseEventHandler = (
  eventName: string,
  data: Record<string, unknown>,
) => void;

function parseEvent(block: string): {
  eventName: string;
  data: Record<string, unknown>;
} | null {
  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  const parsed = JSON.parse(dataLines.join("\n"));

  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("SSE data 格式不正确");
  }

  return {
    eventName,
    data: parsed as Record<string, unknown>,
  };
}

export async function consumeSse(
  path: string,
  payload: unknown,
  onEvent: SseEventHandler,
  signal: AbortSignal,
): Promise<void> {
  const token = localStorage.getItem(TOKEN_KEY);
  const baseUrl = import.meta.env.VITE_API_BASE_URL;

  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let message = `请求失败：${response.status}`;

    try {
      const errorData = JSON.parse(errorText) as {
        detail?: string;
      };

      if (errorData.detail) {
        message = errorData.detail;
      }
    } catch {
      // 后端返回的不是 JSON 时使用默认错误信息
    }

    throw new Error(message);
  }

  if (!response.body) {
    throw new Error("浏览器不支持流式响应");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, {
      stream: true,
    });

    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const parsed = parseEvent(block);

      if (parsed) {
        onEvent(parsed.eventName, parsed.data);
      }
    }
  }

  buffer += decoder.decode();

  if (buffer.trim()) {
    const parsed = parseEvent(buffer);

    if (parsed) {
      onEvent(parsed.eventName, parsed.data);
    }
  }
}
