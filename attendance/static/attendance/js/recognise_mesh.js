(async () => {
  const videoEl = document.getElementById("cam");
  const promptEl = document.getElementById("prompt");
  const statusEl = document.getElementById("status");
  const apiUrl   = videoEl.dataset.api;

  // 1) start webcam
  videoEl.srcObject = await navigator.mediaDevices.getUserMedia({ video:true });

  // 2) set up FaceMesh (UMD v0.4)
  const faceMesh = new FaceMesh.FaceMesh({
    locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4/${f}`
  });
  faceMesh.setOptions({ maxNumFaces:1, refineLandmarks:true });

  const steps = ["look left", "look right", "look up"];
  let stepIdx = 0;
  promptEl.textContent = steps[stepIdx];

  function computeYawPitch(landmarks) {
    const rel   = ((landmarks[1].x - landmarks[234].x) /
                   (landmarks[454].x - landmarks[234].x)) * 2 - 1;
    const yaw   = rel * 30;
    const pitch = (landmarks[1].y - landmarks[152].y) * 100;
    return [yaw, pitch];
  }

  faceMesh.onResults(({ multiFaceLandmarks }) => {
    if (!multiFaceLandmarks.length) {
      statusEl.textContent = "No face…";
      return;
    }
    const [yaw, pitch] = computeYawPitch(multiFaceLandmarks[0]);
    statusEl.textContent = `yaw ${yaw.toFixed(1)}°, pitch ${pitch.toFixed(1)}°`;

    const ok =
      (stepIdx === 0 && yaw  < -12) ||
      (stepIdx === 1 && yaw  >  12) ||
      (stepIdx === 2 && pitch <  -5);

    if (!ok) return;

    stepIdx++;
    if (stepIdx < steps.length) {
      promptEl.textContent = steps[stepIdx];
      return;
    }

    // all done → capture & send
    promptEl.textContent = "";
    statusEl.textContent = "Processing… please hold still";

    const canvas = document.createElement("canvas");
    canvas.width  = videoEl.videoWidth;
    canvas.height = videoEl.videoHeight;
    canvas.getContext("2d").drawImage(videoEl, 0, 0);

    fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify({ frame: canvas.toDataURL("image/jpeg"), live:1 })
    })
    .then(r => r.json())
    .then(data => {
      if (data.match) {
        document.getElementById("toastMsg").textContent = `${data.name} marked present`;
        bootstrap.Toast.getOrCreateInstance(
          document.getElementById("recToast")
        ).show();
        statusEl.textContent = "";
      } else {
        promptEl.textContent = "❌ Unknown face";
        promptEl.className   = "text-danger fw-bold";
      }
    })
    .catch(() => statusEl.textContent = "Error contacting server")
    .finally(() => stepIdx = 0);
  });

  // 3) wire up the camera helper
  new Camera(videoEl, { onFrame: async () => await faceMesh.send({ image:videoEl }) }).start();
})();
