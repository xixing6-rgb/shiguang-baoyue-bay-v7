return await (async function setupScriptsAndPhysics(scene) {
  const scopeRes = await scene.scripts.setScopeRole({
    nodes: ["n101", "n153", "n207", "n215"],
    role: "resource"
  });

  const doorPhysicsRes = await scene.components.set({
    nodes: ["n109", "n110", "n111", "n112", "n113", "n114"],
    type: "physicsColliderData",
    values: { enableCollision: false }
  });

  const paths = [
    "courtyard-lights.lua",
    "cottage-door-interact.lua",
    "flowerbed-breed-interact.lua",
    "ambient-pivot-motion.lua"
  ];
  const createdScripts = {};
  for (const p of paths) {
    createdScripts[p] = await scene.scripts.create({ path: p });
  }

  return {
    scopeRes,
    doorPhysicsRes,
    createdScripts
  };
})(scene);
