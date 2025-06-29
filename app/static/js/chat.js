function toggleChatPanel() {
    const panel = document.getElementById("chat-panel");
    const dot = document.getElementById("new-msg-dot");
  
    if (panel.style.display === "none" || panel.style.display === "") {
      panel.style.display = "block";
      dot.style.display = "none"; // clear dot when opened
      fetch('/chat/has_new'); // optional, not required for marking as read
    } else {
      panel.style.display = "none";
    }
  }
  
  document.addEventListener("DOMContentLoaded", function () {
    const dot = document.getElementById("new-msg-dot");
  
    fetch('/chat/has_new')
      .then(res => res.json())
      .then(data => {
        if (data.new_messages) {
          dot.style.display = "block";
        }
      });
  });
  