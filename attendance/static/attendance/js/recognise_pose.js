(async () => {
  const v=document.getElementById("cam"), prompt=document.getElementById("prompt"),
        status=document.getElementById("status");

  await faceapi.nets.tinyFaceDetector.loadFromUri("/static/models");
  await faceapi.nets.faceLandmark68TinyNet.loadFromUri("/static/models");
  v.srcObject = await navigator.mediaDevices.getUserMedia({video:true});

  const steps=["look left","look right","look up"]; let i=0; prompt.textContent=steps[i];
  const cvs=document.createElement("canvas"), ctx=cvs.getContext("2d",{willReadFrequently:true});
  const yawPitch=d=>{const p=d.landmarks.positions, yaw=(p[16].x-p[0].x);
    const rel=((p[30].x-p[0].x)/yaw)*2-1; const pitch=(p[27].y-p[30].y); return [rel*30,pitch*0.8];};

  setInterval(async()=>{
    if(!v.videoWidth) return;
    const det=await faceapi.detectSingleFace(v,new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks(true);
    if(!det) return;
    const [yaw,pitch]=yawPitch(det);
    const ok=(i===0&&yaw<-15)||(i===1&&yaw>15)||(i===2&&pitch>12);
    if(!ok) return;

    i++; if(i<steps.length){prompt.textContent=steps[i]; return;}

    cvs.width=v.videoWidth; cvs.height=v.videoHeight; ctx.drawImage(v,0,0);
    fetch("{% url 'recognise_api' %}",{
      method:"POST",
      headers:{"X-Frame-Data":cvs.toDataURL("image/jpeg"),"X-Live":"1"}
    }).then(r=>r.json()).then(r=>{
      if(r.match){status.textContent=`✅ ${r.name} marked present`; status.className="text-success fw-bold mt-2";}
      else{status.textContent="❌ Unknown face"; status.className="text-danger fw-bold mt-2";}
    });
    prompt.textContent=""; i=0;
  },800);
})();
