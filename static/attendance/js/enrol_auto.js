/* multi-pose enrol with live stats sidebar */
(async () => {

  // FaceMesh thresholds
  const YAW_LEFT  = -12;
  const YAW_RIGHT =  12;
  const PITCH_UP  = -13;   // negative = up

  /* BEGIN PATCH – only yaw poses */
  const steps = [
    { msg: "Face camera", check: ()         => true          },
    { msg: "Turn LEFT",   check: yaw        => yaw < YAW_LEFT },
    { msg: "Turn RIGHT",  check: yaw        => yaw > YAW_RIGHT }
  ];
  const FRAMES_PER_POSE = 6;
  const TOTAL_FRAMES    = steps.length * FRAMES_PER_POSE;
  /* END PATCH */

})();
