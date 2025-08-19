let mediaRecorder;
let audioChunks = [];
let sessionId = "default"; // could randomize if needed

const startBtn = document.getElementById("start-btn");
const stopBtn = document.getElementById("stop-btn");
const voiceSelect = document.getElementById("voice-select");
const chatBox = document.getElementById("chat-box");
const statusEl = document.getElementById("status");
const audioPlayer = document.getElementById("audio-player");

startBtn.addEventListener("click", startRecording);
stopBtn.addEventListener("click", stopRecording);

function addMessage(role, text) {
    const div = document.createElement("div");
    div.classList.add("message", role);
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            statusEl.textContent = "Processing...";
            const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
            await sendAudio(audioBlob);
        };

        mediaRecorder.start();
        statusEl.textContent = "Recording...";
        startBtn.disabled = true;
        stopBtn.disabled = false;

    } catch (err) {
        console.error("Error starting recording:", err);
        statusEl.textContent = "Error starting recording";
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusEl.textContent = "Stopped recording";
    }
}

async function sendAudio(blob) {
    const formData = new FormData();
    formData.append("audio", blob, "recording.wav");

    try {
        const res = await fetch(`/agent/chat/${sessionId}`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();

        if (data.error) {
            addMessage("error", `Error: ${data.error}`);
            statusEl.textContent = "Error";
            return;
        }

        addMessage("user", data.user_transcription || "[No transcription]");
        addMessage("assistant", data.llm_response || "[No response]");
        
        if (data.audio_url) {
            audioPlayer.src = data.audio_url;
            audioPlayer.play();
        }

        statusEl.textContent = "Idle";
    } catch (err) {
        console.error("Error sending audio:", err);
        addMessage("error", "Failed to send audio");
        statusEl.textContent = "Error";
    }
}
