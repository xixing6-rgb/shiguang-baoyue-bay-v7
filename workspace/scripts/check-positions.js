return await (async function checkPositions(scene) {
  const handles = ["n78", "n87", "n100", "n101", "n108", "n142", "n152", "n206", "n214", "n252"];
  const tr = await scene.transforms.get({ nodes: handles, space: "local" });
  const trW = await scene.transforms.get({ nodes: ["n101", "n108", "n87"], space: "world" });
  return { tr, trW };
})(scene);
