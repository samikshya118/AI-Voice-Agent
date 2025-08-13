let mediaRecorder;
let audioChunks = [];
let sessionId = `session-${Date.now()}`; // Unique session ID

const startBtn = document.getElementById("start-btn");
const stopBtn = document.getElementById("stop-btn");
const voiceSelect = document.getElementById("voice-select");
const chatBox = document.getElementById("chat-box");
const statusEl = document.getElementById("status");
const audioPlayer = document.getElementById("audio-player");
const toastContainer = document.getElementById("toast-container");

startBtn.addEventListener("click", startRecording);
stopBtn.addEventListener("click", stopRecording);
stopBtn.disabled = true;

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
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
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
        statusEl.textContent = "🔴 Recording... Click Stop when done.";
        startBtn.disabled = true;
        stopBtn.disabled = false;

    } catch (err) {
        console.error("Mic access error:", err);
        statusEl.textContent = "Error: Mic access denied.";
        showToast("🎤 Microphone access denied or unavailable.", "error");
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusEl.textContent = "Recording stopped. Processing...";
    }
}

async function sendAudio(blob) {
    const formData = new FormData();
    formData.append("audio", blob, "recording.wav");
    formData.append("voice", voiceSelect.value);

    try {
        const res = await fetch(`/agent/chat/${sessionId}`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        // --- Error Case ---
        if (!res.ok) {
            const errorMessage = data.error || `Server error: ${res.status}`;
            const errorDetails = data.details || "No details provided.";
            console.error("Server Error:", errorMessage, errorDetails);
            showToast(`⚠️ ${errorMessage}`, "error");
            addMessage("error", `${errorMessage} - ${errorDetails}`);
            statusEl.textContent = "Error";

            // If fallback audio is provided, play it
            if (data.audio_url) {
                audioPlayer.src = data.audio_url;
                audioPlayer.play().catch(err => {
                    console.error("Audio play error:", err);
                    showToast("🔊 Failed to play fallback audio.", "error");
                });
            }
            return;
        }

        // --- Success Case ---
        addMessage("user", data.user_transcription || "[No transcription]");
        addMessage("assistant", data.llm_response || "[No response]");

        if (data.audio_url) {
            audioPlayer.src = data.audio_url;
            audioPlayer.play().catch(err => {
                console.error("Audio play error:", err);
                showToast("🔊 Failed to play audio.", "error");
            });
        } else {
            showToast("⚠️ No audio was generated.", "error");
        }

        statusEl.textContent = "Idle";

    } catch (err) {
        console.error("Fetch/network error:", err);
        addMessage("error", "Failed to send audio to the server.");
        statusEl.textContent = "Network Error";
        showToast("📡 Network error. Could not reach server.", "error");
    }
}
