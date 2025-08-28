# AI Meeting Intelligence Platform

This is a full-stack web application that uses local AI models to transcribe meeting recordings, extract key insights, and provide a searchable, intelligent summary of the proceedings.



---

## 🚀 Features

- **Modern UI:** A clean, professional, and responsive interface built with React and Tailwind CSS.
- **File Upload:** Upload audio/video recordings via a user-friendly drag-and-drop interface.
- **GPU-Accelerated Transcription:** Utilizes `faster-whisper` for high-speed, accurate speech-to-text on NVIDIA GPUs, with a CPU fallback.
- **Intelligent Insight Extraction:** Leverages a local Ollama instance (e.g., Llama 3) with advanced prompting to identify participants, generate summaries, and extract action items, decisions, and keywords with frequency.
- **Precise Q&A Search:** Ask natural language questions about your meeting and get concise, synthesized answers using a RAG (Retrieval-Augmented Generation) pipeline.
- **Enhanced Analytics:** Visualize meeting data with a tabbed interface showing key metrics, participant action item load, and a topic cloud.
- **Persistent Storage:** All meeting data is saved in a local SQLite database, and vector embeddings are stored in ChromaDB for persistence across sessions.

---

## 🛠️ Tech Stack

- **Frontend:** React, Tailwind CSS, Chart.js, Axios
- **Backend:** Python, FastAPI
- **Database:** SQLite
- **AI Components:**
  - **Transcription:** `faster-whisper` (GPU-accelerated)
  - **LLM / Embeddings:** `Ollama`
  - **Vector Search:** `ChromaDB`
- **Audio Processing:** `ffmpeg`

---

## ⚙️ Setup and Installation

Follow these steps to get the application running on your local machine.

### 1. Prerequisites

- **Python 3.9+** and `pip`.
- **Node.js 18+** and `npm`.
- **NVIDIA GPU** with up-to-date drivers (Required for GPU acceleration).
- **NVIDIA CUDA Toolkit:** Verify by running `nvcc --version` in your terminal. If not installed, download it from the [NVIDIA website](https://developer.nvidia.com/cuda-toolkit).
- **ffmpeg:** Install via your system's package manager (`brew install ffmpeg`, `sudo apt-get install ffmpeg`, or download from the [official site](https://ffmpeg.org/)).
- **Ollama:** Install from [ollama.com](https://ollama.com). After installation, pull the required models:
  ```sh
  ollama pull llama3
  ollama pull nomic-embed-text
  ```

### 2. Clone the Repository

```sh
git clone https://github.com/your-username/ai-meeting-intel.git
cd ai-meeting-intel
```

### 3. Backend Setup

> **Note:** On Windows, it is highly recommended to run these commands from a **Developer Command Prompt for Visual Studio** to ensure the necessary C++ build tools for Python packages are found correctly.

1.  **Navigate to the backend directory:**
    ```sh
    cd backend
    ```

2.  **Create and activate a Python virtual environment:**
    ```sh
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Create your local configuration:**
    - The application looks for a `config.properties` file. A template is provided. Copy it to create your local config.
      ```sh
      # On Windows
      copy config\config.properties.example config\config.properties
      # On macOS/Linux
      cp config/config.properties.example config/config.properties
      ```
    - The default values are ready for a standard local setup. You can edit this file to change the Whisper model size (e.g., `WHISPER_MODEL_NAME=small.en`).

5.  **Run the backend server:**
    - Open a terminal and run the backend. Leave this terminal running.
    ```sh
    uvicorn app.main:app --reload
    ```
    - The backend will be available at `http://127.0.0.1:8000`.

### 4. Frontend Setup

1.  **Open a new, separate terminal.**

2.  **Navigate to the frontend directory:**
    ```sh
    cd frontend
    ```

3.  **Install Node.js dependencies:**
    ```sh
    npm install
    ```

4.  **Run the frontend development server:**
    - Leave this terminal running.
    ```sh
    npm start
    ```
    - Your browser should automatically open to `http://localhost:3000`.

### 5. You're Ready!

The application is now running. Open `http://localhost:3000` in your browser and upload a meeting file to begin.
