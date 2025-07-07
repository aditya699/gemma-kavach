// Enhanced Emergency Classification System JavaScript

class EmergencyClassifier {
    constructor() {
        this.sessionStartTime = Date.now();
        this.totalClassifications = 0;
        this.responseTimes = [];
        this.successfulClassifications = 0;
        this.classificationHistory = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkServerConnection();
        this.startSessionTimer();
        this.updateCharCounter();
    }
    
    initializeElements() {
        this.elements = {
            // Input elements
            emergencyText: document.getElementById('emergencyText'),
            charCount: document.getElementById('charCount'),
            classifyBtn: document.getElementById('classifyBtn'),
            clearBtn: document.getElementById('clearBtn'),
            
            // Status elements
            connectionStatus: document.getElementById('connectionStatus'),
            resultDisplay: document.getElementById('resultDisplay'),
            
            // Model info elements
            modelStatus: document.getElementById('modelStatus'),
            modelDevice: document.getElementById('modelDevice'),
            categoriesCount: document.getElementById('categoriesCount'),
            
            // Stats elements
            totalClassifications: document.getElementById('totalClassifications'),
            avgResponseTime: document.getElementById('avgResponseTime'),
            successRate: document.getElementById('successRate'),
            sessionTime: document.getElementById('sessionTime'),
            
            // History
            classificationHistory: document.getElementById('classificationHistory'),
            
            // Modals
            loadingModal: document.getElementById('loadingModal'),
            successModal: document.getElementById('successModal'),
            successMessage: document.getElementById('successMessage')
        };
    }
    
