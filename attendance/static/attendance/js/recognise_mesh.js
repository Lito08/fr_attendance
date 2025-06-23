/* Head-pose liveness with MediaPipe FaceMesh – no eval */
(async () => {
  const v  = document.getElementById("cam");
  const p  = document.getElementById("prompt");
  const s  = document.getElementById("status");
  const api = v.dataset.api;                  // URL from data-attribute

  /* start webcam */
  v.srcObject = await navigator.mediaDevices.getUserMedia({ video: true });

  /* load FaceMesh */
  const fm = new FaceMesh({
    locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`
  });
  fm.setOptions({ maxNumFaces: 1, refineLandmarks: true });

  const steps = ["look left", "look right", "look up"];
  let i = 0;
  p.textContent = steps[i];

  function yawPitch(lm) {
    const rel = ((lm[1].x - lm[234].x) / (lm[454].x - lm[234].x)) * 2 - 1;
    const yaw = rel * 30;
    const pitch = (lm[1].y - lm[152].y) * 100;
    return [yaw, pitch];
  }

fm.onResults(({ multiFaceLandmarks }) => {
  if (!multiFaceLandmarks.length) {
    s.textContent = "No face…";
    return;
  }

  const [yaw, pitch] = yawPitch(multiFaceLandmarks[0]);
  s.textContent = `yaw ${yaw}°, pitch ${pitch}°`;

  const ok =
    (i === 0 && yaw < -12) ||
    (i === 1 && yaw >  12) ||
    (i === 2 && pitch < -5);

  if (!ok) return;

  i++;
  if (i < steps.length) {
    p.textContent = steps[i];
    return;
  }

  // ─── all three done: show processing indicator ───────────────
  p.textContent = "";
  s.textContent = "Processing… please hold still";

  // capture frame
  const c = document.createElement("canvas"), ctx = c.getContext("2d");
  c.width = v.videoWidth; c.height = v.videoHeight;
  ctx.drawImage(v, 0, 0);

  // send to API
  fetch(api, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      frame: c.toDataURL("image/jpeg"),
      live:  1
    })
  })
  .then(r => r.json())
  .then(r => {
    if (r.match) {
      document.getElementById("toastMsg").textContent =
        `${r.name} marked present`;
      bootstrap.Toast.getOrCreateInstance(
        document.getElementById("recToast")
      ).show();
      s.textContent = "";   // clear status on success
    } else {
      p.textContent = "❌ Unknown face";
      p.className   = "text-danger fw-bold";
      s.textContent = "";   // clear or keep error in prompt
    }
  })
  .catch(err => {
    console.error(err);
    s.textContent = "Error contacting server";
  })
  .finally(() => {
    i = 0;              // reset for next person
  });
});


  /* feed webcam frames to FaceMesh */
  new Camera(v, { onFrame: async () => fm.send({ image: v }) }).start();
})();
