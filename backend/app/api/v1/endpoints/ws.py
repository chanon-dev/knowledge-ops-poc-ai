import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_jwt
from app.services.llm.ollama_client import OllamaClient
from app.services.llm.prompt_templates import build_rag_prompt
from app.services.rag.retriever import RAGRetriever

router = APIRouter()


@router.websocket("/chat/{dept_id}")
async def websocket_chat(websocket: WebSocket, dept_id: UUID):
    # Validate token from query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = decode_jwt(token)
        tenant_id = payload.get("tenant_id")
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            query_text = message.get("text", "")

            if not query_text:
                await websocket.send_json({"type": "error", "message": "Empty query"})
                continue

            # Signal start
            await websocket.send_json({"type": "start"})

            try:
                # RAG retrieval
                retriever = RAGRetriever()
                results = retriever.retrieve(
                    query=query_text,
                    tenant_id=str(tenant_id),
                    department_id=str(dept_id),
                )
                context = retriever.build_context(results)

                sources = [
                    {
                        "title": r.get("title", ""),
                        "chunk": r.get("content", "")[:200],
                        "score": r.get("score", 0),
                    }
                    for r in results
                ]

                # Stream LLM response
                messages = build_rag_prompt(
                    query=query_text,
                    context=context,
                    system_prompt="You are a helpful AI assistant.",
                )

                client = OllamaClient()
                stream = await client.chat(messages, stream=True)

                full_response = ""
                async for token in stream:
                    full_response += token
                    await websocket.send_json({"type": "token", "content": token})

                await client.close()

                # Signal end
                await websocket.send_json(
                    {
                        "type": "end",
                        "sources": sources,
                        "full_response": full_response,
                    }
                )

            except Exception as e:
                await websocket.send_json(
                    {"type": "error", "message": f"Error: {e}"}
                )

    except WebSocketDisconnect:
        pass
