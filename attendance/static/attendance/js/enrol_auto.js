/* multi‐pose enrol with live stats sidebar */
(async () => {
  // DOM refs
  const v        = document.getElementById("cam");
  const btn      = document.getElementById("startBtn");
  const api      = btn.dataset.api;
  const promptEl = document.getElementById("prompt");
  const statusEl = document.getElementById("status");
  const bar      = document.getElementById("enrolProgress");

  // Stats elements
  const statStep     = document.getElementById("stat-step");
  const statMsg      = document.getElementById("stat-msg");
  const statYaw      = document.getElementById("stat-yaw");
  const statPitch    = document.getElementById("stat-pitch");
  const statProgress = document.getElementById("stat-progress");

  // capture config
  const FRAMES_PER_POSE = 6;
  const TOTAL_FRAMES    = 5 * FRAMES_PER_POSE;

  // FaceMesh thresholds
  const YAW_LEFT  = -12;
  const YAW_RIGHT =  12;
  const PITCH_UP  = -13;   // negative = up
  const PITCH_DOWN=  13;   // positive = down

  // prompts & checks
  const steps = [
    { msg: "Face camera", check: () => true },
    { msg: "Turn LEFT",   check: yaw   => yaw < YAW_LEFT   },
    { msg: "Turn RIGHT",  check: yaw   => yaw > YAW_RIGHT  },
    { msg: "Look UP",     check: (_,p) => p   < PITCH_UP  },
    { msg: "Look DOWN",   check: (_,p) => p   > PITCH_DOWN }
  ];

  let frames = [], i = 0;

  // start webcam
  v.srcObject = await navigator.mediaDevices.getUserMedia({ video: true });

  // MediaPipe setup
  const fm = new FaceMesh({
    locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`
  });
  fm.setOptions({ maxNumFaces:1, refineLandmarks:true });

  // extract yaw & pitch from landmarks
  function yawPitch(lm) {
    const relX  = ((lm[1].x - lm[234].x) / (lm[454].x - lm[234].x)) *2 -1;
    const yaw   = relX * 30;
    const pitch = (lm[1].y - lm[152].y)*100;
    return [yaw, pitch];
  }

  fm.onResults(({ multiFaceLandmarks }) => {
    if (!multiFaceLandmarks.length) {
      statusEl.textContent = "No face…";
      return;
    }

    const [yaw, pitch] = yawPitch(multiFaceLandmarks[0]);

    // Update stats sidebar
    statStep.textContent     = `${i+1}/${steps.length}`;
    statMsg.textContent      = steps[i].msg;
    statYaw.textContent      = yaw.toFixed(1);
    statPitch.textContent    = pitch.toFixed(1);

    // console debug
    console.log(
      `[Enrol][${i}] ${steps[i].msg} → yaw=${yaw.toFixed(1)}, pitch=${pitch.toFixed(1)}`
    );

    // pose check
    if (!steps[i].check(yaw, pitch)) return;

    // capture FRAMES_PER_POSE frames
    const c   = document.createElement("canvas");
    const ctx = c.getContext("2d");
    c.width  = v.videoWidth; c.height = v.videoHeight;

    for (let j = 0; j < FRAMES_PER_POSE; j++) {
      ctx.drawImage(v, 0, 0);
      frames.push(c.toDataURL("image/jpeg"));
    }

    // update progress
    const pct = Math.round((frames.length / TOTAL_FRAMES)*100);
    bar.style.width       = `${pct}%`;
    bar.textContent       = `${pct}%`;
    statProgress.textContent = pct;

    // advance or upload
    i++;
    if (i < steps.length) {
      promptEl.textContent = steps[i].msg;
    } else {
      promptEl.textContent = "Uploading…";
      submit();
    }
  });

  async function submit() {
    btn.disabled = true;
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
        promptEl.textContent = data.error || "Enrol failed";
        btn.disabled        = false;
      }
    } catch {
      promptEl.textContent = "Network error";
      btn.disabled        = false;
    }
  }

  // kick off on button click
  btn.onclick = () => {
    frames = []; i = 0;
    bar.style.width     = "0%";
    bar.textContent     = "0%";
    statProgress.textContent = "0";
    promptEl.textContent= steps[0].msg;
    statusEl.textContent= "";
    btn.disabled        = true;

    new Camera(v, { onFrame: async ()=> fm.send({ image: v }) }).start();
  };
})();