    setupEventListeners() {
        // Main action buttons
        this.elements.classifyBtn.addEventListener('click', () => this.classifyEmergency());
        this.elements.clearBtn.addEventListener('click', () => this.clearText());
        
        // Text input events
        this.elements.emergencyText.addEventListener('input', () => this.updateCharCounter());
        this.elements.emergencyText.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.classifyEmergency();
            }
        });
        
        // Example buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const text = e.currentTarget.getAttribute('data-text');
                this.elements.emergencyText.value = text;
                this.updateCharCounter();
                this.elements.emergencyText.focus();
            });
        });
        
        // Enter key support for classify button
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                this.classifyEmergency();
            }
        });
    }
    
    async checkServerConnection() {
        try {
            // Check model status
            const modelResponse = await fetch('/model_info');
            const modelData = await modelResponse.json();
            
            if (modelResponse.ok && modelData.model_loaded) {
                this.updateConnectionStatus(true);
                this.updateModelInfo(modelData);
            } else {
                this.updateConnectionStatus(false);
                this.elements.modelStatus.textContent = 'Model Not Loaded';
                this.elements.modelStatus.className = 'info-value status-error';
            }
        } catch (error) {
            console.error('Server connection failed:', error);
            this.updateConnectionStatus(false);
            this.elements.modelStatus.textContent = 'Connection Failed';
            this.elements.modelStatus.className = 'info-value status-error';
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
    
    updateModelInfo(modelData) {
        this.elements.modelStatus.textContent = 'Ready';
        this.elements.modelStatus.className = 'info-value status-active';
        this.elements.modelDevice.textContent = modelData.device || 'Unknown';
        this.elements.categoriesCount.textContent = modelData.categories?.length || 6;
    }
    
    updateCharCounter() {
        const text = this.elements.emergencyText.value;
        const count = text.length;
        this.elements.charCount.textContent = count;
        
        // Update button state
        this.elements.classifyBtn.disabled = count === 0 || count > 500;
        
        // Change color based on character count
        if (count > 450) {
            this.elements.charCount.style.color = '#ef4444';
        } else if (count > 350) {
            this.elements.charCount.style.color = '#f59e0b';
        } else {
            this.elements.charCount.style.color = '#64748b';
        }
    }
    
    clearText() {
        this.elements.emergencyText.value = '';
        this.updateCharCounter();
        this.elements.emergencyText.focus();
        
        // Add a subtle animation
        this.elements.emergencyText.style.transform = 'scale(1.02)';
        setTimeout(() => {
            this.elements.emergencyText.style.transform = 'scale(1)';
        }, 150);
    }
    
    async classifyEmergency() {
        const text = this.elements.emergencyText.value.trim();
        
        if (!text || text.length > 500) {
            this.showAlert('Please enter a valid emergency description (1-500 characters)', 'error');
            return;
        }
        
        try {
            // Show loading
            this.showLoading();
            this.elements.classifyBtn.disabled = true;
            
            // Record start time
            const startTime = performance.now();
            
            // Make API call
            const response = await fetch('/ask_class', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            
            // Calculate response time
            const responseTime = performance.now() - startTime;
            this.responseTimes.push(responseTime);
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Update classification result
            this.displayClassificationResult(result, responseTime);
            
            // Update stats
            this.updateStats(true, responseTime);
            
            // Add to history
            this.addToHistory(text, result.category, responseTime);
            
            // Show success
            this.hideLoading();
            this.showSuccessModal(result.category);
            
        } catch (error) {
            console.error('Classification failed:', error);
            this.hideLoading();
            this.updateStats(false);
            this.showAlert(`Classification failed: ${error.message}`, 'error');
        } finally {
            this.elements.classifyBtn.disabled = false;
        }
    }
    
    displayClassificationResult(result, responseTime) {
        const categoryInfo = this.getCategoryInfo(result.category);
        
        const resultHTML = `
            <div class="result-success fade-in">
                <div class="category-badge">
                    <i class="${categoryInfo.icon}"></i>
                    ${categoryInfo.displayName}
                </div>
                <div class="confidence">Classification Confidence: High</div>
                <div class="response-time">Response Time: ${responseTime.toFixed(0)}ms</div>
            </div>
        `;
        
        this.elements.resultDisplay.innerHTML = resultHTML;
    }
    
    getCategoryInfo(category) {
        const categoryMap = {
            'child_lost': { displayName: 'Child Lost', icon: 'fas fa-child' },
            'crowd_panic': { displayName: 'Crowd Panic', icon: 'fas fa-running' },
            'medical_help': { displayName: 'Medical Help', icon: 'fas fa-first-aid' },
            'small_fire': { displayName: 'Small Fire', icon: 'fas fa-fire' },
            'lost_item': { displayName: 'Lost Item', icon: 'fas fa-wallet' },
            'need_interpreter': { displayName: 'Need Interpreter', icon: 'fas fa-language' }
        };
        
        return categoryMap[category] || { displayName: category, icon: 'fas fa-question' };
    }
    
    updateStats(success, responseTime = null) {
        this.totalClassifications++;
        
        if (success) {
            this.successfulClassifications++;
        }
        
        // Update display
        this.elements.totalClassifications.textContent = this.totalClassifications;
        
        if (responseTime !== null && this.responseTimes.length > 0) {
            const avgResponseTime = this.responseTimes.reduce((a, b) => a + b, 0) / this.responseTimes.length;
            this.elements.avgResponseTime.textContent = `${avgResponseTime.toFixed(0)}ms`;
        }
        
        const successRate = this.totalClassifications > 0 
            ? (this.successfulClassifications / this.totalClassifications * 100)
            : 100;
        this.elements.successRate.textContent = `${successRate.toFixed(0)}%`;
    }
    
    addToHistory(text, category, responseTime) {
        const categoryInfo = this.getCategoryInfo(category);
        const time = new Date().toLocaleTimeString();
        
        const historyItem = {
            text: text,
            category: category,
            categoryInfo: categoryInfo,
            time: time,
            responseTime: responseTime
        };
        
        // Add to beginning of array
        this.classificationHistory.unshift(historyItem);
        
        // Keep only last 10 items
        if (this.classificationHistory.length > 10) {
            this.classificationHistory = this.classificationHistory.slice(0, 10);
        }
        
        this.updateHistoryDisplay();
    }
    
    updateHistoryDisplay() {
        const historyContainer = this.elements.classificationHistory;
        
        if (this.classificationHistory.length === 0) {
            historyContainer.innerHTML = '<div class="history-placeholder"><p>No recent classifications yet.</p></div>';
            return;
        }
        
        const historyHTML = this.classificationHistory.map(item => `
            <div class="history-item slide-up">
                <div class="history-item-header">
                    <span class="history-category">
                        <i class="${item.categoryInfo.icon}"></i>
                        ${item.categoryInfo.displayName}
                    </span>
                    <span class="history-time">${item.time}</span>
                </div>
                <div class="history-text">${this.truncateText(item.text, 60)}</div>
            </div>
        `).join('');
        
        historyContainer.innerHTML = historyHTML;
    }
    
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    startSessionTimer() {
        setInterval(() => {
            const elapsed = Date.now() - this.sessionStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            this.elements.sessionTime.textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    showLoading() {
        this.elements.loadingModal.classList.add('show');
    }
    
    hideLoading() {
        this.elements.loadingModal.classList.remove('show');
    }
    
    showSuccessModal(category) {
        const categoryInfo = this.getCategoryInfo(category);
        this.elements.successMessage.textContent = 
            `Emergency classified as "${categoryInfo.displayName}". Classification complete!`;
        this.elements.successModal.classList.add('show');
        
        // Auto-close after 3 seconds
        setTimeout(() => {
            this.closeSuccessModal();
        }, 3000);
    }
    
    closeSuccessModal() {
        this.elements.successModal.classList.remove('show');
    }
    
    showAlert(message, type = 'info') {
        // Create temporary alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            background: ${type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            border-radius: 12px;
            z-index: 10000;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            animation: slideInFromRight 0.3s ease-out;
            max-width: 400px;
            font-weight: 600;
        `;
        
        alert.textContent = message;
        document.body.appendChild(alert);
        
        // Add animation styles if not already present
        if (!document.getElementById('alert-animations')) {
            const style = document.createElement('style');
            style.id = 'alert-animations';
            style.textContent = `
                @keyframes slideInFromRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOutToRight {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            alert.style.animation = 'slideOutToRight 0.3s ease-out forwards';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }, 4000);
    }
}

// Global function for modal close (called from HTML)
function closeSuccessModal() {
    if (window.classifier) {
        window.classifier.closeSuccessModal();
    }
}

// Enhanced keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape key to close modals
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.show').forEach(modal => {
            modal.classList.remove('show');
        });
    }
    
    // Ctrl+L to clear text
    if (e.key === 'l' && e.ctrlKey) {
        e.preventDefault();
        if (window.classifier) {
            window.classifier.clearText();
        }
    }
});

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.classifier = new EmergencyClassifier();
    console.log('✅ Emergency Classification System initialized');
});

// Add some utility functions for enhanced UX
function addFocusAnimations() {
    // Add focus animations to interactive elements
    const interactiveElements = document.querySelectorAll('button, input, textarea, .example-btn');
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Add performance monitoring
function trackPerformance() {
    // Track page load time
    window.addEventListener('load', () => {
        const loadTime = performance.now();
        console.log(`📊 Page loaded in ${loadTime.toFixed(2)}ms`);
    });
}

// Initialize additional features
document.addEventListener('DOMContentLoaded', () => {
    addFocusAnimations();
    trackPerformance();
    
    // Add version info to console
    console.log('🚀 Gemma Kavach Emergency Classification System v1.0.0');
    console.log('⌨️  Keyboard shortcuts:');
    console.log('   • Ctrl+Enter: Classify text');
    console.log('   • Ctrl+L: Clear text');
    console.log('   • Escape: Close modals');
});