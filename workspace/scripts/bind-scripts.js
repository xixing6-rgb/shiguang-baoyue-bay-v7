return await (async function bindScripts(scene) {
  await scene.scripts.bind({
    nodes: ["n101"],
    script: "ca75e61e-97e0-49f2-be2e-446fd45e9390"
  });
  await scene.scripts.bind({
    nodes: ["n101"],
    script: "f1099544-6fa0-4303-af3e-9cc8f325ed91",
    params: {
      DoorNodePath: "DoorPivot",
      TriggerDistance: 3.4,
      OpenAngle: -85,
      LerpSpeed: 5.5
    }
  });
  await scene.scripts.bind({
    nodes: ["n153"],
    script: "c2bf26b4-0bf1-4901-9466-2aeb83d597e5",
    params: {
      InteractDistance: 4.5,
      AutoTriggerOnFirstVisit: true,
      CooldownSeconds: 0.8
    }
  });
  await scene.scripts.bind({
    nodes: ["n215"],
    script: "0c79838b-2318-4bcd-80d5-3e2aada3657a",
    params: {
      TargetNodePath: "BladesPivot",
      Mode: "spinZ",
      Speed: 22
    }
  });
  await scene.scripts.bind({
    nodes: ["n207"],
    script: "0c79838b-2318-4bcd-80d5-3e2aada3657a",
    params: {
      TargetNodePath: "FlagClothPivot",
      Mode: "swayY",
      Speed: 2.2,
      Amplitude: 14
    }
  });

  const bindings = await scene.scripts.bindings(["n101", "n153", "n207", "n215"], { limit: 100 });
  return { bindings: bindings.items };
})(scene);
