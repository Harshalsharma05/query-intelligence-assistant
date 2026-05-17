import os
from dotenv import load_dotenv
import anthropic
from groq import Groq
from supabase import create_client

load_dotenv()

# API Keys 
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
SUPABASE_URL      = os.environ["SUPABASE_URL"]
SUPABASE_KEY      = os.environ["SUPABASE_KEY"]

# LLM Clients 
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
groq_client      = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

GROQ_MODEL    = "llama-3.3-70b-versatile"
CLAUDE_MODEL  = "claude-sonnet-4-20250514"

# Supabase Client
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)