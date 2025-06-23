// captures 30 frames while user turns head; sends array of JPEGs to /enrol/
(async () => {
  const video  = document.getElementById("cam");
  const ring   = document.getElementById("ring");
  const start  = document.getElementById("startBtn");
  const status = document.getElementById("status");

  await faceapi.nets.tinyFaceDetector.loadFromUri("/static/models");
  await faceapi.nets.faceLandmark68TinyNet.loadFromUri("/static/models");

  video.srcObject = await navigator.mediaDevices.getUserMedia({ video:true });

  const canvas = document.createElement("canvas"), ctx = canvas.getContext("2d");
  let frames = [];

  start.onclick = async () => {
    start.disabled = true; status.textContent = "Move head slowly in a circle…";
    const target = 30, step = 360/target;
    let nextAngle = 0;

    const interval = setInterval(async () => {
      if (!video.videoWidth) return;
      canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      ctx.drawImage(video,0,0);

      const det = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
                                .withFaceLandmarks(true);
      if (!det) return;

      // Estimate yaw (left-right) & pitch (up-down) from landmarks
      const lm = det.landmarks.positions;
      const yaw  = (lm[16].x - lm[0].x);           // crude horizontal span
      const nose = lm[30].x;
      const rel  = (nose - lm[0].x) / yaw;         // 0 = far left, 1 = far right
      const angle = (rel * 180) + 90;              // map 0–180 → 0–180°, add 90

      if (angle >= nextAngle - step/2) {
        ring.style.strokeDashoffset = (1 - angle/360) * 283;  // 283 = 2πr (r=45)
        frames.push(canvas.toDataURL("image/jpeg"));
        nextAngle += step;
      }

      if (frames.length >= target) {
        clearInterval(interval);
        status.textContent = "Uploading…";
        const resp = await fetch("", {              // POST back to same URL
          method:"POST",
          headers:{ "X-CSRFToken":start.dataset.csrf },
          body:JSON.stringify({frames})});
        const r = await resp.json();
        status.textContent = r.ok ? "✅ Enrolled!" : r.error;
        if (r.redirect) window.location = r.redirect;
      }
    }, 100);
  };
})();
