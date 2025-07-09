const canvas = document.getElementById("qrCanvas");
const ctx = canvas.getContext("2d");

let logoImg = new Image();
let logoData = "";
let logoPos = { x: 170, y: 170, w: 60, h: 60 };
let textPos = { x: 130, y: 450 };
let draggingLogo = false, draggingText = false;
let qrURL = "";
let qrImage = new Image();

function generateQRCode(callback) {
  const ssid = document.getElementById("ssid").value.trim();
  const password = document.getElementById("password").value.trim();
  if (!ssid || !password) return;

  const qrData = `WIFI:T:WPA;S:${ssid};P:${password};;;`;

  QRCode.toDataURL(qrData, {
    margin: 1,
    scale: 10,
    color: {
      dark: document.getElementById("fgColor").value,
      light: document.getElementById("bgColor").value
    }
  }, (err, url) => {
    if (err) return;
    qrURL = url;
    qrImage.onload = () => {
      drawCanvas();
      if (callback) callback();
    };
    qrImage.src = url;
  });
}

function drawCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const bgColor = document.getElementById("bgColor").value;
  const borderColor = document.getElementById("borderColor").value;
  const borderThickness = parseInt(document.getElementById("borderThickness").value) || 0;
  const addBorder = document.getElementById("borderToggle").checked;

  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const qrX = 50;
  const qrY = 50;
  const qrSize = 300;

  if (qrURL) {
    ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize);

    if (addBorder && borderThickness > 0) {
      ctx.strokeStyle = borderColor;
      ctx.lineWidth = borderThickness;
      ctx.strokeRect(
        qrX - borderThickness / 2,
        qrY - borderThickness / 2,
        qrSize + borderThickness,
        qrSize + borderThickness
      );
    }
  }

  if (logoImg.src && logoImg.complete) {
    ctx.drawImage(logoImg, logoPos.x, logoPos.y, logoPos.w, logoPos.h);
  }

  ctx.fillStyle = document.getElementById("scanTextColor").value;
  ctx.font = `${document.getElementById("scanFontSize").value}px Arial`;
  ctx.fillText(document.getElementById("scanText").value, textPos.x, textPos.y);
}

document.querySelectorAll("input").forEach(input => {
  input.addEventListener("input", () => generateQRCode());
  input.addEventListener("change", () => generateQRCode());
});

document.getElementById("logo").addEventListener("change", function (e) {
  const reader = new FileReader();
  reader.onload = function (evt) {
    logoData = evt.target.result;
    logoImg.onload = drawCanvas;
    logoImg.src = logoData;
  };
  reader.readAsDataURL(e.target.files[0]);
});

canvas.addEventListener("mousedown", function (e) {
  let mx = e.offsetX, my = e.offsetY;
  if (mx >= logoPos.x && mx <= logoPos.x + logoPos.w && my >= logoPos.y && my <= logoPos.y + logoPos.h) {
    draggingLogo = true;
  } else if (mx >= textPos.x - 50 && mx <= textPos.x + 200 && my >= textPos.y - 30 && my <= textPos.y + 10) {
    draggingText = true;
  }
});

canvas.addEventListener("mousemove", function (e) {
  if (draggingLogo) {
    logoPos.x = e.offsetX - logoPos.w / 2;
    logoPos.y = e.offsetY - logoPos.h / 2;
    drawCanvas();
  } else if (draggingText) {
    textPos.x = e.offsetX - 50;
    textPos.y = e.offsetY;
    drawCanvas();
  }
});

canvas.addEventListener("mouseup", () => {
  draggingLogo = false;
  draggingText = false;
});

function handleSave() {
  sessionStorage.setItem("persist_qr", canvas.toDataURL("image/png"));
  sessionStorage.setItem("ssid", document.getElementById("ssid").value);
  sessionStorage.setItem("password", document.getElementById("password").value);
  sessionStorage.setItem("fgColor", document.getElementById("fgColor").value);
  sessionStorage.setItem("bgColor", document.getElementById("bgColor").value);
  sessionStorage.setItem("scanText", document.getElementById("scanText").value);
  sessionStorage.setItem("scanTextColor", document.getElementById("scanTextColor").value);
  sessionStorage.setItem("scanFontSize", document.getElementById("scanFontSize").value);
  sessionStorage.setItem("borderToggle", document.getElementById("borderToggle").checked);
  sessionStorage.setItem("borderColor", document.getElementById("borderColor").value);
  sessionStorage.setItem("borderThickness", document.getElementById("borderThickness").value);
  if (logoData) {
    sessionStorage.setItem("logoData", logoData);
  }

  fetch('/auth/status')
    .then(res => res.json())
    .then(data => {
      if (!data.logged_in) {
        document.getElementById("login-required-alert").style.display = "block";
        document.getElementById("downloadLink").style.display = "none";
      } else {
        document.getElementById("login-required-alert").style.display = "none";
        saveQRCode();
      }
    })
    .catch(() => {
      document.getElementById("login-required-alert").style.display = "block";
      document.getElementById("downloadLink").style.display = "none";
    });
}

