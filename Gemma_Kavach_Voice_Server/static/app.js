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
        this.debugMobileSupport();
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
            // Check MediaRecorder support first
            if (!window.MediaRecorder) {
                throw new Error('MediaRecorder not supported on this browser');
            }
            
            // Test basic audio recording capability
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Test if we can create a MediaRecorder with supported format
            const supportedTypes = [
                'audio/mp4',                  // iOS Safari REQUIRED
                'audio/mp4;codecs=mp4a.40.2', // iOS Safari with codec
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/wav',
                'audio/ogg;codecs=opus',
                'audio/mpeg'
            ];
            
            let hasSupport = false;
            for (const type of supportedTypes) {
                if (MediaRecorder.isTypeSupported(type)) {
                    hasSupport = true;
                    console.log('✅ Supported audio format found:', type);
                    break;
                }
            }
            
            if (!hasSupport) {
                throw new Error('No supported audio formats found');
            }
            
            stream.getTracks().forEach(track => track.stop());
            this.updateVoiceStatus('ready', 'Click to start recording');
            this.elements.voiceEngineStatus.textContent = 'Ready';
            this.elements.voiceEngineStatus.style.color = '#00ff88';
            this.addLogEntry('🎤 Microphone access granted', 'success');
            
                    // Add mobile-specific guidance
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        
        if (isMobile) {
            this.addLogEntry('📱 Mobile browser detected - using optimized settings', 'info');
            // Show mobile notice
            const mobileNotice = document.getElementById('mobileNotice');
            if (mobileNotice) {
                mobileNotice.style.display = 'block';
            }
        }
        
        if (isIOS) {
            this.addLogEntry('🍎 iOS device detected - audio playback requires user interaction', 'info');
            // Show iOS notice
            const iosNotice = document.getElementById('iosNotice');
            if (iosNotice) {
                iosNotice.style.display = 'block';
                
                // Add iOS audio test functionality
                const iosAudioTest = document.getElementById('iosAudioTest');
                if (iosAudioTest) {
                    iosAudioTest.addEventListener('click', () => {
                        this.testIOSAudio();
                    });
                }
            }
        }
            
        } catch (error) {
            console.error('Microphone permission denied:', error);
            this.updateVoiceStatus('error', 'Microphone access required');
            this.elements.voiceButton.disabled = true;
            this.elements.voiceEngineStatus.textContent = 'No Access';
            this.elements.voiceEngineStatus.style.color = '#ff3366';
            this.addLogEntry('❌ Microphone access denied: ' + error.message, 'error');
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
                // Mobile-friendly AudioContext creation
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (!AudioContextClass) {
                    reject(new Error('AudioContext not supported'));
                    return;
                }
                
                // Create AudioContext with fallback options for mobile
                let audioContext;
                try {
                    // Try with specific sample rate first
                    audioContext = new AudioContextClass({ sampleRate: 16000 });
                } catch (e) {
                    // Fallback to default settings for mobile compatibility
                    console.log('⚠️ Creating AudioContext with default settings for mobile');
                    audioContext = new AudioContextClass();
                }
                
                const fileReader = new FileReader();
                
                fileReader.onload = async (e) => {
                    try {
                        const arrayBuffer = e.target.result;
                        
                        // Decode audio with timeout for mobile
                        const audioBuffer = await Promise.race([
                            audioContext.decodeAudioData(arrayBuffer),
                            new Promise((_, reject) => 
                                setTimeout(() => reject(new Error('Decode timeout')), 10000)
                            )
                        ]);
                        
                        // Convert to WAV with proper format
                        const wavBuffer = this.audioBufferToWav(audioBuffer);
                        const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
                        
                        // Clean up AudioContext
                        if (audioContext.state !== 'closed') {
                            audioContext.close();
                        }
                        
                        resolve(wavBlob);
                    } catch (decodeError) {
                        // Clean up AudioContext on error
                        if (audioContext.state !== 'closed') {
                            audioContext.close();
                        }
                        reject(new Error(`Audio decode failed: ${decodeError.message}`));
                    }
                };
                
                fileReader.onerror = () => {
                    if (audioContext.state !== 'closed') {
                        audioContext.close();
                    }
                    reject(new Error('Failed to read audio file'));
                };
                
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
        
        // Convert float samples to 16-bit PCM with bounds checking
        const channelData = buffer.getChannelData(0);
        let offset = 44;
        
        for (let i = 0; i < length; i++) {
            // Clamp sample to [-1, 1] range and convert to 16-bit
            let sample = Math.max(-1, Math.min(1, channelData[i]));
            sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
            view.setInt16(offset, sample, true);
            offset += 2;
        }
        
        return arrayBuffer;
    }
    
    async startRecording() {
        if (this.isRecording || this.elements.voiceButton.disabled) return;
        
        try {
            this.audioChunks = [];
            
            // Mobile-optimized audio constraints
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            const audioConstraints = {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                channelCount: 1     // Mono audio for better compatibility
            };
            
            // Only set sampleRate on desktop browsers (mobile may not support it)
            if (!isMobile) {
                audioConstraints.sampleRate = 16000;
            }
            
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: audioConstraints
            });
            
            // Mobile-friendly mimeType detection with fallbacks
            let mimeType = 'audio/mp4';  // Default fallback (iPhone compatible)
            
            // Priority order for mobile compatibility - iPhone first
            const supportedTypes = [
                'audio/mp4',                  // iOS Safari REQUIRED
                'audio/mp4;codecs=mp4a.40.2', // iOS Safari with codec
                'audio/webm;codecs=opus',     // Android/Desktop
                'audio/webm',                 // Generic WebM
                'audio/wav',                  // Desktop browsers
                'audio/ogg;codecs=opus',      // Alternative
                'audio/mpeg'                  // Last resort
            ];
            
            // Find the first supported type
            for (const type of supportedTypes) {
                if (MediaRecorder.isTypeSupported(type)) {
                    mimeType = type;
                    break;
                }
            }
            
            console.log('🎵 Using audio format:', mimeType);
            
            // Create MediaRecorder with error handling
            try {
                this.mediaRecorder = new MediaRecorder(stream, { mimeType });
            } catch (mimeError) {
                console.warn('❌ Failed to create MediaRecorder with', mimeType, ':', mimeError.message);
                // Fallback to basic MediaRecorder without mimeType specification
                this.mediaRecorder = new MediaRecorder(stream);
                console.log('🔄 Using default MediaRecorder format');
            }
            
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
                type: this.audioChunks[0]?.type || 'audio/mp4' 
            });
            
            console.log('🎵 Original audio:', audioBlob.size, 'bytes, type:', audioBlob.type);
            
            if (audioBlob.size < 500) {  // Lower threshold for mobile
                throw new Error('Recording too short or no audio detected');
            }
            
            // Determine file extension based on MIME type
            let fileExtension = 'mp4';  // Default for iPhone
            if (audioBlob.type.includes('mp4')) {
                fileExtension = 'mp4';
            } else if (audioBlob.type.includes('wav')) {
                fileExtension = 'wav';
            } else if (audioBlob.type.includes('webm')) {
                fileExtension = 'webm';
            } else if (audioBlob.type.includes('ogg')) {
                fileExtension = 'ogg';
            } else if (audioBlob.type.includes('mpeg')) {
                fileExtension = 'mp3';
            }
            
            // Try WAV conversion for better server compatibility (all browsers)
            if (!audioBlob.type.includes('wav')) {
                try {
                    console.log('🔄 Converting to WAV format for better server compatibility...');
                    const originalSize = audioBlob.size;
                    const originalType = audioBlob.type;
                    
                    audioBlob = await this.convertToWav(audioBlob);
                    fileExtension = 'wav';
                    
                    console.log('✅ Converted to WAV format:');
                    console.log(`  Original: ${originalSize} bytes (${originalType})`);
                    console.log(`  Converted: ${audioBlob.size} bytes (audio/wav)`);
                    
                    this.addLogEntry(`🎵 Audio converted: ${originalType} → WAV`, 'success');
                    
                } catch (convError) {
                    console.log('⚠️ WAV conversion failed, using original format:', convError.message);
                    console.log('📤 Server should still be able to process', audioBlob.type);
                    
                    // For iPhone MP4, this is actually fine - server can handle MP4
                    if (audioBlob.type.includes('mp4')) {
                        this.addLogEntry(`📱 Using iPhone MP4 format (server compatible)`, 'success');
                    } else {
                        this.addLogEntry(`⚠️ WAV conversion failed, using ${audioBlob.type}`, 'info');
                    }
                }
            } else {
                console.log('✅ Audio already in WAV format');
                this.addLogEntry('✅ Audio already in WAV format', 'success');
            }
            
            const formData = new FormData();
            const fileName = `voice-command.${fileExtension}`;
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
    
    // Play audio from base64 encoded content - iPhone compatible
    async playAudioResponse(base64Audio) {
        try {
            console.log('🎵 playAudioResponse called');
            console.log('📦 Base64 audio length:', base64Audio ? base64Audio.length : 'null');
            console.log('🌐 User Agent:', navigator.userAgent);
            console.log('📱 Device Info:', {
                platform: navigator.platform,
                language: navigator.language,
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine
            });
            
            if (!base64Audio) {
                console.log('❌ No audio content to play');
                this.addLogEntry('❌ No audio content received', 'error');
                return;
            }
            
            console.log('🎵 Preparing audio response...');
            this.addLogEntry('🎵 Preparing audio response...', 'info');
            
            // Convert base64 to blob
            console.log('🔄 Converting base64 to audio blob...');
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            const audioBlob = new Blob([bytes], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(audioBlob);
            console.log('✅ Audio blob created:', {
                size: audioBlob.size,
                type: audioBlob.type,
                url: audioUrl
            });
            
            // Stop any currently playing audio
            if (this.audioPlayer) {
                console.log('⏹️ Stopping current audio player');
                this.audioPlayer.pause();
                this.audioPlayer = null;
            }
            
            // Create new audio element
            console.log('🎵 Creating new audio element...');
            this.audioPlayer = new Audio(audioUrl);
            
            // iPhone Safari requires user interaction - don't auto-play
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
            const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
            
            // Configure audio player for iOS/Safari
            if (isIOS || isSafari) {
                console.log('🍎 Configuring audio player for iOS/Safari');
                this.audioPlayer.playsInline = true;
                this.audioPlayer.preload = 'none';
                this.audioPlayer.crossOrigin = 'anonymous';
                console.log('✅ iOS/Safari audio configuration applied:', {
                    playsInline: this.audioPlayer.playsInline,
                    preload: this.audioPlayer.preload,
                    crossOrigin: this.audioPlayer.crossOrigin
                });
            } else {
                console.log('🖥️ Using standard audio configuration for non-iOS browser');
            }
            
            // Set up event listeners
            console.log('🔗 Setting up audio event listeners...');
            this.audioPlayer.onplay = () => {
                console.log('▶️ Audio play event triggered');
                this.updateVoiceStatus('speaking', '🔊 Playing response...');
                this.addLogEntry('🎵 Playing audio response', 'success');
            };
            
            this.audioPlayer.onended = () => {
                console.log('⏹️ Audio ended event triggered');
                URL.revokeObjectURL(audioUrl);
                this.updateVoiceStatus('ready', 'Click to start recording');
                console.log('✅ Audio playback completed');
            };
            
            this.audioPlayer.onloadstart = () => {
                console.log('🔄 Audio load start event triggered');
            };
            
            this.audioPlayer.oncanplay = () => {
                console.log('✅ Audio can play event triggered');
            };
            
            this.audioPlayer.onwaiting = () => {
                console.log('⏳ Audio waiting event triggered');
            };
            
            this.audioPlayer.onerror = (error) => {
                console.error('❌ Audio error event triggered:', error);
                console.error('Audio error details:', {
                    error: error.target.error,
                    networkState: error.target.networkState,
                    readyState: error.target.readyState,
                    src: error.target.src,
                    currentTime: error.target.currentTime,
                    duration: error.target.duration,
                    paused: error.target.paused,
                    muted: error.target.muted,
                    volume: error.target.volume
                });
                URL.revokeObjectURL(audioUrl);
                this.updateVoiceStatus('ready', 'Click to start recording');
                this.addLogEntry('❌ Audio playback failed', 'error');
            };
            
            // Always show play button for iOS/Safari, try auto-play for others
            if (isIOS || isSafari) {
                // For iOS/Safari, always show a play button
                this.showPlayButton(audioUrl);
                this.addLogEntry('📱 Audio ready - tap play button (iOS/Safari)', 'info');
            } else {
                // For other browsers, try to auto-play
                try {
                    await this.audioPlayer.play();
                } catch (playError) {
                    console.log('Auto-play blocked, showing play button:', playError.message);
                    this.showPlayButton(audioUrl);
                    this.addLogEntry('🔘 Auto-play blocked - tap play button', 'info');
                }
            }
            
        } catch (error) {
            console.error('Error preparing audio:', error);
            this.addLogEntry('❌ Audio preparation error: ' + error.message, 'error');
        }
    }
    
    // Show play button for iOS audio playback
    showPlayButton(audioUrl) {
        // Remove existing play button if any
        const existingButton = document.querySelector('.ios-play-button');
        if (existingButton) {
            existingButton.remove();
        }
        
        // Create play button
        const playButton = document.createElement('button');
        playButton.className = 'ios-play-button';
        playButton.innerHTML = '🔊 Play Audio Response';
        
        // Style the button
        playButton.style.cssText = `
            background: linear-gradient(135deg, #00ff88 0%, #00ffff 100%);
            border: none;
            padding: 15px 25px;
            border-radius: 25px;
            color: #000;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            margin: 15px 0;
            width: 100%;
            max-width: 300px;
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
            transition: all 0.3s ease;
        `;
        
        // Add click handler
        playButton.addEventListener('click', async () => {
            try {
                playButton.textContent = '🔊 Playing...';
                playButton.disabled = true;
                
                // Create new audio element for user-triggered playback
                const audio = new Audio(audioUrl);
                
                // Configure for iOS/Safari
                const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
                const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
                
                if (isIOS || isSafari) {
                    audio.playsInline = true;
                    audio.preload = 'none';
                    audio.crossOrigin = 'anonymous';
                    console.log('🍎 Configuring audio for iOS/Safari');
                }
                
                audio.onplay = () => {
                    this.updateVoiceStatus('speaking', '🔊 Playing response...');
                    this.addLogEntry('🎵 Playing audio response', 'success');
                };
                
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                    this.updateVoiceStatus('ready', 'Click to start recording');
                    playButton.remove();
                    console.log('✅ Audio playback completed');
                };
                
                audio.onerror = (error) => {
                    console.error('Audio playback error:', error);
                    console.error('Audio error details:', {
                        error: error.target.error,
                        networkState: error.target.networkState,
                        readyState: error.target.readyState,
                        src: error.target.src
                    });
                    URL.revokeObjectURL(audioUrl);
                    this.updateVoiceStatus('ready', 'Click to start recording');
                    playButton.textContent = '❌ Playback Failed';
                    setTimeout(() => playButton.remove(), 2000);
                };
                
                // Force load for iOS/Safari
                if (isIOS || isSafari) {
                    audio.load();
                    // Wait a bit for the audio to be ready
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                
                await audio.play();
                
            } catch (error) {
                console.error('Play button error:', error);
                console.error('Play button error details:', {
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                });
                
                // More specific error messages for iOS
                if (error.name === 'NotAllowedError') {
                    playButton.textContent = '❌ Check Volume/Silent Mode';
                    this.addLogEntry('❌ Audio blocked - check iPhone volume and silent mode', 'error');
                } else if (error.name === 'NotSupportedError') {
                    playButton.textContent = '❌ Format Not Supported';
                    this.addLogEntry('❌ Audio format not supported on this device', 'error');
                } else {
                    playButton.textContent = '❌ Playback Failed';
                    this.addLogEntry('❌ Audio playback failed: ' + error.message, 'error');
                }
                
                setTimeout(() => playButton.remove(), 3000);
            }
        });
        
        // Add to response section
        const responseSection = this.elements.responseSection;
        if (responseSection) {
            responseSection.appendChild(playButton);
        }
    }

    handleVoiceResponse(result) {
        this.hideProcessingModal();
        this.commandCount++;
        
        console.log('📨 Voice response received:', {
            success: result.success,
            transcription: result.transcription ? 'present' : 'missing',
            hindi_message: result.hindi_message ? 'present' : 'missing',
            audio_content: result.audio_content ? `present (${result.audio_content.length} chars)` : 'missing',
            zone: result.zone
        });
        
        if (result.success) {
            this.successCount++;
            
            // Show transcription
            if (result.transcription) {
                this.elements.transcriptionText.textContent = result.transcription;
                this.elements.transcriptionSection.style.display = 'block';
                console.log('✅ Transcription displayed');
            }
            
            // Show response
            if (result.hindi_message) {
                this.elements.responseText.textContent = result.hindi_message;
                this.elements.responseSection.style.display = 'block';
                console.log('✅ Hindi message displayed');
                
                // Add audio playback button
                console.log('🔘 Adding audio playback button...');
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
        console.log('🔘 addAudioPlaybackButton called');
        console.log('📝 Text length:', text ? text.length : 'null');
        console.log('🎵 Audio content length:', audioContent ? audioContent.length : 'null');
        
        // Remove existing audio button if any
        const existingButton = this.elements.responseSection.querySelector('.audio-playback-button');
        if (existingButton) {
            console.log('🗑️ Removing existing audio button');
            existingButton.remove();
        }
        
        if (audioContent) {
            console.log('✅ Creating audio playback button');
            const audioButton = document.createElement('button');
            audioButton.className = 'audio-playback-button';
            audioButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
            
            console.log('🔘 Audio button created, adding click listener...');
            
            audioButton.addEventListener('click', async () => {
                try {
                    // Simple visual feedback first
                    audioButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                    audioButton.disabled = true;
                    
                    if (!audioContent) {
                        throw new Error('No audio content available');
                    }
                    
                    // Convert base64 to blob - simplified
                    const binaryString = atob(audioContent);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    
                    // iPhone-specific audio handling
                    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
                    const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
                    
                    // Use MP3 format for better iOS compatibility
                    const mimeType = 'audio/mpeg';
                    const audioBlob = new Blob([bytes], { type: mimeType });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Create audio element with iPhone-compatible settings
                    const audio = new Audio();
                    
                    // iOS/Safari specific configuration
                    if (isIOS || isSafari) {
                        audio.controls = false;
                        audio.autoplay = false;
                        audio.preload = 'none'; // Changed from 'metadata' to 'none' for iOS
                        audio.crossOrigin = 'anonymous';
                        audio.playsInline = true; // Prevent fullscreen playback on iOS
                    } else {
                        audio.preload = 'auto';
                    }
                    
                    audio.src = audioUrl;
                    
                    audioButton.innerHTML = '<i class="fas fa-pause"></i> Playing...';
                    
                    // Show visual feedback in the UI
                    this.addLogEntry('🔘 Playing audio response...', 'info');
                    
                    audio.onloadstart = () => {
                        console.log('🔄 Audio loading started');
                        this.addLogEntry('🔄 Audio loading started', 'info');
                    };
                    
                    audio.oncanplay = () => {
                        console.log('✅ Audio can play');
                        this.addLogEntry('✅ Audio ready to play', 'success');
                    };
                    
                    audio.onplay = () => {
                        console.log('▶️ Audio started playing');
                        this.updateVoiceStatus('speaking', '🔊 Playing response...');
                        this.addLogEntry('🎵 Playing audio response', 'success');
                    };
                    
                    audio.onended = () => {
                        console.log('⏹️ Audio playback ended');
                        URL.revokeObjectURL(audioUrl);
                        this.updateVoiceStatus('ready', 'Click to start recording');
                        audioButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                        audioButton.disabled = false;
                        this.addLogEntry('✅ Audio playback completed', 'success');
                    };
                    
                    audio.onerror = (error) => {
                        console.error('❌ Audio playback error:', error);
                        console.error('❌ Audio error details:', {
                            error: error.target.error,
                            networkState: error.target.networkState,
                            readyState: error.target.readyState,
                            src: error.target.src
                        });
                        URL.revokeObjectURL(audioUrl);
                        this.updateVoiceStatus('ready', 'Click to start recording');
                        audioButton.innerHTML = '<i class="fas fa-exclamation"></i> Failed';
                        this.addLogEntry('❌ Audio playback failed', 'error');
                        setTimeout(() => {
                            audioButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                            audioButton.disabled = false;
                        }, 2000);
                    };
                    
                    audio.onpause = () => {
                        console.log('⏸️ Audio paused');
                    };
                    
                    audio.onwaiting = () => {
                        console.log('⏳ Audio waiting for data');
                    };
                    
                    // iPhone-specific play method
                    if (isIOS || isSafari) {
                        // For iPhone/Safari, we need to ensure the audio is ready
                        console.log('🍎 iOS/Safari detected - using optimized playback');
                        
                        // Force load the audio first
                        audio.load();
                        
                        // Add a small delay to ensure the audio is loaded
                        setTimeout(async () => {
                            try {
                                // Check if audio is ready
                                if (audio.readyState < 2) {
                                    console.log('⏳ Audio not ready, waiting...');
                                    await new Promise(resolve => {
                                        audio.addEventListener('canplay', resolve, { once: true });
                                        audio.addEventListener('error', resolve, { once: true });
                                    });
                                }
                                
                                // Attempt to play
                                console.log('▶️ Attempting to play audio on iOS/Safari');
                                await audio.play();
                                
                            } catch (iosError) {
                                console.log('iOS play failed:', iosError);
                                console.log('Error details:', {
                                    name: iosError.name,
                                    message: iosError.message,
                                    readyState: audio.readyState,
                                    networkState: audio.networkState,
                                    paused: audio.paused,
                                    muted: audio.muted,
                                    volume: audio.volume
                                });
                                
                                // Check if it's a silent mode issue
                                if (iosError.name === 'NotAllowedError') {
                                    this.addLogEntry('❌ iPhone audio blocked - check volume/silent mode', 'error');
                                    audioButton.innerHTML = '<i class="fas fa-volume-mute"></i> Check Volume & Silent Mode';
                                } else {
                                    this.addLogEntry('❌ iPhone audio error: ' + iosError.message, 'error');
                                    audioButton.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Audio Error';
                                }
                                
                                setTimeout(() => {
                                    audioButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                                    audioButton.disabled = false;
                                }, 4000);
                            }
                        }, 200); // Increased delay for iOS
                    } else {
                        // Standard playback for other browsers
                        await audio.play();
                    }
                    
                } catch (error) {
                    console.error('Audio button error:', error);
                    audioButton.innerHTML = '<i class="fas fa-exclamation"></i> Failed';
                    setTimeout(() => {
                        audioButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                        audioButton.disabled = false;
                    }, 2000);
                }
            });
            
            console.log('➕ Appending audio button to response section');
            this.elements.responseSection.appendChild(audioButton);
            console.log('✅ Audio button added successfully');
            this.addLogEntry('🔘 Audio play button added', 'success');
        } else {
            console.log('❌ No audio content provided, not creating button');
            this.addLogEntry('❌ No audio content for playback button', 'warning');
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
    
    debugMobileSupport() {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        console.log('📱 Mobile Detection:', isMobile);
        console.log('🎵 MediaRecorder Support:', !!window.MediaRecorder);
        console.log('🎤 getUserMedia Support:', !!navigator.mediaDevices?.getUserMedia);
        
        if (window.MediaRecorder) {
            const testTypes = [
                'audio/mp4',                  // iOS Safari REQUIRED
                'audio/mp4;codecs=mp4a.40.2', // iOS Safari with codec
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/wav',
                'audio/ogg;codecs=opus',
                'audio/mpeg'
            ];
            
            console.log('🎵 Supported Audio Formats:');
            testTypes.forEach(type => {
                const supported = MediaRecorder.isTypeSupported(type);
                console.log(`  ${type}: ${supported ? '✅' : '❌'}`);
            });
        }
        
        // Log browser and device info
        console.log('🌐 User Agent:', navigator.userAgent);
        console.log('🔧 Browser Info:', {
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine
        });
        
        // Test WAV conversion capability
        this.testWavConversion();
    }
    
    async testWavConversion() {
        try {
            // Create a small test audio buffer
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) {
                console.log('❌ AudioContext not available - WAV conversion will fail');
                return;
            }
            
            const audioContext = new AudioContextClass();
            const testBuffer = audioContext.createBuffer(1, 1024, 16000);
            
            // Fill with test data
            const channelData = testBuffer.getChannelData(0);
            for (let i = 0; i < channelData.length; i++) {
                channelData[i] = Math.sin(2 * Math.PI * 440 * i / 16000) * 0.1; // 440Hz tone
            }
            
            // Test WAV conversion
            const wavBuffer = this.audioBufferToWav(testBuffer);
            const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
            
            console.log('✅ WAV conversion test passed:', wavBlob.size, 'bytes');
            audioContext.close();
            
        } catch (error) {
            console.log('❌ WAV conversion test failed:', error.message);
            console.log('⚠️ Audio will be sent in original format to server');
        }
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
    
    async testIOSAudio() {
        const testButton = document.getElementById('iosAudioTest');
        const originalText = testButton.textContent;
        
        try {
            testButton.textContent = '🔄 Testing...';
            testButton.disabled = true;
            
            this.addLogEntry('🧪 Testing iOS audio capability...', 'info');
            
            // Create a simple test tone using Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 440; // A4 note
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1; // Low volume
            
            // Check if audio context is suspended (iOS requirement)
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }
            
            // Play for 0.5 seconds
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.5);
            
            // Wait for the tone to finish
            await new Promise(resolve => setTimeout(resolve, 600));
            
            testButton.textContent = '✅ Audio Works';
            testButton.style.background = '#00C851';
            this.addLogEntry('✅ iOS audio test successful - audio should work', 'success');
            
            setTimeout(() => {
                testButton.textContent = originalText;
                testButton.style.background = '#007AFF';
                testButton.disabled = false;
            }, 2000);
            
        } catch (error) {
            console.error('iOS audio test failed:', error);
            
            testButton.textContent = '❌ Audio Blocked';
            testButton.style.background = '#FF3B30';
            
            if (error.name === 'NotAllowedError') {
                this.addLogEntry('❌ Audio blocked - check iPhone silent mode and volume', 'error');
            } else if (error.name === 'NotSupportedError') {
                this.addLogEntry('❌ Audio not supported on this device', 'error');
            } else {
                this.addLogEntry('❌ iOS audio test failed: ' + error.message, 'error');
            }
            
            setTimeout(() => {
                testButton.textContent = originalText;
                testButton.style.background = '#007AFF';
                testButton.disabled = false;
            }, 3000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VoiceCommandSystem();
});

// Add CSS for audio playback button and mobile notice
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
    
    .mobile-notice {
        margin-top: 20px;
        padding: 16px;
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border: 1px solid rgba(79, 70, 229, 0.2);
        border-radius: 12px;
        animation: slideIn 0.5s ease-out;
    }
    
    .notice-content {
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }
    
    .notice-content i {
        color: #4F46E5;
        font-size: 1.2rem;
        margin-top: 2px;
    }
    
    .notice-text {
        flex: 1;
        color: #e2e8f0;
        line-height: 1.5;
    }
    
    .notice-text strong {
        color: #00ff88;
        display: block;
        margin-bottom: 4px;
    }
    
    .notice-text span {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
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