function startDetection() {
    fetch('/start_detection', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Detection started') {
                const videoElement = document.getElementById('video');
                videoElement.src = "/video_feed";  // Set the source for the image
                videoElement.style.display = 'block';  // Ensure the image is displayed
                startAlertPolling();  // Start polling for alerts
            }
        });
}

function stopDetection() {
    fetch('/stop_detection', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Detection stopped') {
                const videoElement = document.getElementById('video');
                videoElement.src = "";  // Clear the video feed
                videoElement.style.display = 'none';  // Hide the video feed when stopped
                stopAlertPolling();  // Stop polling for alerts
            }
        });
}

let alertPollingInterval;

function startAlertPolling() {
    alertPollingInterval = setInterval(() => {
        fetch('/get_alert')
            .then(response => response.json())
            .then(data => {
                const alertMessageElement = document.getElementById('alert-message');
                if (data.alert) {
                    alertMessageElement.innerText = data.alert;
                    alertMessageElement.style.display = 'block';
                    if (data.alert.includes("Drowsiness")) {
                        alertMessageElement.className = 'alert alert-drowsiness';
                    } else if (data.alert.includes("Yawn")) {
                        alertMessageElement.className = 'alert alert-yawn';
                    }
                } else {
                    alertMessageElement.style.display = 'none';
                }
            });
    }, 1000);
}

function stopAlertPolling() {
    clearInterval(alertPollingInterval);
    const alertMessageElement = document.getElementById('alert-message');
    alertMessageElement.style.display = 'none';
}
