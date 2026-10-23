"""Live API adapters; no simulation fallback."""
import os
from dataclasses import dataclass

@dataclass
class Reply:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    model: str

def generate(provider, model, system, prompt, max_tokens=512):
    if provider == 'openai':
        if not os.getenv('OPENAI_API_KEY'): raise RuntimeError('Missing OPENAI_API_KEY')
        from openai import OpenAI
        r=OpenAI(timeout=120,max_retries=0).responses.create(model=model,instructions=system,input=prompt,max_output_tokens=max_tokens)
        return Reply(r.output_text or '',getattr(r.usage,'input_tokens',None),getattr(r.usage,'output_tokens',None),r.model)
    if provider == 'anthropic':
        if not os.getenv('ANTHROPIC_API_KEY'): raise RuntimeError('Missing ANTHROPIC_API_KEY')
        from anthropic import Anthropic
        r=Anthropic(timeout=120,max_retries=0).messages.create(model=model,max_tokens=max_tokens,system=system,messages=[{'role':'user','content':prompt}])
        return Reply('\n'.join(x.text for x in r.content if x.type=='text'),r.usage.input_tokens,r.usage.output_tokens,r.model)
    if provider == 'gemini':
        key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not key: raise RuntimeError('Missing GEMINI_API_KEY')
        from google import genai
        from google.genai import types
        with genai.Client(api_key=key) as client:
            r=client.models.generate_content(model=model,contents=prompt,config=types.GenerateContentConfig(system_instruction=system,max_output_tokens=max_tokens))
        u=r.usage_metadata
        return Reply(r.text or '',getattr(u,'prompt_token_count',None),getattr(u,'candidates_token_count',None),model)
    raise ValueError('Unknown provider: '+provider)