function saveQRCode() {
  drawCanvas();

  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/qr/generate";

  ["ssid", "password", "scanText"].forEach(id => {
    const input = document.createElement("input");
    input.name = id === "scanText" ? "scan_text" : id;
    input.value = document.getElementById(id).value;
    form.appendChild(input);
  });

  const imgInput = document.createElement("input");
  imgInput.name = "canvas_data";
  imgInput.value = canvas.toDataURL("image/png");
  form.appendChild(imgInput);

  document.body.appendChild(form);
  form.submit();
}

function resetStylesOnly() {
  document.getElementById("fgColor").value = "#000000";
  document.getElementById("bgColor").value = "#ffffff";
  document.getElementById("scanText").value = "SCAN ME";
  document.getElementById("scanTextColor").value = "#000000";
  document.getElementById("scanFontSize").value = 28;
  document.getElementById("borderToggle").checked = false;
  document.getElementById("borderColor").value = "#000000";
  document.getElementById("borderThickness").value = 10;

  logoData = "";
  logoImg = new Image();
  logoPos = { x: 170, y: 170, w: 60, h: 60 };
  textPos = { x: 130, y: 450 };
  document.getElementById("logo").value = "";

  // Regenerate QR in black on white
  const ssid = document.getElementById("ssid").value.trim();
  const password = document.getElementById("password").value.trim();
  if (!ssid || !password) {
    drawCanvas();
    return;
  }

  const qrData = `WIFI:T:WPA;S:${ssid};P:${password};;;`;

  QRCode.toDataURL(qrData, {
    margin: 1,
    scale: 10,
    color: {
      dark: "#000000",
      light: "#ffffff"
    }
  }, (err, url) => {
    if (err) return;
    qrURL = url;
    qrImage.onload = drawCanvas;
    qrImage.src = url;
  });
}

window.onload = () => {
  fetch("/auth/status")
    .then(res => res.json())
    .then(data => {
      const savedQR = sessionStorage.getItem("persist_qr");
      const ssid = sessionStorage.getItem("ssid");
      const password = sessionStorage.getItem("password");

      if (savedQR && ssid && password) {
        qrURL = savedQR;
        qrImage.onload = () => {
          drawCanvas();
          if (data.logged_in) {
            document.getElementById("downloadLink").style.display = "block";
          }
        };
        qrImage.src = savedQR;

        document.getElementById("ssid").value = ssid;
        document.getElementById("password").value = password;
        document.getElementById("fgColor").value = sessionStorage.getItem("fgColor") || "#000000";
        document.getElementById("bgColor").value = sessionStorage.getItem("bgColor") || "#ffffff";
        document.getElementById("scanText").value = sessionStorage.getItem("scanText") || "SCAN ME";
        document.getElementById("scanTextColor").value = sessionStorage.getItem("scanTextColor") || "#000000";
        document.getElementById("scanFontSize").value = sessionStorage.getItem("scanFontSize") || 28;
        document.getElementById("borderToggle").checked = sessionStorage.getItem("borderToggle") === "true";
        document.getElementById("borderColor").value = sessionStorage.getItem("borderColor") || "#000000";
        document.getElementById("borderThickness").value = sessionStorage.getItem("borderThickness") || 10;

        const savedLogo = sessionStorage.getItem("logoData");
        if (savedLogo) {
          logoData = savedLogo;
          logoImg.onload = drawCanvas;
          logoImg.src = savedLogo;
        }

        sessionStorage.clear();
      }

      generateQRCode();
    });
};

document.getElementById("resetBtn").addEventListener("click", resetStylesOnly);

const downloadLink = document.getElementById("downloadLink");
if (downloadLink) {
  downloadLink.addEventListener("click", () => {
    const img = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = img;
    a.download = "qr-code.png";
    a.click();
  });

  downloadLink.style.display = "none";
}

