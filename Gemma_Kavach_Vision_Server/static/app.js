// Enhanced Gemma Kavach Frontend JavaScript - Dual Analysis Support

class GemmaKavach {
    constructor() {
        this.sessionId = null;
        this.isMonitoring = false;
        this.captureInterval = null;
        this.sessionStartTime = null;
        this.frameCount = 0;
        
        // Enhanced analytics tracking
        this.analytics = {
            densityStats: {"Low": 0, "Medium": 0, "High": 0, "Unknown": 0},
            motionStats: {"Calm": 0, "Chaotic": 0, "Unknown": 0},
            riskLevels: {"SAFE": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
        };
        
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
            activityLog: document.getElementById('activityLog'),
            
            // NEW: Enhanced analysis display elements
            currentDensity: document.getElementById('currentDensity'),
            currentMotion: document.getElementById('currentMotion'),
            riskLevel: document.getElementById('riskLevel'),
            analysisTime: document.getElementById('analysisTime'),
            
            // NEW: Analytics breakdown elements
            densityChart: document.getElementById('densityChart'),
            motionChart: document.getElementById('motionChart'),
            riskLevelChart: document.getElementById('riskLevelChart'),
            
            // NEW: Alert indicators
            alertIndicator: document.getElementById('alertIndicator'),
            criticalFramesCount: document.getElementById('criticalFramesCount')
        };
    }
    
    setupEventListeners() {
        this.elements.startBtn.addEventListener('click', () => this.startMonitoring());
        this.elements.stopBtn.addEventListener('click', () => this.stopMonitoring());
    }
    
