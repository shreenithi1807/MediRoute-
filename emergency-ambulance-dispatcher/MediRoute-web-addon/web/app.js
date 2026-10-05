
const message = document.getElementById("message");
const documentInput = document.getElementById("document");
const button = document.getElementById("analyze");
const answer = document.getElementById("answer");
const loading = document.getElementById("loading");
const status = document.getElementById("status");
const model = document.getElementById("model");

fetch("/api/health")
  .then(r => r.json())
  .then(() => status.textContent = "MediRoute online")
  .catch(() => status.textContent = "Offline");

button.addEventListener("click", async () => {
  const text = message.value.trim();
  const file = documentInput.files[0];

  if (!text && !file) {
    answer.textContent = "Enter a situation or upload a document.";
    return;
  }

  const form = new FormData();
  form.append("message", text);
  if (file) form.append("document", file);

  button.disabled = true;
  loading.hidden = false;
  answer.textContent = "";
  model.textContent = "";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: form,
    });
    const result = await response.json();

    if (!result.ok) {
      answer.textContent = "Error: " + result.error;
      return;
    }

    answer.textContent = result.answer || "Claude returned no text.";
    model.textContent = result.model || "";
  } catch (error) {
    answer.textContent = "Connection error: " + error.message;
  } finally {
    button.disabled = false;
    loading.hidden = true;
  }
});
