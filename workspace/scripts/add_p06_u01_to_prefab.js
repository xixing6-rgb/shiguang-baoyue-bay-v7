const P06_URI = "hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/y2v6iyx5ibejl7bd.glb";
const U01_URI = "hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/rav6btlz747bpaa9.glb";

const farmMatches = await scene.nodes.query({ name: { equals: "FarmGarden" } }, { fields: ["handle", "parent"], limit: 3 });
if (farmMatches.items.length !== 1) throw new Error("Expected exactly one FarmGarden");
const parentRoot = farmMatches.items[0].parent;

const placements = [
  { name: "P06_Armillary_West", uri: P06_URI, pos: { x: -52.5, y: 2.750, z: -21.5 }, yaw: 35, decorative: false },
  { name: "P06_Armillary_North", uri: P06_URI, pos: { x: -4.0, y: 3.100, z: 53.5 }, yaw: 180, decorative: false },
  { name: "U01_PaperPet_Courtyard", uri: U01_URI, pos: { x: 1.2, y: 1.150, z: 2.2 }, yaw: 170, decorative: true },
];

const added = [];
for (const item of placements) {
  const existing = await scene.nodes.query({ name: { equals: item.name } }, { fields: ["handle"], limit: 3 });
  if (existing.items.length > 0) {
    throw new Error("Duplicate placement already exists: " + item.name);
  }
  const inst = await scene.assets.instantiateModel({ resource: item.uri, parent: parentRoot, name: item.name });
  const half = item.yaw * Math.PI / 360;
  await scene.transforms.set({
    nodes: [inst.root],
    space: "local",
    scope: "subtree",
    value: {
      position: item.pos,
      rotation: { x: 0, y: Math.sin(half), z: 0, w: Math.cos(half) },
      scale: { x: 1, y: 1, z: 1 },
    },
  });
  if (item.decorative) {
    const cols = await scene.nodes.query({ subtree: inst.root, hasComponent: "physicsColliderData" }, { fields: ["handle"], limit: 25 });
    if (cols.items.length) {
      await scene.components.set({
        nodes: cols.items.map(n => n.handle),
        type: "physicsColliderData",
        values: { enableCollision: false, enableRigidBody: false },
      });
    }
  }
  added.push({ name: item.name, root: inst.root });
}

return { added, diagnostics: await scene.document.validate() };