    async checkServerConnection() {
        try {
            const response = await fetch('/api/monitoring/status');
            const data = await response.json();
            
            if (data.status === 'available') {
                this.updateConnectionStatus(true, data.analysis_type || 'dual_crowd_analysis');
                this.addLogEntry('System ready for dual crowd analysis');
            } else {
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            console.error('Server connection failed:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    updateConnectionStatus(connected, analysisType = null) {
        const statusEl = this.elements.connectionStatus;
        if (connected) {
            statusEl.className = 'status-indicator connected';
            statusEl.innerHTML = `<i class="fas fa-circle"></i><span>Connected</span>`;
            if (analysisType) {
                statusEl.title = `Analysis Type: ${analysisType}`;
            }
        } else {
            statusEl.className = 'status-indicator disconnected';
            statusEl.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
        }
    }
    
    async startMonitoring() {
        try {
            this.addLogEntry('🚀 Initializing dual-analysis monitoring...');
            
            // Get camera access
            let videoConstraints = { width: 640, height: 480 };
            
            try {
                videoConstraints.facingMode = "environment";
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: videoConstraints 
                });
                this.videoElement.srcObject = stream;
                this.addLogEntry('📹 Using back camera (optimal for crowd monitoring)');
            } catch (backCameraError) {
                delete videoConstraints.facingMode;
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: videoConstraints 
                });
                this.videoElement.srcObject = stream;
                this.addLogEntry('📹 Using available camera');
            }
            
            this.elements.cameraOverlay.style.display = 'none';
            
            // Create session
            await this.createSession();
            
            // Start monitoring
            this.isMonitoring = true;
            this.sessionStartTime = Date.now();
            
            // Reset analytics
            this.resetAnalytics();
            
            // Update UI
            this.elements.startBtn.disabled = true;
            this.elements.stopBtn.disabled = false;
            this.elements.sessionStatus.textContent = 'Monitoring';
            
            // Add monitoring class to risk circle for enhanced animations
            const riskCircle = document.querySelector('.risk-circle');
            if (riskCircle) {
                riskCircle.classList.add('monitoring');
            }
            
            this.startSessionTimer();
            this.startFrameCapture();
            
            this.addLogEntry('✅ Dual-analysis monitoring started successfully', 'safe');
            
        } catch (error) {
            console.error('Failed to start monitoring:', error);
            this.addLogEntry('❌ Failed to start monitoring: ' + error.message, 'risk');
            alert('Failed to start monitoring. Please check camera permissions.');
        }
    }
    
    resetAnalytics() {
        this.analytics = {
            densityStats: {"Low": 0, "Medium": 0, "High": 0, "Unknown": 0},
            motionStats: {"Calm": 0, "Chaotic": 0, "Unknown": 0},
            riskLevels: {"SAFE": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
        };
        this.updateAnalyticsDisplay();
    }
    
    async createSession() {
        try {
            const response = await fetch('/api/session/create', {
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
            
            this.addLogEntry(`🆔 Session created: ${this.sessionId}`, 'safe');
            
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
            // Show enhanced loading modal
            this.showAnalysisLoader();
            
            // Capture frame from video
            this.canvas.width = this.videoElement.videoWidth;
            this.canvas.height = this.videoElement.videoHeight;
            this.ctx.drawImage(this.videoElement, 0, 0);
            
            // Convert to blob
            const blob = await new Promise(resolve => {
                this.canvas.toBlob(resolve, 'image/jpeg', 0.8);
            });
            
            // Send to enhanced API
            const formData = new FormData();
            formData.append('frame', blob, 'frame.jpg');
            
            const analysisStart = performance.now();
            const response = await fetch(`/api/session/${this.sessionId}/frame`, {
                method: 'POST',
                body: formData
            });
            const analysisTime = (performance.now() - analysisStart) / 1000;
            
            if (!response.ok) {
                throw new Error('Frame analysis failed');
            }
            
            const result = await response.json();
            
            // Enhanced dashboard update with dual analysis data
            this.updateEnhancedDashboard(result, analysisTime);
            
            this.hideAnalysisLoader();
            
        } catch (error) {
            console.error('Frame capture failed:', error);
            this.addLogEntry('❌ Frame analysis failed: ' + error.message, 'risk');
            this.hideAnalysisLoader();
        }
    }
    
    showAnalysisLoader() {
        const modal = this.elements.loadingModal;
        modal.classList.add('show');
        
        // Enhanced loading text
        const modalContent = modal.querySelector('.modal-content p');
        if (modalContent) {
            modalContent.innerHTML = `
                Analyzing frame...<br>
                <small style="color: #00ffff; font-size: 0.8em;">
                    🧠 Crowd Density | 🏃 Motion Behavior
                </small>
            `;
        }
    }
    
    hideAnalysisLoader() {
        this.elements.loadingModal.classList.remove('show');
    }
    
    updateEnhancedDashboard(result, analysisTime) {
        // Update basic frame counts
        this.elements.framesAnalyzed.textContent = result.frames_analyzed;
        this.elements.framesFlagged.textContent = result.frames_flagged;
        
        // Update NEW dual analysis display
        if (this.elements.currentDensity) {
            this.elements.currentDensity.textContent = result.crowd_density;
            this.elements.currentDensity.className = `density-value ${result.crowd_density.toLowerCase()}`;
        }
        
        if (this.elements.currentMotion) {
            this.elements.currentMotion.textContent = result.crowd_motion;
            this.elements.currentMotion.className = `motion-value ${result.crowd_motion.toLowerCase()}`;
        }
        
        if (this.elements.riskLevel) {
            this.elements.riskLevel.textContent = result.risk_level;
            this.elements.riskLevel.className = `risk-level-value ${result.risk_level.toLowerCase()}`;
        }
        
        if (this.elements.analysisTime) {
            this.elements.analysisTime.textContent = `${analysisTime.toFixed(2)}s`;
        }
        
        // Enhanced risk assessment
        const riskScore = Math.round(result.updated_risk_score);
        this.elements.riskValue.textContent = `${riskScore}%`;
        
        // Enhanced risk circle and label with 4-level system
        const riskCircle = document.querySelector('.risk-circle');
        let verdict = this.getVerdictFromScore(riskScore);
        let riskClass = verdict.toLowerCase();
        
        this.elements.riskLabel.textContent = verdict;
        riskCircle.className = `risk-circle monitoring ${riskClass}`;
        riskCircle.style.setProperty('--progress', `${riskScore}%`);
        
        // Update analytics from detailed breakdown
        if (result.analysis_details) {
            this.updateLocalAnalytics(result.analysis_details);
        }
        
        // Enhanced last analysis time
        const now = new Date().toLocaleTimeString();
        this.elements.lastAnalysis.textContent = now;
        
        // Enhanced activity log with dual analysis info
        this.addEnhancedLogEntry(result, riskScore, analysisTime);
        
        // Check for alerts and critical frames
        this.updateAlertIndicators(result);
    }
    
    getVerdictFromScore(score) {
        if (score <= 15) return "SAFE";
        if (score <= 40) return "WATCH";  
        if (score <= 70) return "ALERT";
        return "CRITICAL";
    }
    
    updateLocalAnalytics(analysisDetails) {
        if (analysisDetails.density_breakdown) {
            this.analytics.densityStats = analysisDetails.density_breakdown;
        }
        if (analysisDetails.motion_breakdown) {
            this.analytics.motionStats = analysisDetails.motion_breakdown;
        }
        if (analysisDetails.risk_level_breakdown) {
            this.analytics.riskLevels = analysisDetails.risk_level_breakdown;
        }
        
        this.updateAnalyticsDisplay();
    }
    
    updateAnalyticsDisplay() {
        // Update density chart
        this.updateMiniChart('densityChart', this.analytics.densityStats, [
            '#00ff88', '#ffaa00', '#ff3366', '#666'  // Low, Medium, High, Unknown
        ]);
        
        // Update motion chart  
        this.updateMiniChart('motionChart', this.analytics.motionStats, [
            '#00ffff', '#ff3366', '#666'  // Calm, Chaotic, Unknown
        ]);
        
        // Update risk level chart
        this.updateMiniChart('riskLevelChart', this.analytics.riskLevels, [
            '#00ff88', '#ffaa00', '#ff6600', '#ff3366'  // SAFE, MODERATE, HIGH, CRITICAL
        ]);
    }
    
    updateMiniChart(elementId, data, colors) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const total = Object.values(data).reduce((sum, val) => sum + val, 0);
        if (total === 0) {
            element.innerHTML = '<div class="chart-empty">No data</div>';
            return;
        }
        
        let html = '<div class="mini-chart">';
        let index = 0;
        
        for (const [label, count] of Object.entries(data)) {
            if (count > 0) {
                const percentage = (count / total * 100).toFixed(1);
                html += `
                    <div class="chart-bar" style="
                        background: ${colors[index]};
                        width: ${percentage}%;
                        height: 20px;
                        display: inline-block;
                        margin-right: 2px;
                        border-radius: 2px;
                        position: relative;
                    " title="${label}: ${count} (${percentage}%)">
                        <span class="chart-label" style="
                            position: absolute;
                            top: -20px;
                            left: 0;
                            font-size: 10px;
                            color: ${colors[index]};
                            font-weight: bold;
                        ">${label}</span>
                    </div>
                `;
            }
            index++;
        }
        
        html += '</div>';
        element.innerHTML = html;
    }
    
    addEnhancedLogEntry(result, riskScore, analysisTime) {
        const logType = result.risk_detected ? 'risk' : 'safe';
        const riskEmoji = this.getRiskEmoji(result.risk_level);
        
        const logMessage = `
            Frame ${result.frame_number}: ${riskEmoji} ${result.risk_level}<br>
            <small style="opacity: 0.8;">
                Density: ${result.crowd_density} | Motion: ${result.crowd_motion} | 
                Score: ${riskScore}% | Time: ${analysisTime.toFixed(2)}s
            </small>
        `;
        
        this.addLogEntry(logMessage, logType);
        
        // Special handling for high risk levels
        if (result.risk_level === 'CRITICAL') {
            this.addLogEntry('🚨 CRITICAL RISK DETECTED - Immediate attention required!', 'risk');
        } else if (result.risk_level === 'HIGH') {
            this.addLogEntry('⚠️ HIGH RISK DETECTED - Monitor closely', 'risk');
        }
    }
    
    getRiskEmoji(riskLevel) {
        switch (riskLevel) {
            case 'SAFE': return '🟢';
            case 'MODERATE': return '🟡';
            case 'HIGH': return '🟠';
            case 'CRITICAL': return '🔴';
            default: return '⚪';
        }
    }
    
    updateAlertIndicators(result) {
        // Update critical frames count
        if (this.elements.criticalFramesCount) {
            const criticalCount = this.analytics.riskLevels.CRITICAL || 0;
            this.elements.criticalFramesCount.textContent = criticalCount;
            
            // Add warning if critical frames >= 2
            if (criticalCount >= 2) {
                this.elements.criticalFramesCount.classList.add('critical-warning');
            }
        }
        
        // Update alert indicator
        if (this.elements.alertIndicator) {
            const shouldAlert = result.updated_risk_score >= 70 || 
                               this.analytics.riskLevels.CRITICAL >= 2;
            
            if (shouldAlert) {
                this.elements.alertIndicator.classList.add('alert-active');
                this.elements.alertIndicator.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    ALERT TRIGGERED
                `;
            }
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
        
        // Remove monitoring animation from risk circle
        const riskCircle = document.querySelector('.risk-circle');
        if (riskCircle) {
            riskCircle.classList.remove('monitoring');
        }
        
        // Update UI
        this.elements.startBtn.disabled = false;
        this.elements.stopBtn.disabled = true;
        this.elements.sessionStatus.textContent = 'Stopped';
        this.elements.cameraOverlay.style.display = 'flex';
        
        this.addLogEntry('🛑 Monitoring stopped', 'safe');
        this.addLogEntry(`📊 Session Summary: ${this.elements.framesAnalyzed.textContent} frames analyzed, ${this.elements.framesFlagged.textContent} flagged`);
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
        
        // Keep only last 15 entries (increased for more detailed logs)
        while (this.elements.activityLog.children.length > 15) {
            this.elements.activityLog.removeChild(this.elements.activityLog.lastChild);
        }
    }
}

// Initialize the enhanced application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GemmaKavach();
});