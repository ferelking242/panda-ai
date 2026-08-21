#!/usr/bin/env python3
"""Comprehensive test suite — validates all core modules without a running server."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.openai_routes import (
    _parse_tool_calls, _build_tool_system_prompt, _extract_json_object,
    _build_prompt, _extract_image_urls, _extract_file_attachments,
    _responses_input_to_messages, _responses_tools_to_chat_tools,
    _CHATGPT_MODELS, _CLAUDE_MODELS, _GEMINI_MODELS, _DEEPSEEK_MODELS,
    _GROK_MODELS, _MISTRAL_MODELS, _QWEN_MODELS, _KIMI_MODELS,
    set_fallback_chain,
)
from src.api.openai_schemas import (
    ToolDefinition, FunctionDefinition, ChatMessage, ChatCompletionRequest,
    ResponsesRequest, ResponseObject,
)
from src.api.schemas import ChatRequest, ChatResponse, StatusResponse
from src.config import Config
from src.cache import get_cache, init_cache


# ── Test 1: JSON extraction ────────────────────────────────────
def test_json_extraction():
    print("=== Test 1: JSON extraction ===")
    text1 = 'Here:\n```json\n{"tool_calls": [{"name": "get_weather", "arguments": {"city": "Tokyo"}}]}\n```\nDone.'
    assert _extract_json_object(text1, "tool_calls") is not None
    print("  PASS: code block extraction")

    text2 = 'Call tools: {"tool_calls": [{"name": "foo", "arguments": {}}]}'
    assert _extract_json_object(text2, "tool_calls") is not None
    print("  PASS: inline extraction")

    text3 = 'No tools here.'
    assert _extract_json_object(text3, "tool_calls") is None
    print("  PASS: no false positive")

    # Nested JSON
    text4 = '```json\n{"tool_calls": [{"name": "x", "arguments": {"nested": {"a": [1,2,3]}}}]}\n```'
    assert _extract_json_object(text4, "tool_calls") is not None
    print("  PASS: nested JSON extraction")


# ── Test 2: Tool call parsing ──────────────────────────────────
def test_tool_call_parsing():
    print("\n=== Test 2: Tool call parsing ===")
    tools = [
        ToolDefinition(type='function', function=FunctionDefinition(
            name='get_weather', description='Get weather',
            parameters={'type': 'object', 'properties': {'city': {'type': 'string'}}}
        ))
    ]

    resp = '```json\n{"tool_calls": [{"name": "get_weather", "arguments": {"city": "Tokyo"}}]}\n```'
    result = _parse_tool_calls(resp, tools)
    assert result is not None and len(result) == 1
    assert result[0].function.name == "get_weather"
    assert "Tokyo" in result[0].function.arguments
    print(f"  PASS: single call parsed")

    # Unknown tool filtered
    resp2 = '```json\n{"tool_calls": [{"name": "unknown_fn", "arguments": {}}]}\n```'
    result2 = _parse_tool_calls(resp2, tools)
    assert result2 is None or len(result2) == 0
    print("  PASS: unknown tool filtered")

    # Multiple tools
    tools2 = tools + [ToolDefinition(type='function', function=FunctionDefinition(
        name='get_time', description='Get time', parameters={'type': 'object', 'properties': {}}
    ))]
    resp3 = '```json\n{"tool_calls": [{"name": "get_weather", "arguments": {"city": "Paris"}}, {"name": "get_time", "arguments": {}}]}\n```'
    result3 = _parse_tool_calls(resp3, tools2)
    assert result3 is not None and len(result3) == 2
    print("  PASS: multiple calls parsed")

    # No tool calls in response
    resp4 = 'The weather in Tokyo is sunny.'
    result4 = _parse_tool_calls(resp4, tools)
    assert result4 is None
    print("  PASS: no false positive on plain text")


# ── Test 3: Prompt builder ─────────────────────────────────────
def test_prompt_builder():
    print("\n=== Test 3: Prompt builder ===")
    assert _build_prompt([ChatMessage(role='user', content='Hello')]) == 'Hello'
    print("  PASS: simple user message")

    p2 = _build_prompt([
        ChatMessage(role='system', content='You are helpful'),
        ChatMessage(role='user', content='Hi')
    ])
    assert 'You are helpful' in p2 and 'Hi' in p2
    print("  PASS: system + user")

    p3 = _build_prompt([
        ChatMessage(role='user', content='What is 2+2?'),
        ChatMessage(role='assistant', content='4'),
        ChatMessage(role='user', content='And 3+3?')
    ])
    assert '2+2' in p3 and '3+3' in p3
    print("  PASS: multi-turn")


# ── Test 4: Image extraction ───────────────────────────────────
def test_image_extraction():
    print("\n=== Test 4: Image extraction ===")
    content = [
        {"type": "text", "text": "Look"},
        {"type": "image_url", "image_url": {"url": "https://example.com/img.png"}}
    ]
    urls = _extract_image_urls(content)
    assert urls == ["https://example.com/img.png"]
    print("  PASS: image URL extracted")

    # No images
    assert _extract_image_urls("just a string") == []
    assert _extract_image_urls([{"type": "text", "text": "hi"}]) == []
    print("  PASS: no false positives")


# ── Test 5: File attachment extraction ─────────────────────────
def test_file_attachments():
    print("\n=== Test 5: File attachments ===")
    content = [
        {"type": "file", "file": {"filename": "test.pdf", "data": "base64data==", "mime_type": "application/pdf"}}
    ]
    files = _extract_file_attachments(content)
    assert len(files) == 1 and files[0]["filename"] == "test.pdf"
    print("  PASS: file attachment extracted")

    # Data URL style
    content2 = [
        {"type": "file", "file": {"filename": "doc.xlsx", "url": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,AAAA"}}
    ]
    files2 = _extract_file_attachments(content2)
    assert len(files2) == 1 and files2[0]["mime_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    print("  PASS: data URL file attachment")


# ── Test 6: Responses API input conversion ─────────────────────
def test_responses_input():
    print("\n=== Test 6: Responses API input ===")
    msgs = _responses_input_to_messages("Hello there")
    assert len(msgs) == 1 and msgs[0].role == "user"
    print("  PASS: string input")

    msgs2 = _responses_input_to_messages([
        {"type": "message", "role": "user", "content": "Hi"},
        {"type": "function_call", "name": "get_weather", "arguments": '{"city":"NYC"}'},
        {"type": "function_call_output", "call_id": "c1", "output": "Sunny, 22C"}
    ])
    assert len(msgs2) == 3
    assert msgs2[0].role == "user"
    assert msgs2[1].role == "assistant" and msgs2[1].tool_calls
    assert msgs2[2].role == "tool"
    print("  PASS: mixed input types")

    msgs3 = _responses_input_to_messages("Hello", instructions="Be concise")
    assert len(msgs3) == 2 and msgs3[0].role == "system"
    print("  PASS: instructions -> system message")


# ── Test 7: Responses tools conversion ─────────────────────────
def test_responses_tools():
    print("\n=== Test 7: Responses tools conversion ===")
    flat = [{"type": "function", "name": "foo", "description": "A function", "parameters": {}}]
    nested = _responses_tools_to_chat_tools(flat)
    assert len(nested) == 1 and nested[0].function.name == "foo"
    print("  PASS: flat -> nested ToolDefinition")

    # Non-function tool ignored
    flat2 = [{"type": "web_search", "name": "search"}]
    nested2 = _responses_tools_to_chat_tools(flat2)
    assert len(nested2) == 0
    print("  PASS: non-function tool ignored")


# ── Test 8: Config provider switching ──────────────────────────
def test_config_providers():
    print("\n=== Test 8: Config provider switching ===")
    original = Config.PROVIDER
    for provider, expected_host in [
        ("chatgpt", "chatgpt.com"),
        ("claude", "claude.ai"),
        ("gemini", "aistudio.google.com"),
        ("deepseek", "chat.deepseek.com"),
        ("grok", "grok.com"),
        ("mistral", "chat.mistral.ai"),
        ("qwen", "chat.qwen.ai"),
        ("kimi", "kimi.moonshot.cn"),
    ]:
        Config.PROVIDER = provider
        url = Config.provider_url()
        model = Config.default_model()
        assert expected_host in url, f"{provider} URL mismatch: {url}"
        assert model, f"{provider} has no default model"
        print(f"  PASS: {provider} -> {url} ({model})")
    Config.PROVIDER = original


# ── Test 9: Model catalogs ─────────────────────────────────────
def test_model_catalogs():
    print("\n=== Test 9: Model catalogs ===")
    catalogs = {
        "chatgpt": _CHATGPT_MODELS, "claude": _CLAUDE_MODELS,
        "gemini": _GEMINI_MODELS, "deepseek": _DEEPSEEK_MODELS,
        "grok": _GROK_MODELS, "mistral": _MISTRAL_MODELS,
        "qwen": _QWEN_MODELS, "kimi": _KIMI_MODELS,
    }
    for name, models in catalogs.items():
        assert len(models) >= 2, f"{name} has only {len(models)} models"
        assert all(isinstance(m, str) for m in models), f"{name} has non-string models"
    print(f"  PASS: all 8 catalogs valid (total {sum(len(m) for m in catalogs.values())} models)")


# ── Test 10: Tool system prompt ────────────────────────────────
def test_tool_system_prompt():
    print("\n=== Test 10: Tool system prompt ===")
    tools = [
        ToolDefinition(type='function', function=FunctionDefinition(
            name='get_weather', description='Get weather', parameters={}
        ))
    ]
    prompt_auto = _build_tool_system_prompt(tools, tool_choice="auto")
    assert "get_weather" in prompt_auto
    assert "Available functions" in prompt_auto or "available" in prompt_auto.lower()
    print("  PASS: auto tool_choice")

    prompt_req = _build_tool_system_prompt(tools, tool_choice="required")
    assert "MUST call" in prompt_req
    print("  PASS: required tool_choice")

    prompt_forced = _build_tool_system_prompt(tools, tool_choice={"type": "function", "function": {"name": "get_weather"}})
    assert "get_weather" in prompt_forced and "MUST call" in prompt_forced
    print("  PASS: forced tool_choice")


# ── Test 11: Cache ─────────────────────────────────────────────
def test_cache():
    print("\n=== Test 11: Cache ===")
    init_cache()
    cache = get_cache()
    assert cache is not None
    # Cache should be disabled (TTL=0)
    print(f"  PASS: cache initialized (TTL={Config.CACHE_TTL})")


# ── Test 12: Schemas validation ────────────────────────────────
def test_schemas():
    print("\n=== Test 12: Schemas validation ===")
    req = ChatRequest(message="Hello")
    assert req.message == "Hello"
    print("  PASS: ChatRequest")

    resp = ChatResponse(message="Hi", thread_id="t1", response_time_ms=100, images=[], has_images=False)
    assert resp.message == "Hi"
    print("  PASS: ChatResponse")

    status = StatusResponse(status="ok", logged_in=True, current_thread="t1")
    assert status.status == "ok"
    print("  PASS: StatusResponse")

    # OpenAI schemas
    cc_req = ChatCompletionRequest(messages=[ChatMessage(role="user", content="Hi")])
    assert cc_req.model is not None  # has default
    assert cc_req.stream is False
    print(f"  PASS: ChatCompletionRequest (model={cc_req.model})")


# ── Run all ────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_json_extraction, test_tool_call_parsing, test_prompt_builder,
        test_image_extraction, test_file_attachments, test_responses_input,
        test_responses_tools, test_config_providers, test_model_catalogs,
        test_tool_system_prompt, test_cache, test_schemas,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed == 0:
        print("ALL TESTS PASSED ✅")
    else:
        print("SOME TESTS FAILED ❌")
        sys.exit(1)
