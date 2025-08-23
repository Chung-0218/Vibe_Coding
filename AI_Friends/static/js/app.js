async function postForm(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData });
  if (!res.ok) throw new Error('Request failed');
  return res;
}

function appendMessage(role, text, imageUrl) {
  const messages = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = `message ${role}`;
  el.innerHTML = `
    <div class="avatar"></div>
    <div class="bubble">
      ${imageUrl ? `<img src="${imageUrl}" class="rounded-lg mb-2 max-w-xs"/>` : ''}
      <div>${text.replace(/\n/g, '<br/>')}</div>
    </div>
  `;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

document.getElementById('sendBtn').addEventListener('click', async () => {
  const input = document.getElementById('textInput');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  appendMessage('user', text);
  const fd = new FormData();
  fd.append('text', text);
  const res = await postForm('/api/chat', fd);
  const data = await res.json();
  appendMessage('ai', data.reply);
});

document.getElementById('speakBtn').addEventListener('click', async () => {
  const text = document.getElementById('ttsText').value.trim();
  if (!text) return;
  const fd = new FormData();
  fd.append('text', text);
  const res = await postForm('/api/voice', fd);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const player = document.getElementById('audioPlayer');
  player.src = url;
  player.play();
});

// 음성 녹음 → 전사(STT)
let mediaRecorder;
let recordedChunks = [];
const recBtn = document.getElementById('recBtn');
recBtn?.addEventListener('click', async () => {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    recordedChunks = [];
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedChunks.push(e.data);
    };
    mediaRecorder.onstop = async () => {
      const blob = new Blob(recordedChunks, { type: 'audio/webm' });
      const fd = new FormData();
      fd.append('file', blob, 'speech.webm');
      const res = await postForm('/api/transcribe', fd);
      const data = await res.json();
      document.getElementById('sttResult').value = data.text || '';
    };
    mediaRecorder.start();
    recBtn.textContent = '🛑 녹음 종료';
  } else if (mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    recBtn.textContent = '🎙️ 녹음 시작';
  }
});

document.getElementById('sendFromSttBtn')?.addEventListener('click', async () => {
  const text = document.getElementById('sttResult').value.trim();
  if (!text) return;
  appendMessage('user', text);
  const fd = new FormData();
  fd.append('text', text);
  const res = await postForm('/api/chat', fd);
  const data = await res.json();
  appendMessage('ai', data.reply);
});

// 이미지 업로드 + 프롬프트
const imageInput = document.getElementById('imageFile');
const preview = document.getElementById('preview');
imageInput.addEventListener('change', async (e) => {
  const f = e.target.files?.[0];
  if (!f) return;
  const fd = new FormData();
  fd.append('file', f);
  const res = await postForm('/api/upload-image', fd);
  const data = await res.json();
  preview.src = data.image_url;
  preview.classList.remove('hidden');
  preview.dataset.url = data.image_url;
});

document.getElementById('imageSendBtn').addEventListener('click', async () => {
  const text = document.getElementById('imageText').value.trim();
  const imgUrl = preview.dataset.url;
  if (!text && !imgUrl) return;
  appendMessage('user', text || '(이미지와 함께)', imgUrl);
  const fd = new FormData();
  fd.append('text', text);
  if (imgUrl) fd.append('image_url', imgUrl);
  const res = await postForm('/api/chat', fd);
  const data = await res.json();
  appendMessage('ai', data.reply);
});

// 추천 프롬프트 버튼
document.querySelectorAll('.chip').forEach((btn) => {
  btn.addEventListener('click', () => {
    const prompt = btn.getAttribute('data-prompt');
    const input = document.getElementById('textInput');
    input.value = prompt;
    input.focus();
  });
});


