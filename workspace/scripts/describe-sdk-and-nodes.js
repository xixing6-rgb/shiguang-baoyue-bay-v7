return await (async function describeSdk(scene) {
  const dScope = await scene.context.describe("scripts.setScopeRole");
  const dCreate = await scene.context.describe("scripts.create");
  const dBind = await scene.context.describe("scripts.bind");
  const dLight = await scene.components.schema("lightData");
  const qCottage = await scene.nodes.query({ subtree: "n101" }, { fields: ["handle", "name", "parent", "componentTypes"], limit: 100 });
  const qFlowers = await scene.nodes.query({ subtree: "n153" }, { fields: ["handle", "name", "parent"], limit: 100 });
  const qPier = await scene.nodes.query({ subtree: "n143" }, { fields: ["handle", "name", "parent", "componentTypes"], limit: 50 });
  return {
    dScope, dCreate, dBind, dLight,
    cottageNodes: qCottage.items,
    flowerNodes: qFlowers.items,
    pierNodes: qPier.items
  };
})(scene);
