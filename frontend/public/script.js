const API_BASE = "http://localhost:5000";

const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadLabel = document.getElementById("uploadLabel");
const uploadArea = document.getElementById("uploadArea");
const uploadStatus = document.getElementById("uploadStatus");
const documentsList = document.getElementById("documentsList");

// Load documents on page load
loadDocuments();

// File selection
uploadArea.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    const file = fileInput.files[0];
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext !== "pptx" && ext !== "ppt" && ext !== "pdf") {
      alert("Please select a .pptx, .ppt or .pdf file only.");
      fileInput.value = "";
      return;
    }
    uploadLabel.textContent = file.name;
    uploadArea.classList.add("has-file");
    uploadBtn.disabled = false;
  }
});

// Upload PPT
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!fileInput.files.length) return;

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  uploadBtn.disabled = true;
  uploadBtn.textContent = "Processing...";
  showStatus("Uploading and processing PPT... This may take a moment.", "loading");

  try {
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (res.ok) {
      showStatus(`${data.message} (${data.chunks_created} chunks created)`, "success");
      loadDocuments();
      // Reset upload form
      fileInput.value = "";
      uploadLabel.textContent = "Click to select a .pptx or .pdf file";
      uploadArea.classList.remove("has-file");
    } else {
      showStatus(`Error: ${data.error}`, "error");
    }
  } catch (err) {
    showStatus(`Upload failed: ${err.message}`, "error");
  }

  uploadBtn.disabled = false;
  uploadBtn.textContent = "Upload & Process";
});

// Chat
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = chatInput.value.trim();
  if (!question) return;

  // Add user message
  addMessage(question, "user");
  chatInput.value = "";
  sendBtn.disabled = true;

  // Show typing indicator
  const typingEl = showTyping();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();

    removeTyping(typingEl);

    if (res.ok) {
      addMessage(data.answer, "bot", data.sources);
    } else {
      addMessage(`Error: ${data.error}`, "bot");
    }
  } catch (err) {
    removeTyping(typingEl);
    addMessage(`Failed to get response: ${err.message}`, "bot");
  }

  sendBtn.disabled = false;
  chatInput.focus();
});

// Load documents list
async function loadDocuments() {
  try {
    const res = await fetch(`${API_BASE}/api/documents`);
    const data = await res.json();

    if (data.documents && data.documents.length > 0) {
      documentsList.innerHTML = data.documents
        .map(
          (doc) => `
        <div class="doc-item">
          <div class="doc-info">
            <div class="doc-name">${escapeHtml(doc.filename)}</div>
            <div class="doc-chunks">${doc.chunk_count} chunks</div>
          </div>
          <button class="doc-delete" onclick="deleteDocument('${escapeHtml(doc.filename)}')" title="Delete">&#10005;</button>
        </div>
      `
        )
        .join("");
    } else {
      documentsList.innerHTML = '<p class="empty-state">No documents uploaded</p>';
    }
  } catch (err) {
    documentsList.innerHTML = '<p class="empty-state">Failed to load documents</p>';
  }
}

// Delete document
async function deleteDocument(filename) {
  if (!confirm(`Delete "${filename}" and all its embeddings?`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/documents/${encodeURIComponent(filename)}`, {
      method: "DELETE",
    });
    const data = await res.json();

    if (res.ok) {
      loadDocuments();
    } else {
      alert(`Error: ${data.error}`);
    }
  } catch (err) {
    alert(`Delete failed: ${err.message}`);
  }
}

// UI Helpers
function addMessage(content, type, sources) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${type}-message`;

  let html = `<div class="message-content">${escapeHtml(content)}</div>`;

  if (sources && sources.length > 0) {
    const sourceLabels = sources
      .map((s) => `<span>${escapeHtml(s.filename)} - Page ${s.page_number}</span>`)
      .join("");
    html += `<div class="message-sources">Sources: ${sourceLabels}</div>`;
  }

  msgDiv.innerHTML = html;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
  const typingDiv = document.createElement("div");
  typingDiv.className = "message bot-message";
  typingDiv.innerHTML = `
    <div class="typing-indicator">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
  `;
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return typingDiv;
}

function removeTyping(el) {
  if (el && el.parentNode) {
    el.parentNode.removeChild(el);
  }
}

function showStatus(message, type) {
  uploadStatus.textContent = message;
  uploadStatus.className = `status-message ${type}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}
