        // Set up SSE connection
        const eventSource = new EventSource('/events');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'webhook') {
                updateContent(data.content);
            }
        };

        eventSource.onerror = function(error) {
            console.error("EventSource failed:", error);
            eventSource.close();
            // Try to reconnect after 5 seconds
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        };

        function updateContent(content) {
            document.querySelector('.update-info').innerHTML = content;
            // Add click handlers to event cards after content update
            addEventCardHandlers();
        }

        function refreshUpdates() {
            fetch('/refresh-updates')
                .then(response => response.text())
                .then(data => {
                    updateContent(data);
                });
        }

        function launchGame() {
            fetch('/launch-game')
                .then(response => response.text())
                .then(data => console.log(data));
        }

        function addEventCardHandlers() {
            document.querySelectorAll('.event-card.active').forEach(card => {
                card.addEventListener('click', launchGame);
            });
        }

        function formatDateTime(timestamp) {
            const date = new Date(timestamp);
            const options = { 
                weekday: 'long',
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit', 
                minute: '2-digit'
            };
            return date.toLocaleDateString(undefined, options);
        }

        function updateCountdowns() {
            document.querySelectorAll('.event-card').forEach(card => {
                const type = card.dataset.type;
                const timestamp = parseInt(card.dataset.timestamp);
                const countdownText = card.querySelector('.countdown-text');
                const dateText = card.querySelector('.date-text');
                
                if (type === 'recurring') {
                    const duration = parseInt(card.dataset.duration);
                    const period = parseInt(card.dataset.period);
                    const offset = parseInt(card.dataset.offset);
                    const showSeconds = card.dataset.showSeconds === 'true';
                    
                    // Calculate next occurrence
                    const now = Math.floor(Date.now() / 1000);
                    const cyclePosition = (now + offset) % period;
                    const timeUntilNext = period - cyclePosition;
                    const nextOccurrence = new Date((now + timeUntilNext) * 1000);
                    
                    // Format the countdown
                    const hours = Math.floor(timeUntilNext / 3600);
                    const minutes = Math.floor((timeUntilNext % 3600) / 60);
                    const seconds = timeUntilNext % 60;
                    
                    const timeStr = showSeconds ? 
                        `${hours}h ${minutes}m ${seconds}s` :
                        `${hours}h ${minutes}m`;
                        
                    countdownText.textContent = `Next in: ${timeStr}`;
                    dateText.textContent = `Next occurrence: ${formatDateTime(nextOccurrence)}`;
                    
                } else if (type === 'onetime') {
                    const eventTime = new Date(timestamp);
                    const now = new Date();
                    const diff = eventTime - now;
                    
                    if (diff > 0) {
                        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                        
                        let timeStr = '';
                        if (days > 0) timeStr += `${days}d `;
                        timeStr += `${hours}h ${minutes}m ${seconds}s`;
                        
                        const status = card.querySelector('.countdown-text').textContent.includes('Ends') ? 'Ends' : 'Starts';
                        countdownText.textContent = `${status} in: ${timeStr}`;
                        dateText.textContent = `Event ${status.toLowerCase()} on: ${formatDateTime(eventTime)}`;
                    }
                }
            });
        }

        // Update countdowns every second
        setInterval(updateCountdowns, 1000);
        
        // Initial update
        updateCountdowns();

        async function refreshUpdates() {
            try {
                const response = await fetch('data/updates.json');
                const data = await response.json();
                updateContent(data);
            } catch (error) {
                console.error('Error fetching updates:', error);
            }
        }
        
        function updateContent(data) {
            const updateInfo = document.querySelector('.update-info');
            updateInfo.innerHTML = `
                <div style='background-color: #f0f8ff; padding: 15px; border-radius: 4px; margin-bottom: 15px;'>
                    <strong>Last Update:</strong><br>
                    ${data.lastUpdate}
                </div>
            `;
        }
        
        // Initial load
        document.addEventListener('DOMContentLoaded', refreshUpdates);