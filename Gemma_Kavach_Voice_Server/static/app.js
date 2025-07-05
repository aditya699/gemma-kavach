// Enhanced Voice Command System with Audio Playback

class VoiceCommandSystem {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.speechSynthesis = window.speechSynthesis;
        this.currentZone = null;
        this.commandCount = 0;
        this.successCount = 0;
        this.audioPlayer = null; // For playing TTS audio

        this.elements = {
            voiceButton: document.getElementById('voiceButton'),
            voiceStatusText: document.getElementById('voiceStatusText'),
            voiceStatusIndicator: document.getElementById('voiceStatusIndicator'),
            voiceFeedback: document.getElementById('voiceFeedback'),
            transcriptionSection: document.getElementById('transcriptionSection'),
            transcriptionText: document.getElementById('transcriptionText'),
            responseSection: document.getElementById('responseSection'),
            responseText: document.getElementById('responseText'),
            processingModal: document.getElementById('processingModal'),
            processingText: document.getElementById('processingText'),
            processingStep: document.getElementById('processingStep'),
            connectionStatus: document.getElementById('connectionStatus'),
            currentZone: document.getElementById('currentZone'),
            commandHistory: document.getElementById('commandHistory'),
            voiceEngineStatus: document.getElementById('voiceEngineStatus'),
            databaseStatus: document.getElementById('databaseStatus'),
            totalCommands: document.getElementById('totalCommands'),
            successRate: document.getElementById('successRate')
        };
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.checkServerConnection();
        await this.checkMicrophonePermission();
        this.updateStats();
        this.addLogEntry('🎤 Voice command system with TTS initialized', 'success');
    }
    
    setupEventListeners() {
        // Simple click to start/stop recording
        this.elements.voiceButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleRecording();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.ctrlKey && !this.isRecording) {
                e.preventDefault();
                this.startRecording();
            }
            if (e.code === 'Escape' && this.isRecording) {
                e.preventDefault();
                this.stopRecording();
            }
        });
        
        // Zone item clicks
        document.querySelectorAll('.zone-item').forEach(item => {
            item.addEventListener('click', () => {
                const zone = item.dataset.zone;
                this.selectZone(`Mela Zone ${zone}`);
            });
        });
    }
    
    async checkServerConnection() {
        try {
            const response = await fetch('/api/monitoring/status');
            if (response.ok) {
                const status = await response.json();
                this.updateConnectionStatus(true);
                this.elements.databaseStatus.textContent = 'Connected';
                this.elements.databaseStatus.style.color = '#00ff88';
                
                // Check if TTS is enabled
                if (status.text_to_speech === 'enabled') {
                    this.addLogEntry('🎵 Text-to-Speech enabled', 'success');
                }
            } else {
                throw new Error('Server not responding');
            }
        } catch (error) {
            console.error('Server connection failed:', error);
            this.updateConnectionStatus(false);
            this.elements.databaseStatus.textContent = 'Disconnected';
            this.elements.databaseStatus.style.color = '#ff3366';
        }
    }
    
    updateConnectionStatus(connected) {
        const statusEl = this.elements.connectionStatus;
        if (connected) {
            statusEl.className = 'status-indicator connected';
            statusEl.innerHTML = '<i class="fas fa-circle"></i><span>Connected</span>';
        } else {
            statusEl.className = 'status-indicator disconnected';
            statusEl.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
        }
    }
    
    async checkMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            this.updateVoiceStatus('ready', 'Click to start recording');
            this.elements.voiceEngineStatus.textContent = 'Ready';
            this.elements.voiceEngineStatus.style.color = '#00ff88';
            this.addLogEntry('🎤 Microphone access granted', 'success');
        } catch (error) {
            console.error('Microphone permission denied:', error);
            this.updateVoiceStatus('error', 'Microphone access required');
            this.elements.voiceButton.disabled = true;
            this.elements.voiceEngineStatus.textContent = 'No Access';
            this.elements.voiceEngineStatus.style.color = '#ff3366';
            this.addLogEntry('❌ Microphone access denied', 'error');
        }
    }
    
    resetVoiceButton() {
        this.elements.voiceButton.classList.remove('recording');
        this.elements.voiceButton.innerHTML = `
            <div class="button-inner">
                <i class="fas fa-microphone"></i>
            </div>
            <div class="pulse-ring"></div>
            <div class="pulse-ring-2"></div>
        `;
        this.elements.voiceButton.style.background = '';
        this.elements.voiceButton.style.boxShadow = '';
    }
    
    async convertToWav(audioBlob) {
        return new Promise((resolve, reject) => {
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 16000  // Force 16kHz for better server compatibility
                });
                const fileReader = new FileReader();
                
                fileReader.onload = async (e) => {
                    try {
                        const arrayBuffer = e.target.result;
                        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                        
                        // Convert to WAV with proper format
                        const wavBuffer = this.audioBufferToWav(audioBuffer);
                        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
                        
                        resolve(wavBlob);
                    } catch (decodeError) {
                        reject(new Error(`Audio decode failed: ${decodeError.message}`));
                    }
                };
                
                fileReader.onerror = () => reject(new Error('Failed to read audio file'));
                fileReader.readAsArrayBuffer(audioBlob);
                
            } catch (error) {
                reject(new Error(`Audio conversion failed: ${error.message}`));
            }
        });
    }
    
    audioBufferToWav(buffer) {
        const length = buffer.length;
        const sampleRate = buffer.sampleRate;
        const arrayBuffer = new ArrayBuffer(44 + length * 2);
        const view = new DataView(arrayBuffer);
        
        // WAV header with proper format
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);               // PCM format
        view.setUint16(20, 1, true);                // Linear quantization
        view.setUint16(22, 1, true);                // Mono channel
        view.setUint32(24, sampleRate, true);       // Sample rate
        view.setUint32(28, sampleRate * 2, true);   // Byte rate
        view.setUint16(32, 2, true);                // Block align
        view.setUint16(34, 16, true);               // Bits per sample
        writeString(36, 'data');
        view.setUint32(40, length * 2, true);
        
        // Convert float samples to 16-bit PCM
        const channelData = buffer.getChannelData(0);
        let offset = 44;
        for (let i = 0; i < length; i++) {
            const sample = Math.max(-1, Math.min(1, channelData[i]));
            view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
            offset += 2;
        }
        
        return arrayBuffer;
    }
    
    async startRecording() {
        if (this.isRecording || this.elements.voiceButton.disabled) return;
        
        try {
            this.audioChunks = [];
            
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000,  // Standard for speech recognition
                    channelCount: 1     // Mono audio for better compatibility
                }
            });
            
            // Prefer uncompressed formats for better server compatibility
            let mimeType = 'audio/webm;codecs=opus';
            if (MediaRecorder.isTypeSupported('audio/wav')) {
                mimeType = 'audio/wav';
            } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=pcm')) {
                mimeType = 'audio/webm;codecs=pcm';  // Uncompressed WebM
            }
            
            console.log('🎵 Using audio format:', mimeType);
            this.mediaRecorder = new MediaRecorder(stream, { mimeType });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                stream.getTracks().forEach(track => track.stop());
                this.processAudio();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.elements.voiceButton.classList.add('recording');
            this.elements.voiceButton.innerHTML = `
                <div class="button-inner stop-recording">
                    <i class="fas fa-stop"></i>
                </div>
                <div class="pulse-ring active"></div>
                <div class="pulse-ring-2 active"></div>
            `;
            
            this.elements.voiceButton.style.background = 'linear-gradient(135deg, #ff3366 0%, #ff6b9d 100%)';
            this.elements.voiceButton.style.boxShadow = '0 0 30px rgba(255, 51, 102, 0.6)';
            
            this.updateVoiceStatus('listening', '🔴 RECORDING - Click red STOP button or press ESC');
            this.addLogEntry('🎤 Started recording', 'success');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.updateVoiceStatus('error', 'Recording failed');
            this.addLogEntry('❌ Recording failed: ' + error.message, 'error');
        }
    }
    
    toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    stopRecording() {
        if (!this.isRecording) return;
        
        this.isRecording = false;
        this.mediaRecorder.stop();
        
        this.resetVoiceButton();
        this.showProcessingModal('Processing...', 'Analyzing your voice command');
        this.updateVoiceStatus('processing', 'Processing...');
        this.addLogEntry('🎤 Stopped recording', 'success');
    }
    
    async processAudio() {
        try {
            console.log('📤 Processing audio chunks:', this.audioChunks.length);
            
            // Create audio blob with proper MIME type
            let audioBlob = new Blob(this.audioChunks, { 
                type: this.audioChunks[0]?.type || 'audio/webm;codecs=opus' 
            });
            
            console.log('🎵 Original audio:', audioBlob.size, 'bytes, type:', audioBlob.type);
            
            if (audioBlob.size < 1000) {
                throw new Error('Recording too short or no audio detected');
            }
            
            // Try to convert to WAV for better server compatibility
            try {
                audioBlob = await this.convertToWav(audioBlob);
                console.log('✅ Converted to WAV format:', audioBlob.size, 'bytes');
            } catch (convError) {
                console.log('⚠️ WAV conversion failed, using original format:', convError.message);
            }
            
            const formData = new FormData();
            const fileName = audioBlob.type.includes('wav') ? 'voice-command.wav' : 'voice-command.webm';
            formData.append('audio', audioBlob, fileName);
            
            console.log('📡 Sending', fileName, 'to server...');
            
            this.updateProcessingModal('Sending to AI...', 'Processing voice command');
            
            const response = await fetch('/api/voice-command', {
                method: 'POST',
                body: formData,
                timeout: 120000
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }
            
            const result = await response.json();
            console.log('✅ Voice command response:', result);
            this.handleVoiceResponse(result);
            
        } catch (error) {
            console.error('❌ Audio processing failed:', error);
            this.handleVoiceError(error.message);
        }
    }
    
    // Play audio from base64 encoded content
    async playAudioResponse(base64Audio) {
        try {
            if (!base64Audio) {
                console.log('No audio content to play');
                return;
            }
            
            console.log('🎵 Playing audio response...');
            
            // Convert base64 to blob
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            const audioBlob = new Blob([bytes], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Stop any currently playing audio
            if (this.audioPlayer) {
                this.audioPlayer.pause();
                this.audioPlayer = null;
            }
            
            // Create new audio element
            this.audioPlayer = new Audio(audioUrl);
            
            // Add visual feedback while playing
            this.audioPlayer.onplay = () => {
                this.updateVoiceStatus('speaking', '🔊 Playing response...');
                this.addLogEntry('🎵 Playing audio response', 'success');
            };
            
            this.audioPlayer.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this.updateVoiceStatus('ready', 'Click to start recording');
                console.log('✅ Audio playback completed');
            };
            
            this.audioPlayer.onerror = (error) => {
                console.error('Audio playback error:', error);
                URL.revokeObjectURL(audioUrl);
                this.updateVoiceStatus('ready', 'Click to start recording');
                this.addLogEntry('❌ Audio playback failed', 'error');
            };
            
            // Play the audio
            await this.audioPlayer.play();
            
        } catch (error) {
            console.error('Error playing audio:', error);
            this.addLogEntry('❌ Audio playback error: ' + error.message, 'error');
        }
    }
    
    handleVoiceResponse(result) {
        this.hideProcessingModal();
        this.commandCount++;
        
        if (result.success) {
            this.successCount++;
            
            // Show transcription
            if (result.transcription) {
                this.elements.transcriptionText.textContent = result.transcription;
                this.elements.transcriptionSection.style.display = 'block';
            }
            
            // Show response
            if (result.hindi_message) {
                this.elements.responseText.textContent = result.hindi_message;
                this.elements.responseSection.style.display = 'block';
                
                // Add audio playback button
                this.addAudioPlaybackButton(result.hindi_message, result.audio_content);
            }
            
            // Update current zone
            if (result.zone) {
                this.selectZone(result.zone);
            }
            
            // Show feedback
            this.elements.voiceFeedback.style.display = 'block';
            this.elements.voiceFeedback.classList.add('success-flash');
            
            this.updateVoiceStatus('success', 'Command processed successfully');
            this.addLogEntry(`✅ Voice command: "${result.zone}" - Success`, 'success');
            
            // Auto-play the audio response
            if (result.audio_content) {
                setTimeout(() => {
                    this.playAudioResponse(result.audio_content);
                }, 500); // Small delay for better UX
            }
            
        } else {
            // Handle error with audio
            if (result.audio_content) {
                this.playAudioResponse(result.audio_content);
            }
            this.handleVoiceError(result.error_message || 'Command processing failed');
        }
        
        this.updateStats();
        
        // Reset status after audio finishes or 5 seconds
        setTimeout(() => {
            if (!this.audioPlayer || this.audioPlayer.ended) {
                this.updateVoiceStatus('ready', 'Click to start recording');
                this.elements.voiceFeedback.classList.remove('success-flash');
            }
        }, 5000);
    }
    
    // Add audio playback button to response section
    addAudioPlaybackButton(text, audioContent) {
        // Remove existing audio button if any
        const existingButton = this.elements.responseSection.querySelector('.audio-playback-button');
        if (existingButton) {
            existingButton.remove();
        }
        
        if (audioContent) {
            const audioButton = document.createElement('button');
            audioButton.className = 'audio-playback-button';
            audioButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
            
            audioButton.addEventListener('click', () => {
                this.playAudioResponse(audioContent);
            });
            
            this.elements.responseSection.appendChild(audioButton);
        }
    }
    
    handleVoiceError(errorMessage) {
        this.hideProcessingModal();
        this.commandCount++;
        
        this.updateVoiceStatus('error', errorMessage);
        this.addLogEntry(`❌ Voice command failed: ${errorMessage}`, 'error');
        
        this.elements.voiceFeedback.classList.add('error-shake');
        
        setTimeout(() => {
            this.updateVoiceStatus('ready', 'Click to start recording');
            this.elements.voiceFeedback.classList.remove('error-shake');
        }, 3000);
        
        this.updateStats();
    }
    
    selectZone(zoneName) {
        this.currentZone = zoneName;
        
        const zoneDisplay = this.elements.currentZone.querySelector('.zone-label');
        const zoneStatus = this.elements.currentZone.querySelector('.zone-status');
        
        if (zoneDisplay && zoneStatus) {
            zoneDisplay.textContent = zoneName;
            zoneStatus.textContent = 'Last queried';
        }
        
        document.querySelectorAll('.zone-item').forEach(item => {
            item.classList.remove('selected');
            if (zoneName.includes(item.dataset.zone)) {
                item.classList.add('selected');
            }
        });
        
        this.addLogEntry(`📍 Selected zone: ${zoneName}`, 'success');
    }
    
    updateVoiceStatus(type, message) {
        this.elements.voiceStatusText.textContent = message;
        
        const indicator = this.elements.voiceStatusIndicator;
        indicator.className = `status-indicator-voice ${type}`;
        
        const statusText = indicator.querySelector('span');
        if (statusText) {
            statusText.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        }
    }
    
    showProcessingModal(title, step) {
        this.elements.processingModal.classList.add('show');
        this.elements.processingText.querySelector('h3').textContent = title;
        this.elements.processingStep.textContent = step;
    }
    
    updateProcessingModal(title, step) {
        if (this.elements.processingModal.classList.contains('show')) {
            this.elements.processingText.querySelector('h3').textContent = title;
            this.elements.processingStep.textContent = step;
        }
    }
    
    hideProcessingModal() {
        this.elements.processingModal.classList.remove('show');
    }
    
    updateStats() {
        this.elements.totalCommands.textContent = this.commandCount;
        
        if (this.commandCount > 0) {
            const successRate = Math.round((this.successCount / this.commandCount) * 100);
            this.elements.successRate.textContent = `${successRate}%`;
            this.elements.successRate.style.color = successRate >= 80 ? '#00ff88' : 
                                                   successRate >= 60 ? '#ffaa00' : '#ff3366';
        } else {
            this.elements.successRate.textContent = '-';
        }
    }
    
    addLogEntry(message, type = '') {
        const logEntry = document.createElement('div');
        logEntry.className = `history-item ${type}`;
        
        const time = new Date().toLocaleTimeString();
        logEntry.innerHTML = `
            <div class="history-time">${time}</div>
            <div class="history-text">${message}</div>
        `;
        
        this.elements.commandHistory.insertBefore(
            logEntry, 
            this.elements.commandHistory.firstChild
        );
        
        while (this.elements.commandHistory.children.length > 10) {
            this.elements.commandHistory.removeChild(
                this.elements.commandHistory.lastChild
            );
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VoiceCommandSystem();
});

// Add CSS for audio playback button
const audioButtonStyle = document.createElement('style');
audioButtonStyle.textContent = `
    .audio-playback-button {
        background: linear-gradient(135deg, #00ff88 0%, #00ffff 100%);
        border: none;
        padding: 12px 24px;
        border-radius: 25px;
        color: #000;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 12px;
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
    }
    
    .audio-playback-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 255, 136, 0.4);
        filter: brightness(1.1);
    }
    
    .audio-playback-button:active {
        transform: translateY(0);
    }
    
    .audio-playback-button i {
        font-size: 1rem;
    }
    
    .status-indicator-voice.speaking .status-dot {
        background: #00ff88;
        animation: speakingPulse 0.8s ease-in-out infinite;
    }
    
    @keyframes speakingPulse {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        50% { 
            opacity: 0.7; 
            transform: scale(1.3);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
        }
    }
`;
document.head.appendChild(audioButtonStyle);