// ================================
// CONFIGURATION
// ================================

const API_BASE_URL = 'http://localhost:5000/api';

// ================================
// NAVIGATION & PAGE SWITCHING
// ================================

const navLinks = document.querySelectorAll('.nav-link');
const pages = document.querySelectorAll('.page');

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetPage = link.getAttribute('data-page');
        
        navLinks.forEach(l => l.classList.remove('active'));
        pages.forEach(p => p.classList.remove('active'));
        
        link.classList.add('active');
        document.getElementById(targetPage).classList.add('active');
        
        if (targetPage === 'schedule') loadSchedule();
        if (targetPage === 'ask-ai') loadChatHistory();
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});

// ================================
// API UTILITY
// ================================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-User': 'demo_user',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        return null;
    }
}

// ================================
// HOME PAGE - WORKFLOW CARD
// ================================

const tellWorkflowBtn = document.getElementById('tellWorkflowBtn');
const workflowCard = document.getElementById('workflowCard');
const closeWorkflowBtn = document.getElementById('closeWorkflowBtn');

tellWorkflowBtn.addEventListener('click', () => {
    workflowCard.classList.add('visible');
    setTimeout(() => workflowCard.querySelector('.workflow-input').focus(), 400);
});

closeWorkflowBtn.addEventListener('click', () => {
    workflowCard.classList.remove('visible');
});

document.addEventListener('click', (e) => {
    if (workflowCard.classList.contains('visible') && 
        !workflowCard.contains(e.target) && 
        !tellWorkflowBtn.contains(e.target)) {
        workflowCard.classList.remove('visible');
    }
});

// ================================
// CHAT FUNCTIONALITY
// ================================

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isUser ? 'You' : 'AI';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = `<p>${content}</p>`;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message typing-message';
    typingDiv.id = 'typing-indicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'message-content';
    typingContent.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    
    typingDiv.appendChild(avatar);
    typingDiv.appendChild(typingContent);
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) typingIndicator.remove();
}

async function loadChatHistory() {
    const data = await apiCall('/chat/history?limit=50');
    if (data && data.history) {
        const messages = chatMessages.querySelectorAll('.message');
        messages.forEach((msg, idx) => {
            if (idx > 0) msg.remove();
        });
        
        data.history.forEach(msg => {
            const initialGreeting = chatMessages.querySelector('.ai-message p').textContent;
            if (msg.role !== 'assistant' || msg.content !== initialGreeting) {
                addMessage(msg.content, msg.role === 'user');
            }
        });
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (message === '') return;
    
    addMessage(message, true);
    chatInput.value = '';
    showTypingIndicator();
    
    const data = await apiCall('/chat', {
        method: 'POST',
        body: JSON.stringify({ message })
    });
    
    removeTypingIndicator();
    
    if (data && data.response) {
        addMessage(data.response);
    } else {
        addMessage("I'm here to help! Try the Pomodoro Technique: 25min work, 5min break.");
    }
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ================================
// SCHEDULE PAGE
// ================================

let currentScheduleId = null;

async function loadSchedule() {
    const data = await apiCall('/schedule');
    if (data && data.blocks && data.blocks.length > 0) {
        currentScheduleId = data.schedule_id;
        renderSchedule(data.blocks);
    }
}

function renderSchedule(blocks) {
    const dayBlocks = {};
    blocks.forEach(block => {
        if (!dayBlocks[block.day_of_week]) dayBlocks[block.day_of_week] = [];
        dayBlocks[block.day_of_week].push(block);
    });
    
    const dayColumns = document.querySelectorAll('.day-column');
    dayColumns.forEach((column, idx) => {
        if (idx < 5) {
            const existingBlocks = column.querySelectorAll('.study-block');
            existingBlocks.forEach(b => b.remove());
            
            if (dayBlocks[idx]) {
                dayBlocks[idx].forEach(block => {
                    const blockEl = createStudyBlockElement(block);
                    column.appendChild(blockEl);
                });
            }
        }
    });
}

function createStudyBlockElement(block) {
    const blockDiv = document.createElement('div');
    blockDiv.className = `study-block priority-${block.priority}`;
    blockDiv.dataset.blockId = block.id;
    
    blockDiv.innerHTML = `
        <div class="block-time">${block.start_time} - ${block.end_time}</div>
        <div class="block-subject">${block.subject}</div>
        <div class="block-topic">${block.topic || ''}</div>
    `;
    
    blockDiv.addEventListener('click', () => {
        console.log('Study block clicked:', block);
        blockDiv.style.transform = 'scale(0.98)';
        setTimeout(() => blockDiv.style.transform = '', 100);
    });
    
    return blockDiv;
}

// ================================
// WORKFLOW FORM SUBMISSION
// ================================

const workflowInput = document.querySelector('.workflow-input');
const submitBtn = document.querySelector('.submit-btn');

submitBtn.addEventListener('click', async () => {
    const workflowText = workflowInput.value.trim();
    
    if (workflowText === '') {
        workflowInput.style.animation = 'shake 0.3s';
        setTimeout(() => workflowInput.style.animation = '', 300);
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Generating...';
    
    const data = await apiCall('/generate-schedule', {
        method: 'POST',
        body: JSON.stringify({ workflow: workflowText })
    });
    
    submitBtn.disabled = false;
    
    if (data && data.success) {
        submitBtn.textContent = 'Schedule Generated! ✓';
        submitBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        
        setTimeout(() => {
            submitBtn.textContent = 'Generate Schedule';
            submitBtn.style.background = '';
            workflowCard.classList.remove('visible');
            workflowInput.value = '';
            document.querySelector('[data-page="schedule"]').click();
        }, 1500);
    } else {
        submitBtn.textContent = 'Error - Try Again';
        submitBtn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        
        setTimeout(() => {
            submitBtn.textContent = 'Generate Schedule';
            submitBtn.style.background = '';
        }, 2000);
    }
});

// ================================
// SMOOTH SCROLL
// ================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && !this.classList.contains('nav-link')) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// ================================
// HEADER SCROLL EFFECT
// ================================

const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    if (currentScroll > 100) {
        header.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.5)';
    } else {
        header.style.boxShadow = '';
    }
});

