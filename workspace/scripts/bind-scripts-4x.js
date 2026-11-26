return await (async function bindScripts4x(scene) {
  const SCRIPTS = {
    courtyardLights: "ca75e61e-97e0-49f2-be2e-446fd45e9390",
    cottageDoor: "f1099544-6fa0-4303-af3e-9cc8f325ed91",
    flowerbedBreed: "c2bf26b4-0bf1-4901-9466-2aeb83d597e5",
    ambientPivot: "0c79838b-2318-4bcd-80d5-3e2aada3657a",
    narrativeHost: "4f32bd33-448d-44f3-8e41-85327fff30eb",
    residentUtilityAI: "c5670c57-c276-47ed-a8f6-b71d5e9e2352",
    blackboardDialogue: "dfacf592-c757-4758-95fa-bf000f4bd97c",
    smartObject: "132b6356-c42c-45d9-a2f3-34f02a940885",
    fastTravelFerry: "b0db7871-23a3-45f2-a6fb-6f52737fb26e",
    timeWeatherLighting: "e61d5806-bc55-4463-8873-191b97209e4e",
    ugcCollage: "33e13146-3731-4d44-b13f-101f8380a590"
  };

  // 查询当前场景中已存在的节点句柄与名称映射，兼容老镇既有句柄与 4x 新增命名节点
  const queried = await scene.nodes.query({}, { fields: ["handle", "name"], limit: 1500 });
  const handleSet = new Set();
  const nameToHandle = new Map();
  for (const item of (queried && queried.items) || []) {
    if (item.handle) handleSet.add(item.handle);
    if (item.name && !nameToHandle.has(item.name)) {
      nameToHandle.set(item.name, item.handle);
    }
  }

  const boundHandles = new Set();
  const pendingNodes = [];
  const applied = [];

  async function tryBind(targetRef, scriptId, params, label) {
    let handle = null;
    if (handleSet.has(targetRef)) {
      handle = targetRef;
    } else if (nameToHandle.has(targetRef)) {
      handle = nameToHandle.get(targetRef);
    }

    if (!handle) {
      pendingNodes.push({ targetRef, label, scriptId });
      return false;
    }

    await scene.scripts.bind({
      nodes: [handle],
      script: scriptId,
      params: params || {}
    });
    boundHandles.add(handle);
    applied.push({ handle, label, scriptId });
    return true;
  }

  // 1. 保留原 4 项核心老镇脚本绑定（绝对兼容现有 prefab.json）
  await tryBind("n101", SCRIPTS.courtyardLights, {
    HearthIntensity: 2.6,
    PorchIntensity: 2.2,
    TerraceIntensity: 1.9
  }, "F04-Lights");

  await tryBind("n101", SCRIPTS.cottageDoor, {
    DoorNodePath: "DoorPivot",
    TriggerDistance: 3.4,
    OpenAngle: -85,
    LerpSpeed: 5.5
  }, "F04-Door");

  await tryBind("n153", SCRIPTS.flowerbedBreed, {
    InteractDistance: 4.5,
    AutoTriggerOnFirstVisit: true,
    CooldownSeconds: 0.8
  }, "F06-Flowerbed");

  await tryBind("n215", SCRIPTS.ambientPivot, {
    TargetNodePath: "BladesPivot",
    Mode: "spinZ",
    Speed: 22
  }, "F15-WindmillSpin");

  await tryBind("n207", SCRIPTS.ambientPivot, {
    TargetNodePath: "FlagClothPivot",
    Mode: "swayY",
    Speed: 2.2,
    Amplitude: 14
  }, "F07-FlagSway");

  // 2. 绑定全局叙事宿主、黑板对话引擎、三时段光影与全镇 AI 调度器到根节点 n1
  await tryBind("n1", SCRIPTS.narrativeHost, {
    SaveKey: "shiguang_town_save_v4",
    InitialChapter: "prologue",
    AutoSaveInterval: 45,
    EnableDebugUnlockAll: false
  }, "TownRoot-NarrativeHost");

  await tryBind("n1", SCRIPTS.blackboardDialogue, {
    DefaultVoiceMode: "dual",
    RuleCooldownSeconds: 180,
    MaxTraceryDepth: 5,
    SyllableInterval: 0.075
  }, "TownRoot-BlackboardDialogue");

  await tryBind("n1", SCRIPTS.timeWeatherLighting, {
    TimeMode: "auto",
    LighthouseBeamPath: "F22_WestLighthouse/BeamPivot",
    NightMarketPath: "F25_NightMarketKiln/StringLights",
    FirefliesPath: "F32_FireflyCreek/FireflyParticles",
    LighthouseSweepSpeed: 30
  }, "TownRoot-TimeWeatherLighting");

  await tryBind("n1", SCRIPTS.residentUtilityAI, {
    ResidentId: "ALL",
    DecisionInterval: 4.5,
    DirectorBiasSeconds: 8.0,
    DirectorScanRadius: 28.0,
    MaxPerScreen: 6
  }, "TownRoot-ResidentDirectorAI");

  // 3. 绑定 9 名动物居民独立节点脚本（若场景中存在 C01..C09 独立角色根节点）
  const residentNodes = [
    ["C01_GlassesBear", "C01"],
    ["C02_LopRabbit", "C02"],
    ["C03_DeadpanCat", "C03"],
    ["C04_CorgiBaker", "C04"],
    ["C05_FloatingOwl", "C05"],
    ["C06_StrawhatFox", "C06"],
    ["C07_PostmanOtter", "C07"],
    ["C08_CarpenterRaccoon", "C08"],
    ["C09_ArtistSheep", "C09"]
  ];
  for (const [nodeName, cid] of residentNodes) {
    await tryBind(nodeName, SCRIPTS.residentUtilityAI, {
      ResidentId: cid,
      DecisionInterval: 4.5,
      DirectorBiasSeconds: 8.0,
      DirectorScanRadius: 28.0,
      MaxPerScreen: 6
    }, `Resident-${cid}`);
  }

  // 4. 绑定 F01–F42 全部 42 项设施的统一 Smart Object 动机广播与叙事交互
  const facilities = [
    ["n398", "F01", "Zone0", "prologue", "curiosity", 0.65, 3, "wave", "M09", ""],
    ["n143", "F02", "Zone0", "prologue", "relax", 0.85, 2, "sit", "M23", ""],
    ["n618", "F03", "Zone0", "prologue", "curiosity", 0.90, 3, "greet", "M01", ""],
    ["n101", "F04", "Zone0", "prologue", "warmth", 0.90, 4, "door_open", "", ""],
    ["n88", "F05", "Zone0", "prologue", "social", 0.88, 4, "sit", "", ""],
    ["n153", "F06", "Zone0", "prologue", "nature", 0.95, 3, "water_bend", "M18", "blue_rose_bred"],
    ["n207", "F07", "Zone0", "prologue", "curiosity", 0.75, 2, "clap", "", "pixel_flag_customized"],
    ["n79", "F08", "Zone0", "prologue", "curiosity", 0.85, 3, "photo", "", "lingo_injected"],
    ["n253", "F09", "Zone0", "prologue", "social", 0.90, 5, "cheer", "", ""],
    ["n653", "F10", "Zone0", "prologue", "hunger", 0.85, 2, "hop_bounce", "", ""],
    ["n667", "F11", "Zone0", "prologue", "social", 0.85, 4, "sit", "", ""],
    ["n388", "F12", "Zone0", "prologue", "hunger", 0.92, 4, "greet", "", ""],
    ["n259", "F13", "Zone0", "prologue", "rest", 0.75, 3, "wave", "", ""],
    ["n408", "F14", "Zone0", "prologue", "music", 0.88, 3, "dance", "M14", ""],
    ["n215", "F15", "Zone0", "prologue", "curiosity", 0.70, 2, "pivot_spin", "", ""],
    ["n476", "F16", "Zone0", "prologue", "curiosity", 0.90, 3, "photo", "", ""],
    ["n677", "F17", "Zone0", "prologue", "nature", 0.85, 3, "cheer", "", ""],
    ["n806", "F18", "Zone0", "prologue", "play", 0.80, 3, "paper_pet_squash", "M21", ""],
    ["F19_PostOffice", "F19", "ZoneW", "ch1", "curiosity", 0.90, 4, "greet", "M02", ""],
    ["F20_MailboxGallery", "F20", "ZoneW", "ch1", "curiosity", 0.82, 3, "clap", "M03", ""],
    ["F21_WindchimeCorridor", "F21", "ZoneW", "ch1", "relax", 0.80, 3, "wave", "M04", ""],
    ["F22_WestLighthouse", "F22", "ZoneW", "ch1", "warmth", 0.95, 4, "pivot_spin", "M05", "lighthouse_relight"],
    ["F23_CliffCottages", "F23", "ZoneW", "ch1", "rest", 0.80, 2, "wave", "M06", ""],
    ["F24_DriftwoodCampfire", "F24", "ZoneW", "ch1", "warmth", 0.95, 4, "sit", "M10", ""],
    ["F25_NightMarketKiln", "F25", "ZoneE", "ch2", "hunger", 0.98, 6, "dance", "M15", ""],
    ["F26_OldBoatyard", "F26", "ZoneE", "ch2", "craft", 0.92, 4, "nod_tilt", "M19", ""],
    ["F27_DaylightLightship", "F27", "ZoneE", "ch2", "warmth", 0.95, 4, "cheer", "M11", "lightship_relight"],
    ["F28_TidepoolWetland", "F28", "ZoneE", "ch2", "nature", 0.90, 3, "water_bend", "M12", ""],
    ["F29_CamelliaKiteTerrace", "F29", "ZoneE", "ch2", "nature", 0.86, 3, "wave", "M20", ""],
    ["F30_StudioCottages", "F30", "ZoneE", "ch2", "craft", 0.85, 2, "clap", "", ""],
    ["F31_MemoryGreenhouse", "F31", "ZoneN", "ch3", "curiosity", 0.96, 5, "door_open", "M16", "chronicle_restored"],
    ["F32_FireflyCreek", "F32", "ZoneN", "ch3", "relax", 0.88, 3, "walk", "", ""],
    ["F33_ForestWatermill", "F33", "ZoneN", "ch3", "music", 0.96, 3, "pivot_spin", "M17", "vinyl_played"],
    ["F34_CamphorBellTower", "F34", "ZoneN", "ch3", "warmth", 0.95, 5, "cheer", "M22", "summit_bell_rung"],
    ["F35_TimberSlides", "F35", "ZoneN", "ch3", "play", 0.94, 2, "sit", "", ""],
    ["F36_TreeHollowNook", "F36", "ZoneN", "ch3", "curiosity", 0.92, 2, "photo", "M07", ""],
    ["F37_WestSeaBridge", "F37", "ZoneS", "ch4", "relax", 0.80, 3, "walk", "M25", ""],
    ["F38_EastTidalStones", "F38", "ZoneS", "ch4", "nature", 0.80, 3, "walk", "", ""],
    ["F39_EchoAmphitheater", "F39", "ZoneS", "ch4", "music", 0.98, 9, "dance", "M26", ""],
    ["F40_SouthFerryPier", "F40", "ZoneS", "ch2", "relax", 0.70, 2, "wave", "", ""],
    ["F41_MiniBookBooth", "F41", "ZoneS", "ch4", "curiosity", 0.90, 2, "greet", "M13", ""],
    ["F42_PostalBikeStop", "F42", "Zone0", "ch1", "curiosity", 0.60, 2, "hop_bounce", "M24", ""]
  ];

  for (const [nodeRef, fid, zone, unlockCh, motive, weight, cap, act, memId, evKey] of facilities) {
    await tryBind(nodeRef, SCRIPTS.smartObject, {
      FacilityId: fid,
      ZoneId: zone,
      UnlockChapter: unlockCh,
      MotivePrimary: motive,
      MotiveWeight: weight,
      SlotCapacity: cap,
      AllowedAction: act,
      CollectibleId: memId,
      StoryEventKey: evKey,
      InteractDistance: 4.0,
      AutoTriggerOnFirstVisit: fid === "F04" || fid === "F19" || fid === "F22" || fid === "F27" || fid === "F31" || fid === "F39"
    }, `SmartObject-${fid}`);
  }

  // 5. 绑定第二座可进入室内（F31 记忆温室门扇）与水车磨坊旋转枢轴（F33）
  await tryBind("F31_MemoryGreenhouse", SCRIPTS.cottageDoor, {
    DoorNodePath: "GreenhouseDoorPivot",
    TriggerDistance: 3.6,
    OpenAngle: -85,
    LerpSpeed: 5.5
  }, "F31-Door");

  await tryBind("F33_ForestWatermill", SCRIPTS.ambientPivot, {
    TargetNodePath: "WaterwheelPivot",
    Mode: "spinZ",
    Speed: 16
  }, "F33-Waterwheel");

  // 6. 绑定快速通行节点（F42单车驿站 / F01-F40-F26渡船 / F35W-F35E下行滑道）
  await tryBind("F42_PostalBikeStop", SCRIPTS.fastTravelFerry, {
    TravelMode: "BikeHub",
    StationId: "F42_Zone0",
    TargetStationId: "F42_ZoneW",
    InteractDistance: 3.5,
    TransitionSeconds: 1.5
  }, "Travel-Bike-Zone0");

  await tryBind("F42_Bike_ZoneW", SCRIPTS.fastTravelFerry, {
    TravelMode: "BikeHub",
    StationId: "F42_ZoneW",
    TargetStationId: "F42_ZoneE",
    InteractDistance: 3.5,
    TransitionSeconds: 1.5
  }, "Travel-Bike-ZoneW");

  await tryBind("F42_Bike_ZoneE", SCRIPTS.fastTravelFerry, {
    TravelMode: "BikeHub",
    StationId: "F42_ZoneE",
    TargetStationId: "F42_ZoneN",
    InteractDistance: 3.5,
    TransitionSeconds: 1.5
  }, "Travel-Bike-ZoneE");

  await tryBind("F42_Bike_ZoneN", SCRIPTS.fastTravelFerry, {
    TravelMode: "BikeHub",
    StationId: "F42_ZoneN",
    TargetStationId: "F42_Zone0",
    InteractDistance: 3.5,
    TransitionSeconds: 1.5
  }, "Travel-Bike-ZoneN");

  await tryBind("n398", SCRIPTS.fastTravelFerry, {
    TravelMode: "FerryRoute",
    StationId: "F01",
    TargetStationId: "F40",
    InteractDistance: 3.8,
    TransitionSeconds: 2.0
  }, "Ferry-F01");

  await tryBind("F40_SouthFerryPier", SCRIPTS.fastTravelFerry, {
    TravelMode: "FerryRoute",
    StationId: "F40",
    TargetStationId: "F26",
    InteractDistance: 3.8,
    TransitionSeconds: 2.0
  }, "Ferry-F40");

  await tryBind("F26_OldBoatyard", SCRIPTS.fastTravelFerry, {
    TravelMode: "FerryRoute",
    StationId: "F26",
    TargetStationId: "F01",
    InteractDistance: 3.8,
    TransitionSeconds: 2.0
  }, "Ferry-F26");

  await tryBind("F35_TimberSlides", SCRIPTS.fastTravelFerry, {
    TravelMode: "TimberSlide",
    StationId: "F35W",
    TargetStationId: "F35W",
    InteractDistance: 2.8,
    TransitionSeconds: 5.0
  }, "Slide-F35W");

  await tryBind("F35E_TimberSlide", SCRIPTS.fastTravelFerry, {
    TravelMode: "TimberSlide",
    StationId: "F35E",
    TargetStationId: "F35E",
    InteractDistance: 2.8,
    TransitionSeconds: 5.0
  }, "Slide-F35E");

  // 7. 绑定轻拼贴 UGC 模块（12x12 像素旗 + 流行语涂鸦黑板 + 2D 纸片宠物）
  await tryBind("n207", SCRIPTS.ugcCollage, {
    UgcMode: "Flag",
    TargetNodePath: "FlagClothPivot"
  }, "UGC-Flag-F07");

  await tryBind("n79", SCRIPTS.ugcCollage, {
    UgcMode: "Chalkboard",
    TargetNodePath: "FrontBoardLeaf"
  }, "UGC-Chalkboard-F08");

  await tryBind("U01_PaperPet", SCRIPTS.ugcCollage, {
    UgcMode: "PaperPet",
    TargetNodePath: "",
    PetFollowDistance: 1.65,
    SquashAmplitude: 0.18,
    SquashFrequency: 6.5
  }, "UGC-PaperPet-U01");

  const finalHandles = Array.from(boundHandles);
  const bindings = finalHandles.length > 0
    ? await scene.scripts.bindings(finalHandles, { limit: 250 })
    : { items: [] };

  return {
    boundCount: applied.length,
    uniqueNodesBound: finalHandles.length,
    pendingExpansionNodes: pendingNodes.length,
    applied,
    pendingNodes,
    bindings: bindings.items
  };
})(scene);
