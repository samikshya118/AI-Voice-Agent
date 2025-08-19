let mediaRecorder;
let audioChunks = [];

const startBtn = document.getElementById("startRecording");
const stopBtn = document.getElementById("stopRecording");
const echoPlayer = document.getElementById("echoPlayer");
const transcriptionResult = document.getElementById("transcriptionResult");
const fileInfo = document.getElementById("fileInfo");

startBtn.addEventListener("click", async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
  };

  mediaRecorder.onstop = () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

    const fileSizeKB = (audioBlob.size / 1024).toFixed(2);
    if (fileInfo) {
      fileInfo.innerHTML = `
        <p>✅ File recorded successfully</p>
        <p>Size: ${fileSizeKB} KB</p>
        <p>Type: ${audioBlob.type}</p>
      `;
    }

    if (transcriptionResult) {
      transcriptionResult.textContent = "📤 Uploading, transcribing, and generating Murf voice...";
    }

    const formData = new FormData();
    formData.append("audio", audioBlob, `recording-${Date.now()}.webm`);

    fetch("/tts/echo", {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      console.log("🔊 Murf API response:", data);

      if (data.transcription) {
        transcriptionResult.innerHTML = `📝 Transcription: "${data.transcription}"`;
      }

      if (data.audio_url) {
        echoPlayer.src = data.audio_url;
        echoPlayer.play();
        transcriptionResult.innerHTML += `<br>🔊 Murf Voice Ready!`;
      } else if (data.error) {
        transcriptionResult.textContent = `❌ Error: ${data.error}`;
      } else {
        transcriptionResult.textContent = "❌ Unknown error occurred. Check server logs.";
      }
    })
    .catch((err) => {
      console.error("🚫 Fetch error:", err);
      transcriptionResult.textContent = "❌ Upload or Murf error.";
    });
  };

  mediaRecorder.start();
  startBtn.disabled = true;
  stopBtn.disabled = false;
});

stopBtn.addEventListener("click", () => {
  mediaRecorder.stop();
  startBtn.disabled = false;
  stopBtn.disabled = true;
});
