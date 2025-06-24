/* yaw-only, 3-pose enrol: front ←→ left ←→ right */
(async () => {
  const v    = document.getElementById("cam");
  const btn  = document.getElementById("startBtn");
  const api  = btn.dataset.api;
  const p    = document.getElementById("prompt");
  const st   = document.getElementById("status");
  const bar  = document.getElementById("enrolProgress");
  const sStep= document.getElementById("stat-step");
  const sYaw = document.getElementById("stat-yaw");
  const sProg= document.getElementById("stat-progress");

  // each pose: 6 frames
  const FRAMES_PER_POSE = 6;
  const TOTAL_FRAMES    = 3 * FRAMES_PER_POSE;

  // start camera
  v.srcObject = await navigator.mediaDevices.getUserMedia({ video: true });

  // define only yaw-based steps
  const steps = [
    { msg: "Face camera",    check: yaw => Math.abs(yaw) < 10 },
    { msg: "Turn LEFT",      check: yaw => yaw < -12 },
    { msg: "Turn RIGHT",     check: yaw => yaw > 12 }
  ];

  let frames = [], i = 0;

  // load FaceMesh (pin to 0.4 so assets resolve)
  const fm = new FaceMesh({
    locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4/${f}`
  });
  fm.setOptions({ maxNumFaces: 1, refineLandmarks: true });

  const yawFromLandmarks = lm => {
    const rel = ((lm[1].x - lm[234].x) / (lm[454].x - lm[234].x)) * 2 - 1;
    return rel * 30;
  };

  fm.onResults(({ multiFaceLandmarks }) => {
    if (!multiFaceLandmarks.length) return;
    const yaw = yawFromLandmarks(multiFaceLandmarks[0]);

    // update stats
    sStep.textContent     = `${i+1}/${steps.length}`;
    sYaw.textContent      = yaw.toFixed(1);
    const progPct = Math.round((frames.length / TOTAL_FRAMES) * 100);
    sProg.textContent    = `${progPct}%`;
    bar.style.width       = `${progPct}%`;
    bar.textContent       = `${progPct}%`;

    // check pose
    if (!steps[i].check(yaw)) return;

    // capture FRAMES_PER_POSE frames
    const c = document.createElement("canvas"), ctx = c.getContext("2d");
    c.width  = v.videoWidth; c.height = v.videoHeight;
    for (let j = 0; j < FRAMES_PER_POSE; j++) {
      ctx.drawImage(v, 0, 0);
      frames.push(c.toDataURL("image/jpeg"));
    }

    // next step or submit
    i++;
    if (i < steps.length) {
      p.textContent = steps[i].msg;
    } else {
      p.textContent = "Uploading…";
      submit();
    }
  });

  async function submit() {
    btn.disabled = true;
    st.textContent = "";
    try {
      const res  = await fetch(api, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken":  "{{ csrf_token }}"
        },
        body: JSON.stringify({ frames })
      });
      const data = await res.json();
      if (data.ok) window.location = data.redirect;
      else {
        p.textContent = data.error || "Enrol failed";
        btn.disabled  = false;
      }
    } catch (e) {
      console.error(e);
      p.textContent = "Network error";
      btn.disabled  = false;
    }
  }

  btn.onclick = () => {
    // reset
    frames = []; i = 0;
    p.textContent    = steps[0].msg;
    sStep.textContent= `0/${steps.length}`;
    sYaw.textContent = "0.0";
    sProg.textContent= "0%";
    bar.style.width  = "0%"; bar.textContent = "0%";
    st.textContent   = "";
    btn.disabled     = true;

    // start mediapipe camera loop
    new Camera(v, { onFrame: async () => fm.send({ image: v }) }).start();
  };
})();
