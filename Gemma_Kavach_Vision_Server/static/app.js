// Gemma Kavach Frontend JavaScript

class GemmaKavach {
    constructor() {
        this.sessionId = null;
        this.isMonitoring = false;
        this.captureInterval = null;
        this.sessionStartTime = null;
        this.frameCount = 0;
        
        this.videoElement = document.getElementById('videoElement');
        this.canvas = document.getElementById('captureCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkServerConnection();
    }
    
    initializeElements() {
        this.elements = {
            startBtn: document.getElementById('startBtn'),
            stopBtn: document.getElementById('stopBtn'),
            locationInput: document.getElementById('locationInput'),
            operatorInput: document.getElementById('operatorInput'),
            cameraOverlay: document.getElementById('cameraOverlay'),
            connectionStatus: document.getElementById('connectionStatus'),
            loadingModal: document.getElementById('loadingModal'),
            
            // Dashboard elements
            riskValue: document.getElementById('riskValue'),
            riskLabel: document.getElementById('riskLabel'),
            framesAnalyzed: document.getElementById('framesAnalyzed'),
            framesFlagged: document.getElementById('framesFlagged'),
            sessionTime: document.getElementById('sessionTime'),
            lastAnalysis: document.getElementById('lastAnalysis'),
            sessionId: document.getElementById('sessionId'),
            sessionLocation: document.getElementById('sessionLocation'),
            sessionStatus: document.getElementById('sessionStatus'),
            activityLog: document.getElementById('activityLog')
        };
    }
    
    setupEventListeners() {
        this.elements.startBtn.addEventListener('click', () => this.startMonitoring());
        this.elements.stopBtn.addEventListener('click', () => this.stopMonitoring());
    }
    
    async checkServerConnection() {
        try {
            const response = await fetch('/api/v1/monitoring/status');
            const data = await response.json();
            
            if (data.status === 'available') {
                this.updateConnectionStatus(true);
                this.addLogEntry('System ready for monitoring');
            } else {
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            console.error('Server connection failed:', error);
            this.updateConnectionStatus(false);
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
    
    async startMonitoring() {
        try {
            this.addLogEntry('Requesting camera access...');
            
            // Get camera access - prefer back camera on mobile, any camera on desktop
            let videoConstraints = { width: 640, height: 480 };
            
            // Try back camera first (better for crowd monitoring)
            try {
                videoConstraints.facingMode = "environment"; // Back camera
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: videoConstraints 
                });
                this.videoElement.srcObject = stream;
                this.addLogEntry('Using back camera (recommended for monitoring)');
            } catch (backCameraError) {
                // If back camera fails, try any available camera
                console.log('Back camera not available, trying default camera');
                delete videoConstraints.facingMode;
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: videoConstraints 
                });
                this.videoElement.srcObject = stream;
                this.addLogEntry('Using available camera');
            }
            
            this.elements.cameraOverlay.style.display = 'none';
            
            // Create session
            await this.createSession();
            
            // Start monitoring
            this.isMonitoring = true;
            this.sessionStartTime = Date.now();
            
            // Update UI
            this.elements.startBtn.disabled = true;
            this.elements.stopBtn.disabled = false;
            this.elements.sessionStatus.textContent = 'Monitoring';
            
            // Start session timer
            this.startSessionTimer();
            
            // Start capturing frames
            this.startFrameCapture();
            
            this.addLogEntry('Monitoring started successfully', 'safe');
            
        } catch (error) {
            console.error('Failed to start monitoring:', error);
            this.addLogEntry('Failed to start monitoring: ' + error.message, 'risk');
            alert('Failed to start monitoring. Please check camera permissions.');
        }
    }
    
