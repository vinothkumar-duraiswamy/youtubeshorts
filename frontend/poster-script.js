// -----------------------------------------------------
// IMAGE LOADERS
// -----------------------------------------------------
let bgImg = null;
let bottomImg = null;

document.getElementById("bgUpload").addEventListener("change", function (e) {
    let img = new Image();
    img.onload = () => (bgImg = img);
    img.src = URL.createObjectURL(e.target.files[0]);
});

document.getElementById("bottomUpload").addEventListener("change", function (e) {
    let img = new Image();
    img.onload = () => (bottomImg = img);
    img.src = URL.createObjectURL(e.target.files[0]);
});

// -----------------------------------------------------
// TEXT WRAP LEFT
// -----------------------------------------------------
function wrapTextLeft(ctx, text, x, y, maxWidth, lineHeight) {
    if (!text) return;
    let lines = text.split("\n");

    for (let line of lines) {
        let words = line.split(" ");
        let cur = "";

        for (let w of words) {
            let test = cur + w + " ";
            if (ctx.measureText(test).width > maxWidth) {
                ctx.fillText(cur.trim(), x, y);
                y += lineHeight;
                cur = w + " ";
            } else {
                cur = test;
            }
        }

        ctx.fillText(cur.trim(), x, y);
        y += lineHeight;
    }
}

// -----------------------------------------------------
// TEXT WRAP CENTER
// -----------------------------------------------------
function wrapTextCenter(ctx, text, x, y, maxWidth, lineHeight) {
    let lines = text.split("\n");

    for (let line of lines) {
        let words = line.split(" ");
        let cur = "";

        for (let w of words) {
            let test = cur + w + " ";
            if (ctx.measureText(test).width > maxWidth) {
                ctx.fillText(cur.trim(), x, y);
                y += lineHeight;
                cur = w + " ";
            } else {
                cur = test;
            }
        }

        ctx.fillText(cur.trim(), x, y);
        y += lineHeight;
    }

    return y;
}

// -----------------------------------------------------
// MAIN POSTER GENERATOR
// -----------------------------------------------------
function generatePoster() {

    let canvas = document.getElementById("posterCanvas");
    let ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // -------------------------------------------------
    // BACKGROUND - COVER MODE
    // -------------------------------------------------
    if (bgImg) {
        let scale = Math.max(canvas.width / bgImg.width, canvas.height / bgImg.height);
        let newW = bgImg.width * scale;
        let newH = bgImg.height * scale;
        let offsetX = (canvas.width - newW) / 2;
        let offsetY = (canvas.height - newH) / 2;
        ctx.drawImage(bgImg, offsetX, offsetY, newW, newH);
    } else {
        ctx.fillStyle = "black";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // -------------------------------------------------
    // USER INPUTS
    // -------------------------------------------------
    let header = document.getElementById("headerText").value;
    let content = document.getElementById("contentText").value;
    let headerColor = document.getElementById("headerColor").value;
    let contentColor = document.getElementById("contentColor").value;
    let fontFamily = document.getElementById("fontSelect").value;

    let headerSize = parseInt(document.getElementById("headerSize").value);
    let contentSize = parseInt(document.getElementById("contentSize").value);
    let lineSpacing = parseInt(document.getElementById("lineSpacing").value);

    let underlineHeader = document.getElementById("underlineHeader").checked;

    // -------------------------------------------------
    // HEADER
    // -------------------------------------------------
    ctx.fillStyle = headerColor;
    ctx.textAlign = "center";
    ctx.font = `bold ${headerSize}px "${fontFamily}"`;

    let headerEndY = wrapTextCenter(ctx, header, canvas.width / 2, 220, 900, headerSize * 1.1);

    // Underline Header
    if (underlineHeader) {
        ctx.strokeStyle = headerColor;
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(150, headerEndY + 10);
        ctx.lineTo(canvas.width - 150, headerEndY + 10);
        ctx.stroke();
    }

    // -------------------------------------------------
    // CONTENT
    // -------------------------------------------------
    ctx.fillStyle = contentColor;
    ctx.textAlign = "left";
    ctx.font = `${contentSize}px "${fontFamily}"`;
    wrapTextLeft(ctx, content, 120, headerEndY + 80, 860, lineSpacing);

    // -------------------------------------------------
    // BOTTOM IMAGE WITH SOFT MASK (OPTION 3)
    // -------------------------------------------------
    if (bottomImg) {
        let width = 550;
        let height = 550;

        let x = (canvas.width - width) / 2;
        let y = canvas.height - height - 60;

        // Create soft mask
        let maskCanvas = document.createElement("canvas");
        maskCanvas.width = width;
        maskCanvas.height = height;
        let maskCtx = maskCanvas.getContext("2d");

        // Draw oval clip
        maskCtx.save();
        maskCtx.beginPath();

        maskCtx.ellipse(
            width / 2,
            height / 2,
            width * 0.45,
            height * 0.50,
            0, 0, Math.PI * 2
        );

        maskCtx.clip();

        // Draw image into oval
        maskCtx.drawImage(bottomImg, 0, 0, width, height);

        maskCtx.restore();

        // Add feather effect
        maskCtx.globalCompositeOperation = "destination-in";
        let gradient = maskCtx.createRadialGradient(
            width / 2, height / 2, width * 0.20,
            width / 2, height / 2, width * 0.50
        );
        gradient.addColorStop(0, "white");
        gradient.addColorStop(1, "transparent");

        maskCtx.fillStyle = gradient;
        maskCtx.fillRect(0, 0, width, height);

        // Draw final blended portrait
        ctx.drawImage(maskCanvas, x, y);
    }

    // -------------------------------------------------
    // DOWNLOAD POSTER
    // -------------------------------------------------
    let link = document.createElement("a");
    link.download = "poster.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
}
