import os
import sys
import subprocess
import time
import requests
import socket

def resource_path(p):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, p)
    return os.path.join(os.path.abspath("."), p)

class OllamaManager:
    def __init__(self, model_name="llama3.2:3b"):
        self.model_name = model_name
        self.ollama_path = resource_path("ollama.exe")
        self.port = 11434
        self.process = None

    def is_server_running(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', self.port)) == 0

    def start_server(self):
        if self.is_server_running():
            print("Ollama is already running.")
            return True

        if not os.path.exists(self.ollama_path):
            # Try finding it in the same directory as the script/exe
            self.ollama_path = os.path.join(os.path.dirname(sys.executable), "ollama.exe")
            if not os.path.exists(self.ollama_path):
                print(f"ollama.exe not found at {self.ollama_path}")
                return False

        print(f"Starting Ollama server from {self.ollama_path}...")
        # Start as a background process
        env = os.environ.copy()
        # You can set OLLAMA_HOST or other env vars here if needed
        self.process = subprocess.Popen(
            [self.ollama_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        # Wait for server to start
        for _ in range(30):
            if self.is_server_running():
                print("Ollama server started successfully.")
                return True
            time.sleep(1)
        
        print("Failed to start Ollama server.")
        return False

    def check_and_pull_model(self, progress_callback=None):
        try:
            response = requests.get(f"http://localhost:{self.port}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                if any(m['name'] == self.model_name or m['name'].startswith(self.model_name) for m in models):
                    print(f"Model {self.model_name} is already available.")
                    return True
            
            print(f"Pulling model {self.model_name}...")
            if progress_callback:
                progress_callback(f"กำลังดาวน์โหลดโมเดล {self.model_name}... (อาจใช้เวลาสักครู่)")
            
            # Run ollama pull
            subprocess.run([self.ollama_path, "pull", self.model_name], check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return True
        except Exception as e:
            print(f"Error checking/pulling model: {e}")
            return False

    def stop_server(self):
        if self.process:
            self.process.terminate()
            print("Ollama server stopped.")