    async createSession() {
        try {
            const response = await fetch('/api/v1/session/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    location: this.elements.locationInput.value,
                    operator_name: this.elements.operatorInput.value
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create session');
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            // Update UI
            this.elements.sessionId.textContent = this.sessionId;
            this.elements.sessionLocation.textContent = data.location;
            
            this.addLogEntry(`Session created: ${this.sessionId}`);
            
        } catch (error) {
            throw new Error('Session creation failed: ' + error.message);
        }
    }
    
    startFrameCapture() {
        // Capture frame every 2 seconds
        this.captureInterval = setInterval(() => {
            if (this.isMonitoring) {
                this.captureAndAnalyzeFrame();
            }
        }, 2000);
    }
    
    async captureAndAnalyzeFrame() {
        try {
            // Show loading modal
            this.elements.loadingModal.classList.add('show');
            
            // Capture frame from video
            this.canvas.width = this.videoElement.videoWidth;
            this.canvas.height = this.videoElement.videoHeight;
            this.ctx.drawImage(this.videoElement, 0, 0);
            
            // Convert to blob
            const blob = await new Promise(resolve => {
                this.canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });
            
            // Send to API
            const formData = new FormData();
            formData.append('frame', blob, 'frame.jpg');
            
            const response = await fetch(`/api/v1/session/${this.sessionId}/frame`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Frame analysis failed');
            }
            
            const result = await response.json();
            this.updateDashboard(result);
            
            // Hide loading modal
            this.elements.loadingModal.classList.remove('show');
            
        } catch (error) {
            console.error('Frame capture failed:', error);
            this.addLogEntry('Frame analysis failed: ' + error.message, 'risk');
            this.elements.loadingModal.classList.remove('show');
        }
    }
    
    updateDashboard(result) {
        // Update frame counts
        this.elements.framesAnalyzed.textContent = result.frames_analyzed;
        this.elements.framesFlagged.textContent = result.frames_flagged;
        
        // Update risk assessment
        const riskScore = Math.round(result.updated_risk_score);
        this.elements.riskValue.textContent = `${riskScore}%`;
        
        // Update risk circle and label
        const riskCircle = document.querySelector('.risk-circle');
        let verdict = 'SAFE';
        let riskClass = 'safe';
        
        if (riskScore > 75) {
            verdict = 'ALERT';
            riskClass = 'alert';
        } else if (riskScore > 30) {
            verdict = 'WATCH';
            riskClass = 'watch';
        }
        
        this.elements.riskLabel.textContent = verdict;
        riskCircle.className = `risk-circle ${riskClass}`;
        riskCircle.style.setProperty('--progress', `${riskScore}%`);
        
        // Update last analysis time
        const now = new Date().toLocaleTimeString();
        this.elements.lastAnalysis.textContent = now;
        
        // Add to activity log
        const logType = result.risk_detected ? 'risk' : 'safe';
        const logMessage = `Frame ${result.frame_number}: ${result.risk_detected ? 'RISK DETECTED' : 'Safe'} (${riskScore}%)`;
        this.addLogEntry(logMessage, logType);
        
        // Special handling for high risk
        if (verdict === 'ALERT') {
            this.addLogEntry('⚠️ HIGH RISK DETECTED - Email alert triggered', 'risk');
        }
    }
    
    startSessionTimer() {
        setInterval(() => {
            if (this.isMonitoring && this.sessionStartTime) {
                const elapsed = Date.now() - this.sessionStartTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                this.elements.sessionTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    stopMonitoring() {
        this.isMonitoring = false;
        
        // Stop camera
        if (this.videoElement.srcObject) {
            this.videoElement.srcObject.getTracks().forEach(track => track.stop());
            this.videoElement.srcObject = null;
        }
        
        // Stop capturing
        if (this.captureInterval) {
            clearInterval(this.captureInterval);
        }
        
        // Update UI
        this.elements.startBtn.disabled = false;
        this.elements.stopBtn.disabled = true;
        this.elements.sessionStatus.textContent = 'Stopped';
        this.elements.cameraOverlay.style.display = 'flex';
        
        this.addLogEntry('Monitoring stopped', 'safe');
    }
    
    addLogEntry(message, type = '') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-item ${type}`;
        
        const time = new Date().toLocaleTimeString();
        logEntry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message">${message}</span>
        `;
        
        this.elements.activityLog.insertBefore(logEntry, this.elements.activityLog.firstChild);
        
        // Keep only last 10 entries
        while (this.elements.activityLog.children.length > 10) {
            this.elements.activityLog.removeChild(this.elements.activityLog.lastChild);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GemmaKavach();
});