// ================================
// KEYBOARD SHORTCUTS
// ================================

document.addEventListener('keydown', (e) => {
    if (e.altKey) {
        switch(e.key) {
            case '1': document.querySelector('[data-page="home"]').click(); break;
            case '2': document.querySelector('[data-page="ask-ai"]').click(); break;
            case '3': document.querySelector('[data-page="schedule"]').click(); break;
            case '4': document.querySelector('[data-page="framework"]').click(); break;
            case '5': document.querySelector('[data-page="about"]').click(); break;
        }
    }
    
    if (e.key === 'Escape' && workflowCard.classList.contains('visible')) {
        workflowCard.classList.remove('visible');
    }
});

// ================================
// ANIMATIONS ON LOAD
// ================================

window.addEventListener('load', () => {
    const scheduleBlocks = document.querySelectorAll('.study-block');
    scheduleBlocks.forEach((block, index) => {
        block.style.animationDelay = `${index * 0.05}s`;
    });
    
    const nodes = document.querySelectorAll('.framework-node');
    nodes.forEach((node, index) => {
        node.style.animationDelay = `${index * 0.1}s`;
    });
    
    checkBackendHealth();
});

// ================================
// BACKEND HEALTH CHECK
// ================================

async function checkBackendHealth() {
    const data = await apiCall('/health');
    
    if (data) {
        console.log('%cFocusFlow-AI Backend Connected ✓', 'color: #10b981; font-weight: bold; font-size: 14px;');
        console.log(`Status: ${data.status}`);
        console.log(`AI Provider: ${data.ai_provider || 'None'}`);
        console.log(`AI Enabled: ${data.ai_enabled ? 'YES ✓' : 'NO (using fallbacks)'}`);
    } else {
        console.warn('%cBackend Not Connected ⚠', 'color: #f59e0b; font-weight: bold; font-size: 14px;');
        console.log('Make sure backend.py is running on port 5000');
    }
}

// ================================
// SHAKE ANIMATION
// ================================

const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
`;
document.head.appendChild(style);

// ================================
// CONSOLE WELCOME
// ================================

console.log('%cFocusFlow-AI', 'font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;');
console.log('%cDeveloper Mode Active', 'font-size: 14px; color: #10b981;');
console.log('\nKeyboard Shortcuts:');
console.log('  Alt + 1-5: Quick navigation');
console.log('  Escape: Close workflow card');
console.log('\nBackend API:');
console.log(`  Base URL: ${API_BASE_URL}`);
console.log('  Checking connection...');
