let ws;
let audioCtx;
let processor;
let source;
let isRecording = false;

const recordBtn = document.getElementById("record-btn");
const statusEl = document.getElementById("status");
const chatBox = document.getElementById("chat-box");
const liveText = document.getElementById("live-text");
const sessionBanner = document.getElementById("session-banner");

recordBtn.addEventListener("click", () => {
  if (!isRecording) startRecording();
  else stopRecording();
});

async function startRecording() {
  try {
    ws = new WebSocket(`ws://${window.location.host}/ws/transcribe`);

    ws.onopen = () => {
      console.log("✅ WS connected");
      statusEl.textContent = "Recording…";
      liveText.innerHTML = "<em>Listening…</em>";

      // 🔥 Hide any old "Session Ended" banner when a new session starts
      sessionBanner.classList.add("hidden");
      sessionBanner.classList.remove("fade");
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.transcript) {
          if (data.end_of_turn) {
            const msg = document.createElement("div");
            msg.classList.add("message", "assistant");
            msg.textContent = data.transcript;
            chatBox.appendChild(msg);
            chatBox.scrollTop = chatBox.scrollHeight;
            liveText.innerHTML = "<em>…</em>";
          } else {
            liveText.innerHTML = "<em>" + data.transcript + "</em>";
          }
        }
      } catch (e) {
        console.warn("Non-JSON message:", evt.data);
      }
    };

    ws.onclose = () => {
      console.log("🔌 WS closed");
      statusEl.textContent = "Stopped";
      liveText.innerHTML = "<em>Idle</em>";
    };

    const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 } });
    audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    source = audioCtx.createMediaStreamSource(stream);

    const BUFFER_SIZE = 4096;
    processor = audioCtx.createScriptProcessor(BUFFER_SIZE, 1, 1);

    processor.onaudioprocess = (e) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;

      const input = e.inputBuffer.getChannelData(0);
      let pcm16;
      if (audioCtx.sampleRate === 16000) {
        pcm16 = floatTo16BitPCM(input);
      } else {
        const ds = downsampleBuffer(input, audioCtx.sampleRate, 16000);
        pcm16 = floatTo16BitPCM(ds);
      }

      ws.send(pcm16.buffer);
    };

    source.connect(processor);
    processor.connect(audioCtx.destination);

    isRecording = true;
    recordBtn.textContent = "🎤";   // 🔥 keep mic icon
    recordBtn.classList.add("recording");
  } catch (err) {
    console.error("Mic error:", err);
    statusEl.textContent = "Mic error";
    liveText.innerHTML = "<em>Error</em>";
  }
}

function stopRecording() {
  if (processor) { processor.disconnect(); processor.onaudioprocess = null; processor = null; }
  if (source) { try { source.disconnect(); } catch {} source = null; }
  if (audioCtx) { try { audioCtx.close(); } catch {} audioCtx = null; }
  if (ws && ws.readyState === WebSocket.OPEN) ws.close();

  isRecording = false;
  recordBtn.textContent = "🎤";
  recordBtn.classList.remove("recording");
  statusEl.textContent = "Idle";
  liveText.innerHTML = "<em>Idle</em>";

  // ✅ Show Session Ended banner
  sessionBanner.classList.remove("hidden");

  // Optional: fade out after 3 seconds
  setTimeout(() => {
    sessionBanner.classList.add("fade");
  }, 3000);
}

function floatTo16BitPCM(float32Array) {
  const out = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    let s = Math.max(-1, Math.min(1, float32Array[i]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return out;
}

function downsampleBuffer(buffer, sampleRate, outRate) {
  if (outRate === sampleRate) return buffer;
  const ratio = sampleRate / outRate;
  const newLength = Math.round(buffer.length / ratio);
  const result = new Float32Array(newLength);
  let offsetResult = 0, offsetBuffer = 0;

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
    let accum = 0, count = 0;
    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i];
      count++;
    }
    result[offsetResult] = accum / (count || 1);
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }
  return result;
}
