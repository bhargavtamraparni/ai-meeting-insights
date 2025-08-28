import os
import json
import httpx
import re
import configparser
from sqlalchemy.orm import sessionmaker
from faster_whisper import WhisperModel
from pydub import AudioSegment
import chromadb
import asyncio
from .crud import meeting_crud
from concurrent.futures import ThreadPoolExecutor
import io

class AIServiceConfig:
    """Loads all AI-related configuration from environment variables."""

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = os.path.join(base_dir, 'config', 'config.properties')
        config = configparser.ConfigParser()
        config.read(config_file)
        self.whisper_model_path = config.get("AI", "WHISPER_MODEL_PATH", fallback=None)
        self.ollama_api_url = config.get("AI", "OLLAMA_API_URL", fallback=None)
        self.ollama_embed_url = config.get("AI", "OLLAMA_EMBED_URL", fallback=None)
        self.ollama_llm_model = config.get("AI", "OLLAMA_LLM_MODEL", fallback=None)
        self.ollama_embed_model = config.get("AI", "OLLAMA_EMBED_MODEL", fallback=None)
        self.validate()

    def validate(self):
        # Updated validation check
        if not all([self.ollama_api_url, self.ollama_embed_url, self.ollama_llm_model, self.ollama_embed_model]):
            raise ValueError("One or more AI service environment variables are not set.")

class TranscriptionService:
    """Handles audio processing and transcription."""

    def __init__(self, config: AIServiceConfig):
        self.config = config
        # Initialize the Whisper model once when the service is created.
        # This is efficient as it loads the model into memory only once.
        print(f"Loading Whisper model from: {self.config.whisper_model_path}")
        self.whisper = WhisperModel(self.config.whisper_model_path, device="cpu", compute_type="int8")

    def _convert_to_wav(self, filepath: str) -> io.BytesIO:
        """
        Converts any audio/video file to a 16kHz mono WAV file, which is
        the required format for whisper.cpp.
        """
        audio = AudioSegment.from_file(filepath)
        audio = audio.set_channels(1).set_frame_rate(16000)

        buf = io.BytesIO()
        audio.export(buf, format="wav")
        buf.seek(0)
        return buf

    def _split_audio(self, wav_buffer: io.BytesIO, chunk_length_ms: int = 120000):
        """
        Split audio into chunks
        """
        audio = AudioSegment.from_file(wav_buffer)
        chunks = []

        for i in range(0, len(audio), chunk_length_ms):
            chunk = audio[i:i + chunk_length_ms]
            buf = io.BytesIO()
            chunk.export(buf, format="wav")
            buf.seek(0)
            chunks.append(buf)

        return chunks

    def _transcribe_chunk(self, chunk: io.BytesIO) -> str:
        segments, _ = self.whisper.transcribe(chunk)
        return " ".join(segment.text for segment in segments)

    async def transcribe(self, filepath: str) -> str:
        wav_buffer = self._convert_to_wav(filepath)
        chunks = self._split_audio(wav_buffer)

        # Use ProcessPoolExecutor to handle CPU-bound transcription tasks
        loop = asyncio.get_event_loop()
        # Use ThreadPoolExecutor instead of ProcessPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:
            tasks = [
                loop.run_in_executor(pool, self._transcribe_chunk, chunk)
                for chunk in chunks
            ]
            results = await asyncio.gather(*tasks)

        return " ".join(results)

class InsightExtractor:
    """Extracts structured insights using an LLM."""

    def __init__(self, config: AIServiceConfig):
        self.config = config

    def _get_prompt(self, transcript: str) -> str:
        return f"""You are an expert meeting analysis assistant. Your task is to perform a two-step analysis of the 
        meeting transcript below and provide the output in a single, strict JSON format.
        **Step 1: Identify Participants**
        First, read the entire transcript and identify a definitive list of all unique participant names mentioned.
        **Step 2: Extract Detailed Insights**
        Using the full transcript AND the list of participants you identified in Step 1, extract the required information.
        The final JSON object must have the following keys: "participants", "summary", "action_items", "decisions", 
        "keywords", and "sentiment".
        - "participants": A list of all unique participant names identified in Step 1.
        - "summary": A concise, neutral summary of the meeting's purpose and key discussion points.
        - "action_items": A list of tasks. Each item must be an object with "task" and "assigned_to" keys. The "assigned_
           to" value MUST be a name from the "participants" list you created. If the assignee is unclear or not in the 
           participant list, you MUST use the string "Unassigned".
        - "decisions": A list of key decisions made during the meeting.
        - "keywords": A list of 5-7 single-word or two-word key topics.
        - "sentiment": The overall meeting sentiment. Must be one of: "Positive", "Neutral", "Negative".
        Do not include any preamble or explanation outside of the JSON object.
        **Transcript:**
        \"\"\"
        {transcript}
        \"\"\"
        """
    def _calculate_keyword_frequency(self, keywords: list, transcript: str) -> list:
        """Counts the occurrences of each keyword in the transcript."""
        frequencies = []
        transcript_lower = transcript.lower()
        for keyword in keywords:
            # Use regex to find whole words to avoid matching substrings (e.g., 'art' in 'start')
            # The \b markers are word boundaries.
            count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', transcript_lower))
            if count > 0:  # Only include keywords that are actually found
                frequencies.append({"keyword": keyword, "count": count})

        # Sort by count descending and take the top 7 for a clean chart
        frequencies.sort(key=lambda x: x['count'], reverse=True)
        return frequencies[:7]

    def extract(self, transcript: str) -> dict:
        payload = {
                    "model": self.config.ollama_llm_model,
                    "prompt": self._get_prompt(transcript),
                    "format": "json",
                    "stream": True
        }
        try:
            with httpx.Client(timeout=None) as client:
                with client.stream("POST", self.config.ollama_api_url, json=payload) as response:
                    response.raise_for_status()
                    insights = ""

                    for line in response.iter_lines():
                        if line.strip():
                            chunk = json.loads(line)
                            # Ollama puts the actual partial text in chunk['response']
                            insights += chunk.get("response", "")

                # At this point, full_text contains the reconstructed JSON string
                insights = json.loads(insights)

                if 'keywords' in insights and isinstance(insights['keywords'], list):
                    # Replace the simple list of keywords with our new list of objects
                    insights['keywords'] = self._calculate_keyword_frequency(insights['keywords'], transcript)

            return insights

        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            print(f"Ollama insight extraction error: {e}")
            return {"summary": "Error extracting insights.", "action_items": [], "decisions": [], "keywords": [], "sentiment": "Unknown"}



