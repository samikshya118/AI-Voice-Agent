// static/script.js
document.addEventListener("DOMContentLoaded", () => {
    const recordBtn = document.getElementById("recordBtn");
    const statusDisplay = document.getElementById("statusDisplay");
    const chatLog = document.getElementById("chat-log");
    const personaSelect = document.getElementById("personaSelect");

    let recognition;
    let isRecording = false;
    let websocket;
    let audioQueue = [];
    let isPlaying = false;
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();

    if (!('webkitSpeechRecognition' in window)) {
        statusDisplay.textContent = "Your browser doesn't support speech recognition. Please use Google Chrome.";
        recordBtn.disabled = true;
        return;
    }

    const startSession = () => {
        const selectedPersona = personaSelect.value;
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${wsProtocol}//${window.location.host}/ws?persona=${selectedPersona}`;
        
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log("WebSocket connection established.");
            statusDisplay.textContent = "Listening...";
            isRecording = true;
            recordBtn.classList.add("recording");
            
            recognition = new webkitSpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = "en-US";

            recognition.onresult = (event) => {
                const transcript = event.results[event.results.length - 1][0].transcript.trim();
                
                if (transcript) {
                    console.log("Final transcript:", transcript);
                    addMessage("You", transcript);
                    websocket.send(JSON.stringify({ transcript: transcript }));
                    statusDisplay.textContent = "Thinking...";
                }
            };
            
            recognition.onerror = (event) => {
                console.error("Speech recognition error:", event.error);
                statusDisplay.textContent = `Error: ${event.error}`;
            };

            recognition.start();
        };

        websocket.onmessage = async (event) => {
            if (typeof event.data === "string") {
                const data = JSON.parse(event.data);
                if (data.response) {
                    addMessage("AI", data.response);
                    statusDisplay.textContent = "Listening...";
                }
            } else if (event.data instanceof Blob) {
                const arrayBuffer = await event.data.arrayBuffer();
                audioContext.decodeAudioData(arrayBuffer)
                    .then(audioBuffer => {
                        audioQueue.push(audioBuffer);
                        if (!isPlaying) {
                            playQueue();
                        }
                    })
                    .catch(e => console.error("Error decoding audio data:", e));
            }
        };

        websocket.onerror = (error) => {
            console.error("WebSocket error:", error);
            statusDisplay.textContent = "Connection error.";
        };

        websocket.onclose = () => {
            console.log("WebSocket connection closed.");
            if (isRecording) {
                stopSession();
            }
        };
    };

    const stopSession = () => {
        if (isRecording) {
            isRecording = false;
            recordBtn.classList.remove("recording");
            statusDisplay.textContent = "Ready to chat!";
            
            if (recognition) {
                recognition.stop();
                recognition = null;
            }
            if (websocket) {
                websocket.close();
                websocket = null;
            }
        }
    };

    recordBtn.addEventListener("click", () => {
        if (!isRecording) {
            startSession();
        } else {
            stopSession();
        }
    });

    personaSelect.addEventListener("change", () => {
        if (isRecording) {
            stopSession();
            setTimeout(startSession, 100);
        }
    });

    function addMessage(sender, message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", sender === "You" ? "user-message" : "ai-message");
        const senderElement = document.createElement("strong");
        senderElement.textContent = `${sender}: `;
        const contentElement = document.createElement("span");
        contentElement.textContent = message;
        messageElement.appendChild(senderElement);
        messageElement.appendChild(contentElement);
        chatLog.appendChild(messageElement);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    async function playQueue() {
        if (audioQueue.length === 0) {
            isPlaying = false;
            return;
        }
        isPlaying = true;
        const audioBuffer = audioQueue.shift();
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.onended = playQueue; 
        source.start();
    }
});