(async () => {
  const v=document.getElementById("cam"), ring=document.getElementById("ring"),
        btn=document.getElementById("startBtn"), status=document.getElementById("status");

  await faceapi.nets.tinyFaceDetector.loadFromUri("/static/models");
  await faceapi.nets.faceLandmark68TinyNet.loadFromUri("/static/models");
  v.srcObject = await navigator.mediaDevices.getUserMedia({video:true});

  const cvs=document.createElement("canvas"), ctx=cvs.getContext("2d",{willReadFrequently:true});
  let frames=[], target=30, step=360/target, next=0;

  btn.onclick = () => {
    btn.disabled=true; status.textContent="Move head slowly in a circle…";
    const loop=setInterval(async()=>{
      if(!v.videoWidth) return;
      const det=await faceapi.detectSingleFace(v,new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks(true);
      if(!det) return;
      const p=det.landmarks.positions, yaw=(p[16].x-p[0].x),
            rel=((p[30].x-p[0].x)/yaw)*2-1, angle=rel*180+90;
      if(angle>=next-step/2){
        ring.style.strokeDashoffset=(1-angle/360)*283;
        cvs.width=v.videoWidth; cvs.height=v.videoHeight; ctx.drawImage(v,0,0);
        frames.push(cvs.toDataURL("image/jpeg")); next+=step;
      }
      if(frames.length>=target){
        clearInterval(loop); status.textContent="Uploading…";
        fetch("",{method:"POST",headers:{"X-CSRFToken":btn.dataset.csrf},
          body:JSON.stringify({frames})})
        .then(r=>r.json()).then(r=>{
          status.textContent=r.ok?"✅ Enrolled!":r.error;
          if(r.redirect) window.location=r.redirect;
        });
      }
    },100);
  };
})();
