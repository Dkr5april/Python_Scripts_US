import logging
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.plugins import deepgram, groq, silero

load_dotenv()
logger = logging.getLogger("sap-copilot")

# Pre-warm loads the VAD model into memory before any user connects
def prewarm(proc):
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("✅ Silero VAD Pre-warmed")

async def entrypoint(ctx: JobContext):
    # 1. Define the Core Instructions (Persona)
    sap_instructions = (
        "You are a Senior SAP Project Manager. Provide expert guidance. "
        "Structure answers into Levels 1-5 when asked. "
        "Keep voice responses concise and professional."
    )

    # 2. Setup the Chat Context for history
    initial_ctx = llm.ChatContext()
    initial_ctx.add_message(
        role="system",
        content=sap_instructions  # Use 'content' for modern LiveKit versions
    )

    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)

    # 3. Define the Agent with the mandatory 'instructions' argument
    # In v1.4.1+, instructions is a required keyword-only argument.
    agent = agents.Agent(
        stt=deepgram.STT(),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=deepgram.TTS(),
        instructions=sap_instructions, # Fix for the TypeError
        chat_ctx=initial_ctx,
        vad=ctx.proc.userdata["vad"],
    )

    # 4. Start the session in the room
    agent.start(ctx.room)
    
    # 5. Initial greeting
    await agent.say(
        "SAP System online. Ready for project architecture queries.", 
        allow_interruptions=True
    )

if __name__ == "__main__":
    # The CLI entry point
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))