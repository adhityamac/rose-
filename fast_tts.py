"""
Fast TTS Service for Rose AI Assistant
Optimized for speed and responsiveness
"""

import threading
import queue
import time
from typing import Optional, Callable
import io
import tempfile
import os

class FastTTSService:
    """Fast, non-blocking TTS service"""
    
    def __init__(self):
        self.is_available = False
        self.voice_queue = queue.Queue()
        self.is_speaking = False
        self.current_voice = "en-US-AriaNeural"
        self.rate = "+0%"
        self.pitch = "+0Hz"
        self.volume = "+0%"
        
        # Try to import edge-tts
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self.is_available = True
            print("✅ Fast TTS service initialized")
        except ImportError:
            print("⚠️ Edge TTS not available - using fallback")
            self.edge_tts = None
            self.is_available = False
        
        # Start TTS worker thread
        self.worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.worker_thread.start()
    
    def speak(self, text: str, voice: str = None, rate: str = None, 
              pitch: str = None, volume: str = None, callback: Callable = None):
        """Speak text asynchronously"""
        if not self.is_available:
            print(f"[TTS] {text}")
            if callback:
                callback()
            return
        
        # Use provided parameters or defaults
        voice = voice or self.current_voice
        rate = rate or self.rate
        pitch = pitch or self.pitch
        volume = volume or self.volume
        
        # Add to queue for processing
        tts_request = {
            'text': text,
            'voice': voice,
            'rate': rate,
            'pitch': pitch,
            'volume': volume,
            'callback': callback,
            'timestamp': time.time()
        }
        
        self.voice_queue.put(tts_request)
    
    def speak_immediate(self, text: str, voice: str = None):
        """Speak text immediately (interrupts current speech)"""
        if not self.is_available:
            print(f"[TTS] {text}")
            return
        
        # Clear queue and stop current speech
        self._clear_queue()
        self._stop_current_speech()
        
        # Speak immediately
        self.speak(text, voice)
    
    def _tts_worker(self):
        """TTS worker thread"""
        while True:
            try:
                # Get next TTS request
                request = self.voice_queue.get(timeout=1)
                
                # Skip if request is too old (older than 5 seconds)
                if time.time() - request['timestamp'] > 5:
                    continue
                
                self.is_speaking = True
                self._process_tts_request(request)
                self.is_speaking = False
                
                # Mark task as done
                self.voice_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS Worker error: {e}")
                self.is_speaking = False
    
    def _process_tts_request(self, request):
        """Process a TTS request"""
        try:
            text = request['text']
            voice = request['voice']
            rate = request['rate']
            pitch = request['pitch']
            volume = request['volume']
            callback = request['callback']
            
            # Create SSML for better control
            ssml = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{voice}">
                    <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Generate audio
            audio_data = self._generate_audio(ssml)
            
            if audio_data:
                # Play audio
                self._play_audio(audio_data)
            
            # Call callback if provided
            if callback:
                callback()
                
        except Exception as e:
            print(f"TTS processing error: {e}")
    
    def _generate_audio(self, ssml: str) -> Optional[bytes]:
        """Generate audio from SSML"""
        try:
            import asyncio
            
            async def _generate():
                communicate = self.edge_tts.Communicate(ssml)
                return await communicate.async_generate()
            
            # Run in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                audio_data = loop.run_until_complete(_generate())
                return audio_data
            finally:
                loop.close()
                
        except Exception as e:
            print(f"Audio generation error: {e}")
            return None
    
    def _play_audio(self, audio_data: bytes):
        """Play audio data"""
        try:
            import pygame
            
            # Initialize pygame mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Load and play
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Cleanup
            pygame.mixer.music.unload()
            os.unlink(temp_file_path)
            
        except ImportError:
            # Fallback: try to play with system default
            try:
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_file_path = temp_file.name
                
                import subprocess
                subprocess.run(['start', temp_file_path], shell=True, check=False)
                
                # Cleanup after a delay
                threading.Timer(10, lambda: os.unlink(temp_file_path)).start()
                
            except Exception as e:
                print(f"Audio playback error: {e}")
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    def _clear_queue(self):
        """Clear the TTS queue"""
        while not self.voice_queue.empty():
            try:
                self.voice_queue.get_nowait()
                self.voice_queue.task_done()
            except queue.Empty:
                break
    
    def _stop_current_speech(self):
        """Stop current speech"""
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except:
            pass
    
    def set_voice(self, voice: str):
        """Set the default voice"""
        self.current_voice = voice
    
    def set_rate(self, rate: str):
        """Set the speech rate"""
        self.rate = rate
    
    def set_pitch(self, pitch: str):
        """Set the speech pitch"""
        self.pitch = pitch
    
    def set_volume(self, volume: str):
        """Set the speech volume"""
        self.volume = volume
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if not self.is_available:
            return []
        
        try:
            import asyncio
            
            async def _get_voices():
                voices = await self.edge_tts.list_voices()
                return [voice['ShortName'] for voice in voices]
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                voices = loop.run_until_complete(_get_voices())
                return voices
            finally:
                loop.close()
                
        except Exception as e:
            print(f"Error getting voices: {e}")
            return []
    
    def is_busy(self) -> bool:
        """Check if TTS is currently speaking"""
        return self.is_speaking or not self.voice_queue.empty()
    
    def wait_until_done(self, timeout: float = 10.0):
        """Wait until TTS is done speaking"""
        start_time = time.time()
        while self.is_busy() and (time.time() - start_time) < timeout:
            time.sleep(0.1)

# Global instance
fast_tts = FastTTSService()
