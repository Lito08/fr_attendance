/* multi-pose enrol: front, L, R, up, down */
(async () => {
  const v   = document.getElementById("cam");
  const btn = document.getElementById("startBtn");
  const api = btn.dataset.api;
  const p   = document.getElementById("prompt");
  const st  = document.getElementById("status");

  v.srcObject = await navigator.mediaDevices.getUserMedia({ video: true });

  const steps = [
    { msg: "Face camera",    check: () => true },
    { msg: "Turn LEFT",      check: yaw => yaw < -12 },
    { msg: "Turn RIGHT",     check: yaw => yaw >  12 },
    { msg: "Look UP",        check: (_, pitch) => pitch > -15 },
    { msg: "Look DOWN",      check: (_, pitch) => pitch > -13 }
  ];

  const frames = [];
  let i = 0;

  /* --- pose detection via FaceMesh (same thresholds as recognise) --- */
  const fm = new FaceMesh({
    locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`
  });
  fm.setOptions({ maxNumFaces: 1, refineLandmarks: true });

  function yawPitch(lm) {
    const rel   = ((lm[1].x - lm[234].x) / (lm[454].x - lm[234].x)) * 2 - 1;
    const yaw   = rel * 30;
    const pitch = (lm[1].y - lm[152].y) * 100;
    return [yaw, pitch];
  }

  fm.onResults(({ multiFaceLandmarks }) => {
    if (!multiFaceLandmarks.length) return;
    const [yaw, pitch] = yawPitch(multiFaceLandmarks[0]);

    if (!steps[i].check(yaw, pitch)) return;

    /* capture six frames for this pose */
    const c   = document.createElement("canvas");
    const ctx = c.getContext("2d");
    c.width   = v.videoWidth;
    c.height  = v.videoHeight;

    for (let j = 0; j < 6; j++) {
      ctx.drawImage(v, 0, 0);
      frames.push(c.toDataURL("image/jpeg"));
    }

    i++;
    if (i < steps.length) {
      p.textContent = steps[i].msg;
    } else {
      p.textContent = "Uploading…";
      submit();
    }
  });

  async function submit() {
    const r = await fetch(api, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": "{{ csrf_token }}"
      },
      body: JSON.stringify({ frames })
    }).then(r => r.json());

    if (r.ok) location.href = r.redirect;
    else { p.textContent = r.error || "Error"; btn.disabled = false; }
  }

  btn.onclick = () => {
    btn.disabled = true;
    p.textContent = steps[0].msg;
    new Camera(v, { onFrame: async () => fm.send({ image: v }) }).start();
  };
})();