class VectorStoreService:
    """Manages vector embeddings and semantic search with ChromaDB."""

    def __init__(self, config: AIServiceConfig):
        self.config = config
        self.client = chromadb.PersistentClient(path="chromadb")
        self.collection = self.client.get_or_create_collection(name="meeting_transcripts")

    def _get_embedding(self, text: str) -> list[float] | None:
        payload = {"model": self.config.ollama_embed_model, "prompt": text}
        try:
            with httpx.Client(timeout=None) as client:
                response = client.post(self.config.ollama_embed_url, json=payload)
                response.raise_for_status()
                return response.json()['embedding']
        except (httpx.RequestError, KeyError) as e:
            print(f"Ollama embedding error: {e}")
            return None

    def _chunk_text(self, text: str, chunk_size=300, overlap=50) -> list[str]:
        words = text.split()
        if not words: return []
        return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size - overlap)]

    def add_transcript(self, meeting_id: int, transcript: str):
        chunks = self._chunk_text(transcript)
        if not chunks: return

        embeddings = [self._get_embedding(chunk) for chunk in chunks if self._get_embedding(chunk) is not None]
        if not embeddings: return

        valid_chunks = [chunk for i, chunk in enumerate(chunks) if embeddings[i] is not None]
        doc_ids = [f"{meeting_id}_{i}" for i in range(len(valid_chunks))]
        metadata = [{"meeting_id": meeting_id} for _ in valid_chunks]

        self.collection.add(embeddings=embeddings, documents=valid_chunks, metadatas=metadata, ids=doc_ids)

    def search(self, meeting_id: int, query: str, n_results=3) -> str:
        """
        Performs Retrieval-Augmented Generation.
        1. Retrieves relevant chunks from the vector store.
        2. Feeds them to an LLM to synthesize an answer.
        """
        # 1. Retrieval
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return "Could not process your query."

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"meeting_id": meeting_id}
        )
        context_chunks = results['documents'][0] if results and results['documents'] else []

        if not context_chunks:
            return "I couldn't find any information related to your query in this meeting's transcript."

        # 2. Generation
        context_str = "\n\n".join(context_chunks)
        rag_prompt = f"""You are a helpful assistant. Using ONLY the context below, answer the user's question. If the 
        answer is not in the context, say that you cannot find the answer in the provided text. Be concise.

        Context:
        ---
        {context_str}
        ---
        
        User Question: {query}
        Answer:"""

        payload = {
            "model": self.config.ollama_llm_model,
            "prompt": rag_prompt,
            "stream": False
        }
        try:
            with httpx.Client(timeout=None) as client:
                with client.stream("POST", self.config.ollama_api_url, json=payload) as response:
                    response.raise_for_status()
                    full_text = ""

                    for line in response.iter_lines():
                        if line.strip():
                            chunk = json.loads(line)
                            # Ollama puts the actual partial text in chunk['response']
                            full_text += chunk.get("response", "")

            # At this point, full_text contains the reconstructed JSON string
            return full_text

        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            print(f"Ollama insight extraction error: {e}")
            return "There was an error generating an answer."

class AIPipeline:
    """Orchestrates the entire AI processing workflow."""

    def __init__(self, db_session_factory: sessionmaker):
        self.config = AIServiceConfig()
        self.transcriber = TranscriptionService(self.config)
        self.extractor = InsightExtractor(self.config)
        self.vector_store = VectorStoreService(self.config)
        self.db_session_factory = db_session_factory

    def run(self, meeting_id: int, filepath: str):
        db = self.db_session_factory()
        try:
            print(f"[{meeting_id}] AI Pipeline Started.")

            meeting_crud.update_status(db, meeting_id, "transcribing")
            print(f"[{meeting_id}] AI Pipeline: Transcribing...")
            # transcript = self.transcriber.transcribe(filepath)
            transcript = asyncio.run(self.transcriber.transcribe(filepath))
            meeting_crud.update_transcript(db, meeting_id, transcript)
            print(f"[{meeting_id}] Transcription complete.")

            meeting_crud.update_status(db, meeting_id, "analyzing")
            print(f"[{meeting_id}] AI Pipeline: Analyzing for insights...")
            insights = self.extractor.extract(transcript)
            meeting_crud.update_insights(db, meeting_id, insights)
            print(f"[{meeting_id}] Insight extraction complete.")

            self.vector_store.add_transcript(meeting_id, transcript)
            print(f"[{meeting_id}] Embeddings stored.")

            meeting_crud.update_status(db, meeting_id, "completed")
            print(f"[{meeting_id}] AI Pipeline Finished Successfully.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            meeting_crud.update_status(db, meeting_id, "failed")
            print(f"[{meeting_id}] AI Pipeline Failed: {e}")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
            db.close()