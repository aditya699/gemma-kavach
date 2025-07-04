// Voice Command System - Complete JavaScript

class VoiceCommandSystem {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.speechSynthesis = window.speechSynthesis;
        this.currentZone = null;
        this.commandCount = 0;
        this.successCount = 0;

        
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
        this.addLogEntry('🎤 Voice command system initialized', 'success');
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
            // Allow Escape key to stop recording
            if (e.code === 'Escape' && this.isRecording) {
                e.preventDefault();
                this.stopRecording();
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (e.code === 'Space' && e.ctrlKey && this.isRecording) {
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
                this.updateConnectionStatus(true);
                this.elements.databaseStatus.textContent = 'Connected';
                this.elements.databaseStatus.style.color = '#00ff88';
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
        // Reset button to original state
        this.elements.voiceButton.innerHTML = `
            <div class="button-inner">
                <i class="fas fa-microphone"></i>
            </div>
            <div class="pulse-ring"></div>
            <div class="pulse-ring-2"></div>
        `;
        
        // Reset styles
        this.elements.voiceButton.style.background = '';
        this.elements.voiceButton.style.boxShadow = '';
    }
    
    async convertToWav(audioBlob) {
        return new Promise((resolve, reject) => {
            try {
                // Create audio context for conversion
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const fileReader = new FileReader();
                
                fileReader.onload = async (e) => {
                    try {
                        // Decode audio data
                        const arrayBuffer = e.target.result;
                        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                        
                        // Convert to WAV format
                        const wavBuffer = this.audioBufferToWav(audioBuffer);
                        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
                        
                        resolve(wavBlob);
                    } catch (decodeError) {
                        reject(decodeError);
                    }
                };
                
                fileReader.onerror = () => reject(new Error('Failed to read audio file'));
                fileReader.readAsArrayBuffer(audioBlob);
                
            } catch (error) {
                reject(error);
            }
        });
    }
    
    audioBufferToWav(buffer) {
        const length = buffer.length;
        const sampleRate = buffer.sampleRate;
        const arrayBuffer = new ArrayBuffer(44 + length * 2);
        const view = new DataView(arrayBuffer);
        
        // WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
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
            // Don't show modal immediately - let user see the stop button
            
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000  // Use 16kHz for better transcription compatibility
                }
            });
            
            // Try to use WAV format if supported, otherwise fall back to WebM
            let mimeType = 'audio/webm;codecs=opus';
            if (MediaRecorder.isTypeSupported('audio/wav')) {
                mimeType = 'audio/wav';
            } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=pcm')) {
                mimeType = 'audio/webm;codecs=pcm';
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
            
            // Update UI to show stop button
            this.elements.voiceButton.classList.add('recording');
            this.elements.voiceButton.classList.add('clicked');
            
            // Change button to show stop option - make it very clear
            this.elements.voiceButton.innerHTML = `
                <div class="button-inner stop-recording">
                    <i class="fas fa-stop"></i>
                </div>
                <div class="pulse-ring active"></div>
                <div class="pulse-ring-2 active"></div>
            `;
            
            // Make the button clearly indicate it's recording and can be stopped
            this.elements.voiceButton.style.background = 'linear-gradient(135deg, #ff3366 0%, #ff6b9d 100%)';
            this.elements.voiceButton.style.boxShadow = '0 0 30px rgba(255, 51, 102, 0.6)';
            
            this.updateVoiceStatus('listening', '🔴 RECORDING - Click red STOP button or press ESC');
            this.addLogEntry('🎤 Started recording - Click red STOP button or press ESC to finish', 'success');
            
            // Remove clicked class after animation
            setTimeout(() => {
                this.elements.voiceButton.classList.remove('clicked');
            }, 600);
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.hideProcessingModal();
            this.updateVoiceStatus('error', 'Recording failed');
            this.addLogEntry('❌ Recording failed: ' + error.message, 'error');
        }
    }
    
    // Simple toggle recording method
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
        
        // Reset UI immediately
        this.elements.voiceButton.classList.remove('recording');
        this.resetVoiceButton();
        
        // Now show processing modal
        this.showProcessingModal('Processing...', 'Analyzing your voice command');
        this.updateVoiceStatus('processing', 'Processing...');
        
        this.addLogEntry('🎤 Stopped recording', 'success');
    }
    
    async processAudio() {
        try {
            console.log('📤 Processing audio chunks:', this.audioChunks.length);
            
            // Create audio blob from recorded chunks
            let audioBlob = new Blob(this.audioChunks, { type: this.audioChunks[0]?.type || 'audio/webm' });
            console.log('🎵 Audio blob size:', audioBlob.size, 'bytes, type:', audioBlob.type);
            
            // Verify we have actual audio data
            if (audioBlob.size < 1000) { // Less than 1KB suggests no real audio
                throw new Error('Recording too short or no audio detected');
            }
            
            // Try to convert to WAV format for better server compatibility
            try {
                audioBlob = await this.convertToWav(audioBlob);
                console.log('✅ Converted to WAV format');
            } catch (convError) {
                console.log('⚠️ Could not convert to WAV, using original format:', convError);
            }
            
            const formData = new FormData();
            const fileName = audioBlob.type.includes('wav') ? 'voice-command.wav' : 'voice-command.webm';
            formData.append('audio', audioBlob, fileName);
            
            this.updateProcessingModal('Uploading...', 'Sending audio to AI system');
            
            console.log('📡 Sending audio to server...');
            const response = await fetch('/api/voice-command', {
                method: 'POST',
                body: formData,
                timeout: 120000 // 2 minute timeout
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Server response error:', response.status, errorText);
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
                this.currentResponse = result.hindi_message;
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
            
        } else {
            this.handleVoiceError(result.message || 'Command processing failed');
        }
        
        this.updateStats();
        
        // Reset status after 3 seconds
        setTimeout(() => {
            this.updateVoiceStatus('ready', 'Click to start recording');
            this.elements.voiceFeedback.classList.remove('success-flash');
            this.resetVoiceButton();
        }, 3000);
    }
    
    handleVoiceError(errorMessage) {
        this.hideProcessingModal();
        this.commandCount++;
        
        this.updateVoiceStatus('error', errorMessage);
        this.addLogEntry(`❌ Voice command failed: ${errorMessage}`, 'error');
        
        // Show error feedback
        this.elements.voiceFeedback.classList.add('error-shake');
        
        // Reset status after 3 seconds
        setTimeout(() => {
            this.updateVoiceStatus('ready', 'Click to start recording');
            this.elements.voiceFeedback.classList.remove('error-shake');
            this.resetVoiceButton();
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
        
        // Highlight the zone in the grid
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
        
        // Keep only last 10 entries
        while (this.elements.commandHistory.children.length > 10) {
            this.elements.commandHistory.removeChild(
                this.elements.commandHistory.lastChild
            );
        }
    }
}

// Initialize the voice command system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VoiceCommandSystem();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Add any cleanup if needed when page becomes hidden
        console.log('Page hidden - cleaning up...');
    }
});

// Add CSS class for selected zone
const style = document.createElement('style');
style.textContent = `
    .zone-item.selected {
        border-color: #00ffff !important;
        background: rgba(0, 255, 255, 0.1) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 255, 255, 0.3) !important;
    }
    
    .zone-item.selected .zone-letter {
        color: #ffff00 !important;
        text-shadow: 0 0 15px rgba(255, 255, 0, 0.5);
    }
`;
document.head.appendChild(style);