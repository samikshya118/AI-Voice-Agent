let mediaRecorder;
let ws;
let isRecording = false;

const recordBtn = document.getElementById("record-btn");
const statusEl = document.getElementById("status");

recordBtn.addEventListener("click", () => {
    if (!isRecording) startRecording();
    else stopRecording();
});

async function startRecording() {
    try {
        // open websocket connection
        ws = new WebSocket("ws://127.0.0.1:8000/ws");

        ws.onopen = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Force browser to use webm/opus
            mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });

            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                    e.data.arrayBuffer().then(buffer => {
                        ws.send(buffer);   // send binary chunk
                    });
                }
            };

            // send chunk every 250ms
            mediaRecorder.start(250);

            isRecording = true;
            recordBtn.textContent = "⏹ Stop Recording";
            recordBtn.classList.add("recording");
            statusEl.textContent = "🔴 Streaming...";
        };

        ws.onclose = () => {
            console.log("WebSocket closed");
        };

    } catch (err) {
        console.error("Mic access error:", err);
        statusEl.textContent = "Error: Mic blocked";
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        isRecording = false;
        recordBtn.textContent = "🎤 Start Recording";
        recordBtn.classList.remove("recording");
        statusEl.textContent = "Stopped";
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }
}
