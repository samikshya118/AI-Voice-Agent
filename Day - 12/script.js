let mediaRecorder;
let audioChunks = [];
let sessionId = `session-${Date.now()}`;

const recordBtn = document.getElementById("record-btn");
const voiceSelect = document.getElementById("voice-select");
const chatBox = document.getElementById("chat-box");
const statusEl = document.getElementById("status");
const audioPlayer = document.getElementById("audio-player");
const toastContainer = document.getElementById("toast-container");

let isRecording = false;

recordBtn.addEventListener("click", () => {
    if (!isRecording) startRecording();
    else stopRecording();
});

function addMessage(role, text) {
    const div = document.createElement("div");
    div.classList.add("message", role);
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showToast(message, type = "error") {
    const toast = document.createElement("div");
    toast.classList.add("toast", type);
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
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
        isRecording = true;
        recordBtn.textContent = "⏹ Stop Recording";
        recordBtn.classList.add("recording");
        statusEl.textContent = "🔴 Recording...";
    } catch (err) {
        console.error("Mic access error:", err);
        showToast("🎤 Microphone access denied.", "error");
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        isRecording = false;
        recordBtn.textContent = "🎤 Start Recording";
        recordBtn.classList.remove("recording");
    }
}

async function sendAudio(blob) {
    const formData = new FormData();
    formData.append("audio", blob, "recording.wav");
    formData.append("voice", voiceSelect.value);

    try {
        const res = await fetch(`/agent/chat/${sessionId}`, { method: "POST", body: formData });
        const data = await res.json();

        if (!res.ok) {
            showToast(`⚠️ ${data.error}`, "error");
            statusEl.textContent = "Error";
            if (data.audio_url) playAudio(data.audio_url);
            return;
        }

        addMessage("user", data.user_transcription || "[No transcription]");
        addMessage("assistant", data.llm_response || "[No response]");

        if (data.audio_url) playAudio(data.audio_url);
        else showToast("⚠️ No audio generated.", "error");

        statusEl.textContent = "Idle";
    } catch (err) {
        console.error("Fetch error:", err);
        showToast("📡 Network error.", "error");
        statusEl.textContent = "Network Error";
    }
}

function playAudio(url) {
    audioPlayer.src = url;
    audioPlayer.play().catch(err => {
        console.error("Audio play error:", err);
        showToast("🔊 Failed to play audio.", "error");
    });
}
