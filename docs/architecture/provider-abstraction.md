# ORVYN: Provider Abstraction & Pluggability

## 1. Zero Vendor Lock-in
ORVYN does not hard-code OpenAI, Anthropic, Gemini, or Twilio into the domain core. Every external interaction is mediated by abstract interfaces:

1. **`LLMProvider`**:
   - `generate(messages, tools, temperature)`
   - Backends: Mock, Gemini, OpenAI, HuggingFace
2. **`EmbeddingProvider`**:
   - `embed(texts)`
3. **`TelephonyProvider`**:
   - `make_call(request)`, `hangup_call(call_id)`
   - Backends: Mock, Twilio, Vapi
4. **`SearchProvider`**:
   - `search(query, max_results)`
   - Backends: Mock, Tavily, DuckDuckGo

## 2. Dynamic Factory Registry
Providers register themselves with factory classes (`LLMProviderFactory`, `TelephonyProviderFactory`, `SearchProviderFactory`). When an API key is not configured, the provider factory cleanly defaults to mock or returns explicit capability errors, allowing the platform to run offline in test environments.
