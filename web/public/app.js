(() => {
  "use strict";

  const UNIT_NAMES = {
    ngol: "Gold Mine (معدن طلا)",
    ntav: "Tavern (میخانه قهرمانان بی‌طرف)",
    ngme: "Goblin Merchant (فروشگاه گابلین)",
    ngad: "Goblin Laboratory (آزمایشگاه گابلین — شردر/زپلین/سپپر)",
    nmer: "Mercenary Camp (اردوگاه مزدوران لوردرون)",
    nfoh: "Fountain of Health (چشمه احیای سلامتی)",
    ngno: "Gnoll (Lvl 1)",
    ngna: "Gnoll Poacher (Lvl 1)",
    ngnw: "Gnoll Warden (Lvl 3)",
    nogr: "Ogre Warrior (Lvl 3)",
    nogm: "Ogre Mauler (Lvl 5)",
    nomg: "Ogre Magi (Lvl 5)",
    nogl: "Ogre Lord (Lvl 7 Boss)",
    nftr: "Forest Troll (Lvl 2)",
    nfsp: "Forest Troll Shadow Priest (Lvl 2)",
    nftb: "Forest Troll Berserker (Lvl 4)",
    nftk: "Forest Troll High Priest (Lvl 6)",
    ngrk: "Mud Golem (Lvl 2)",
    ngst: "Rock Golem (Lvl 6)",
    nggr: "Granite Golem (Lvl 9 Boss)",
    nrdk: "Red Dragon Whelp (Lvl 3)",
    nrdr: "Red Drake (Lvl 6)",
    nrwm: "Red Dragon (Lvl 10 Ancient Boss)",
  };

  const TEX_RGB = [
    [88, 80, 102],    // 0 Zdrt (Obsidian-Bronze Ancient Earth)
    [146, 136, 174],  // 1 Ztil (Carved Astral Temple Marble)
    [98, 138, 146],   // 2 Zsan (Bioluminescent Teal Shore)
    [62, 56, 86],     // 3 Zbkl (Obsidian Sanctum Stonework)
    [46, 118, 102],   // 4 Zgrs (Twilight Emerald Sanctuary)
    [32, 88, 86],     // 5 Zvin (Deep Indigo-Emerald Moss)
  ];

  const state = {
    data: null,
    terrainCanvas: null,
    pathingCanvas: null,
    treesCanvas: null,
    zoom: 1.0,
    panX: 0,
    panY: 0,
    dragging: false,
    dragMoved: false,
    lastMouseX: 0,
    lastMouseY: 0,
    teamMode: "ffa",
    selected: null,
    quickFilter: "boss",
    layers: {
      trees: true,
      players: true,
      neutral: true,
      camps: true,
      aggro: false,
      pathing: false,
      symmetry: false,
    },
  };

  const canvas = document.getElementById("mapCanvas");
  const ctx = canvas.getContext("2d");
  const cursorReadout = document.getElementById("cursorReadout");
  const zoomLabel = document.getElementById("zoomLabel");
  const inspectorContent = document.getElementById("inspectorContent");
  const quickList = document.getElementById("quickList");

  function worldToNorm(wx, wy, dims) {
    const span = dims.maxWorld - dims.minWorld;
    return [
      (wx - dims.minWorld) / span,
      (dims.maxWorld - wy) / span,
    ];
  }

  function normToWorld(nx, ny, dims) {
    const span = dims.maxWorld - dims.minWorld;
    return [
      dims.minWorld + nx * span,
      dims.maxWorld - ny * span,
    ];
  }

  function buildOffscreenLayers(data) {
    const W = 768;
    const H = 768;
    const tilesW = data.dimensions.tilesW; // 192
    const tilesH = data.dimensions.tilesH; // 192

    // 1) Crisp Terrain & Water Relief Layer
    const tCan = document.createElement("canvas");
    tCan.width = W;
    tCan.height = H;
    const tCtx = tCan.getContext("2d");
    const tImg = tCtx.createImageData(W, H);
    const td = tImg.data;

    for (let ty = 0; ty < tilesH; ty++) {
      const wyRow = tilesH - 1 - ty;
      const hRow = data.heightGrid[wyRow];
      const texRow = data.texGrid[wyRow];
      const wpmRow = data.wpmGrid[wyRow];

      for (let tx = 0; tx < tilesW; tx++) {
        const gh = hRow[tx];
        const tex = texRow[tx];
        const wpm = wpmRow[tx];

        let r, g, b;
        if (tx < 6 || tx >= tilesW - 6 || wyRow < 6 || wyRow >= tilesH - 6) {
          r = 22; g = 32; b = 22;
        } else if (gh < -0.55) {
          // Deep Sapphire Moat Lagoon
          r = 22; g = 88; b = 176;
        } else if (gh < 0.0) {
          // Shallow Walkable Cyan River Ford
          r = 54; g = 172; b = 228;
        } else {
          const base = TEX_RGB[tex] || TEX_RGB[4];
          const shade = Math.max(-20, Math.min(26, Math.round((gh - 0.25) * 44)));
          r = Math.max(0, Math.min(255, base[0] + shade));
          g = Math.max(0, Math.min(255, base[1] + shade));
          b = Math.max(0, Math.min(255, base[2] + shade));
          if ((wpm & 0x08) && tex === 3) {
            r = Math.min(255, r + 8);
            g = Math.min(255, g + 8);
            b = Math.min(255, b + 12);
          }
        }

        for (let py = 0; py < 4; py++) {
          for (let px = 0; px < 4; px++) {
            const idx = ((ty * 4 + py) * W + (tx * 4 + px)) * 4;
            td[idx] = r;
            td[idx + 1] = g;
            td[idx + 2] = b;
            td[idx + 3] = 255;
          }
        }
      }
    }
    tCtx.putImageData(tImg, 0, 0);
    state.terrainCanvas = tCan;

    // 2) Pathing / Buildability WPM Heatmap Layer
    const pCan = document.createElement("canvas");
    pCan.width = W;
    pCan.height = H;
    const pCtx = pCan.getContext("2d");
    const pImg = pCtx.createImageData(W, H);
    const pd = pImg.data;

    for (let ty = 0; ty < tilesH; ty++) {
      const wyRow = tilesH - 1 - ty;
      const wpmRow = data.wpmGrid[wyRow];
      for (let tx = 0; tx < tilesW; tx++) {
        const w = wpmRow[tx];
        let r = 0, g = 0, b = 0, a = 140;
        if (w === 0x40) {
          // Buildable & Walkable Dry Land
          r = 34; g = 197; b = 94; a = 82;
        } else if (w === 0x08) {
          // Shallow Walkable River Ford
          r = 56; g = 189; b = 248; a = 155;
        } else if (w === 0x48) {
          // Walkable but Unbuildable (Shore / Rock)
          r = 250; g = 204; b = 21; a = 125;
        } else {
          // Unwalkable (Deep Water / Map Boundary)
          r = 239; g = 68; b = 68; a = 165;
        }
        for (let py = 0; py < 4; py++) {
          for (let px = 0; px < 4; px++) {
            const idx = ((ty * 4 + py) * W + (tx * 4 + px)) * 4;
            pd[idx] = r;
            pd[idx + 1] = g;
            pd[idx + 2] = b;
            pd[idx + 3] = a;
          }
        }
      }
    }
    pCtx.putImageData(pImg, 0, 0);
    state.pathingCanvas = pCan;

    // 3) Pre-rendered 5,920 Harvestable Trees Layer
    const fCan = document.createElement("canvas");
    fCan.width = W;
    fCan.height = H;
    const fCtx = fCan.getContext("2d");
    for (const [tx, ty, sc] of data.trees) {
      const [nx, ny] = worldToNorm(tx, ty, data.dimensions);
      const cx = nx * W;
      const cy = ny * H;
      const rad = 2.6 * (sc || 1.0);
      fCtx.fillStyle = "#183f18";
      fCtx.beginPath();
      fCtx.arc(cx + 0.6, cy + 0.7, rad, 0, Math.PI * 2);
      fCtx.fill();
      fCtx.fillStyle = "#2d6b28";
      fCtx.beginPath();
      fCtx.arc(cx - 0.3, cy - 0.3, rad * 0.72, 0, Math.PI * 2);
      fCtx.fill();
    }
    state.treesCanvas = fCan;
  }

  function clampPan() {
    const maxPan = ((canvas.width * state.zoom) - canvas.width) / 2 + 60;
    if (state.zoom <= 1.01) {
      state.panX = 0;
      state.panY = 0;
    } else {
      state.panX = Math.max(-maxPan, Math.min(maxPan, state.panX));
      state.panY = Math.max(-maxPan, Math.min(maxPan, state.panY));
    }
  }

  function screenToNorm(sx, sy) {
    const W = canvas.width;
    const H = canvas.height;
    const nx = ((sx - W / 2 - state.panX) / state.zoom + W / 2) / W;
    const ny = ((sy - H / 2 - state.panY) / state.zoom + H / 2) / H;
    return [nx, ny];
  }

  function drawTeamOverlay(W, H, dims) {
    if (state.teamMode === "ffa") return;
    const byId = {};
    for (const p of state.data.players) byId[p.id] = p;

    let groups = [];
    if (state.teamMode === "4v4_ns") {
      groups = [
        { color: "#60a5fa", label: "Team 1 (North Alliance)", ids: [7, 0, 1, 2] },
        { color: "#f87171", label: "Team 2 (South Horde)", ids: [6, 5, 4, 3] },
      ];
    } else if (state.teamMode === "4v4_we") {
      groups = [
        { color: "#34d399", label: "Team 1 (West Crown)", ids: [0, 7, 6, 5] },
        { color: "#fbbf24", label: "Team 2 (East Crown)", ids: [1, 2, 3, 4] },
      ];
    } else if (state.teamMode === "2v2v2v2") {
      groups = [
        { color: "#60a5fa", ids: [7, 0] },
        { color: "#34d399", ids: [1, 2] },
        { color: "#fbbf24", ids: [3, 4] },
        { color: "#f472b6", ids: [5, 6] },
      ];
    }

    ctx.save();
    ctx.lineWidth = 3 / state.zoom;
    ctx.setLineDash([8 / state.zoom, 6 / state.zoom]);
    for (const grp of groups) {
      ctx.strokeStyle = grp.color;
      ctx.beginPath();
      grp.ids.forEach((pid, i) => {
        const p = byId[pid];
        const [nx, ny] = worldToNorm(p.x, p.y, dims);
        if (i === 0) ctx.moveTo(nx * W, ny * H);
        else ctx.lineTo(nx * W, ny * H);
      });
      ctx.stroke();
    }
    ctx.restore();
  }

  function render() {
    if (!state.data) return;
    const W = canvas.width;
    const H = canvas.height;
    const dims = state.data.dimensions;
    const worldSpan = dims.maxWorld - dims.minWorld;
    const pxPerWorld = W / worldSpan;

    ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate(W / 2 + state.panX, H / 2 + state.panY);
    ctx.scale(state.zoom, state.zoom);
    ctx.translate(-W / 2, -H / 2);

    ctx.imageSmoothingEnabled = state.zoom < 2.2;
    ctx.drawImage(state.terrainCanvas, 0, 0, W, H);

    if (state.layers.pathing) {
      ctx.drawImage(state.pathingCanvas, 0, 0, W, H);
    }

    if (state.layers.trees) {
      ctx.drawImage(state.treesCanvas, 0, 0, W, H);
    }

    // Playable camera border
    const [bMinX, bMinY] = worldToNorm(-11520, 11520, dims);
    const [bMaxX, bMaxY] = worldToNorm(11520, -11520, dims);
    ctx.strokeStyle = "rgba(229, 190, 83, 0.35)";
    ctx.lineWidth = 1.5 / state.zoom;
    ctx.strokeRect(bMinX * W, bMinY * H, (bMaxX - bMinX) * W, (bMaxY - bMinY) * H);

    // D4 8-way Symmetry Mirror Axes
    if (state.layers.symmetry) {
      ctx.save();
      ctx.strokeStyle = "rgba(255, 224, 130, 0.55)";
      ctx.lineWidth = 1.5 / state.zoom;
      ctx.setLineDash([7 / state.zoom, 5 / state.zoom]);
      ctx.beginPath();
      ctx.moveTo(W / 2, 0); ctx.lineTo(W / 2, H);
      ctx.moveTo(0, H / 2); ctx.lineTo(W, H / 2);
      ctx.moveTo(0, 0); ctx.lineTo(W, H);
      ctx.moveTo(W, 0); ctx.lineTo(0, H);
      ctx.stroke();
      ctx.restore();
    }

    drawTeamOverlay(W, H, dims);

    const invScale = 1 / Math.pow(state.zoom, 0.45);

    // Neutral Passive Buildings & Gold Mines
    for (const nb of state.data.neutralBuildings) {
      const isMine = nb.uid === "ngol";
      if (isMine && !state.layers.players) continue;
      if (!isMine && !state.layers.neutral) continue;

      const [nx, ny] = worldToNorm(nb.x, nb.y, dims);
      const cx = nx * W;
      const cy = ny * H;

      if (isMine) {
        const r = 6.5 * invScale;
        ctx.fillStyle = nb.gold > 12500 ? "#fde047" : "#facc15";
        ctx.strokeStyle = "#111";
        ctx.lineWidth = 1.8 * invScale;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      } else if (nb.uid === "ntav") {
        const r = 9.5 * invScale;
        ctx.fillStyle = "#c084fc";
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2.0 * invScale;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      } else {
        const r = 6.8 * invScale;
        ctx.fillStyle = nb.uid === "nfoh" ? "#34d399" : "#38bdf8";
        ctx.strokeStyle = "#081018";
        ctx.lineWidth = 1.8 * invScale;
        ctx.beginPath();
        ctx.rect(cx - r, cy - r, r * 2, r * 2);
        ctx.fill();
        ctx.stroke();
      }
    }

    // Creep Camps & 200u Camp Aggro Circles
    if (state.layers.camps || state.layers.aggro) {
      for (const camp of state.data.camps) {
        const [nx, ny] = worldToNorm(camp.x, camp.y, dims);
        const cx = nx * W;
        const cy = ny * H;

        const color =
          camp.tier === "green" ? "#4ade80" :
          camp.tier === "orange" ? "#fb923c" : "#ef4444";

        if (state.layers.aggro) {
          ctx.fillStyle = camp.tier === "red"
            ? "rgba(239, 68, 68, 0.18)"
            : "rgba(251, 146, 60, 0.15)";
          ctx.strokeStyle = color;
          ctx.lineWidth = 1.1 / state.zoom;
          ctx.beginPath();
          // 200u Camp Acquisition radius + ~150u formation spread = ~350u effective zone
          ctx.arc(cx, cy, 350 * pxPerWorld, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
        }

        if (state.layers.camps) {
          const r = (camp.tier === "red" ? 6.8 : 5.6) * invScale;
          ctx.fillStyle = color;
          ctx.strokeStyle = "#090d14";
          ctx.lineWidth = 1.8 * invScale;
          ctx.beginPath();
          ctx.arc(cx, cy, r, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
        }
      }
    }

    // 8 Player Start Locations
    if (state.layers.players) {
      for (const p of state.data.players) {
        const [nx, ny] = worldToNorm(p.x, p.y, dims);
        const cx = nx * W;
        const cy = ny * H;
        const r = 10.5 * invScale;

        ctx.fillStyle = `rgb(${p.rgb[0]}, ${p.rgb[1]}, ${p.rgb[2]})`;
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2.2 * invScale;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = p.id === 4 ? "#111" : "#fff";
        ctx.font = `800 ${Math.round(10.5 * invScale)}px system-ui, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(`P${p.id + 1}`, cx, cy + 0.5 * invScale);
      }
    }

    // Highlight Selected Pin
    if (state.selected) {
      const [nx, ny] = worldToNorm(state.selected.x, state.selected.y, dims);
      const cx = nx * W;
      const cy = ny * H;
      ctx.strokeStyle = "#ffe082";
      ctx.lineWidth = 2.6 * invScale;
      ctx.beginPath();
      ctx.arc(cx, cy, 16 * invScale, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.restore();
    zoomLabel.textContent = `${state.zoom.toFixed(1)}×`;
  }

  function renderInspector(sel) {
    if (!sel) return;
    if (sel.kind === "player") {
      const p = sel.item;
      inspectorContent.innerHTML = `
        <div class="insp-header">
          <span class="insp-title">${p.name} (${p.colorName})</span>
          <span class="insp-badge badge-gold">Start Location</span>
        </div>
        <dl class="insp-kv">
          <dt>مختصات World Editor:</dt>
          <dd>(${p.x}, ${p.y})</dd>
          <dt>معدن طلای اصلی:</dt>
          <dd>(${p.mineX}, ${p.mineY}) • 12,500 Gold</dd>
          <dt>فاصله دقیق تالار تا معدن:</dt>
          <dd>640.0 units (استاندارد ۵ کارگر)</dd>
          <dt>پشتیبانی هر ۴ نژاد:</dt>
          <dd>Human / Orc / Undead / Night Elf</dd>
        </dl>
        <div class="insp-sub">ویژگی‌های دفاعی مقر:</div>
        <div class="pill-wrap">
          <span class="unit-pill">دیواره درخت U-شکل بدون شکاف</span>
          <span class="unit-pill">۱۰۰٪ زمین صاف قابل ساخت (0x40)</span>
        </div>
      `;
    } else if (sel.kind === "neutral") {
      const nb = sel.item;
      const isMine = nb.uid === "ngol";
      inspectorContent.innerHTML = `
        <div class="insp-header">
          <span class="insp-title">${UNIT_NAMES[nb.uid] || nb.uid}</span>
          <span class="insp-badge ${isMine ? "badge-gold" : "badge-shop"}">${nb.uid}</span>
        </div>
        <dl class="insp-kv">
          <dt>نقش تاکتیکی:</dt>
          <dd>${nb.role}</dd>
          <dt>مختصات World Editor:</dt>
          <dd>(${nb.x}, ${nb.y})</dd>
          ${isMine ? `<dt>ذخیره طلا:</dt><dd>${nb.gold.toLocaleString()} Gold</dd>` : ""}
        </dl>
        <div class="insp-sub">موقعیت در شبکه راه‌ها:</div>
        <div class="pill-wrap">
          <span class="unit-pill">${nb.uid === "ntav" ? "مرکز امن نقشه (بدون کریپ مزاحم)" : "عقب‌نشسته از بزرگراه اصلی (بدون بلاک ارتش)"}</span>
        </div>
      `;
    } else if (sel.kind === "camp") {
      const c = sel.item;
      const bcls = c.tier === "green" ? "badge-green" : c.tier === "orange" ? "badge-orange" : "badge-red";
      const unitsHtml = c.units
        .map((u) => `<span class="unit-pill"><code>${u}</code> ${UNIT_NAMES[u] || u}</span>`)
        .join("");
      const dropsHtml = c.drops
        .map((d) => `<span class="drop-pill">🎁 ${d}</span>`)
        .join("");
      inspectorContent.innerHTML = `
        <div class="insp-header">
          <span class="insp-title">${c.name}</span>
          <span class="insp-badge ${bcls}">${c.tier.toUpperCase()} CAMP</span>
        </div>
        <dl class="insp-kv">
          <dt>مختصات کمپ:</dt>
          <dd>(${c.x}, ${c.y})</dd>
          <dt>شعاع درگیری (Camp Mode):</dt>
          <dd>200.0 units (No Highway Pull)</dd>
          <dt>تعداد واحدها:</dt>
          <dd>${c.units.length} Neutral Hostile Units</dd>
        </dl>
        <div class="insp-sub">ترکیب واحدهای کمپ:</div>
        <div class="pill-wrap">${unitsHtml}</div>
        <div class="insp-sub">جدول دراپ آیتم (بدون نشت حافظه JASS):</div>
        <div class="pill-wrap">${dropsHtml}</div>
      `;
    }
  }

  function populateQuickList() {
    if (!state.data) return;
    quickList.innerHTML = "";
    let items = [];

    if (state.quickFilter === "boss") {
      items = state.data.camps
        .filter((c) => c.tier === "red")
        .map((c) => ({
          title: c.name,
          sub: `(${c.x}, ${c.y})`,
          sel: { kind: "camp", x: c.x, y: c.y, item: c },
        }));
    } else if (state.quickFilter === "shops") {
      items = state.data.neutralBuildings
        .filter((n) => n.uid !== "ngol")
        .map((n) => ({
          title: n.role,
          sub: `${n.uid} • (${n.x}, ${n.y})`,
          sel: { kind: "neutral", x: n.x, y: n.y, item: n },
        }));
    } else {
      items = state.data.players.map((p) => ({
        title: `${p.name} (${p.colorName})`,
        sub: `(${p.x}, ${p.y})`,
        sel: { kind: "player", x: p.x, y: p.y, item: p },
      }));
    }

    for (const row of items) {
      const div = document.createElement("div");
      div.className = "quick-item";
      div.innerHTML = `<span>${row.title}</span><code dir="ltr">${row.sub}</code>`;
      div.addEventListener("click", () => {
        state.selected = row.sel;
        renderInspector(row.sel);
        render();
      });
      quickList.appendChild(div);
    }
  }

  function handleCanvasClick(ev) {
    if (!state.data || state.dragMoved) return;
    const rect = canvas.getBoundingClientRect();
    const sx = ((ev.clientX - rect.left) / rect.width) * canvas.width;
    const sy = ((ev.clientY - rect.top) / rect.height) * canvas.height;
    const [nx, ny] = screenToNorm(sx, sy);
    const [wx, wy] = normToWorld(nx, ny, state.data.dimensions);

    let best = null;
    let bestDist = 700 / Math.sqrt(state.zoom);

    for (const p of state.data.players) {
      const d = Math.hypot(p.x - wx, p.y - wy);
      if (d < bestDist) {
        bestDist = d;
        best = { kind: "player", x: p.x, y: p.y, item: p };
      }
    }
    for (const nb of state.data.neutralBuildings) {
      const d = Math.hypot(nb.x - wx, nb.y - wy);
      if (d < bestDist) {
        bestDist = d;
        best = { kind: "neutral", x: nb.x, y: nb.y, item: nb };
      }
    }
    for (const c of state.data.camps) {
      const d = Math.hypot(c.x - wx, c.y - wy);
      if (d < bestDist) {
        bestDist = d;
        best = { kind: "camp", x: c.x, y: c.y, item: c };
      }
    }

    if (best) {
      state.selected = best;
      renderInspector(best);
      render();
    }
  }

  function bindEvents() {
    const bindChk = (id, key) => {
      document.getElementById(id).addEventListener("change", (e) => {
        state.layers[key] = e.target.checked;
        render();
      });
    };
    bindChk("chkTrees", "trees");
    bindChk("chkPlayers", "players");
    bindChk("chkNeutral", "neutral");
    bindChk("chkCamps", "camps");
    bindChk("chkAggro", "aggro");
    bindChk("chkPathing", "pathing");
    bindChk("chkSymmetry", "symmetry");

    document.querySelectorAll(".preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.teamMode = btn.dataset.mode;
        render();
      });
    });

    document.querySelectorAll(".qtab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".qtab").forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        state.quickFilter = tab.dataset.filter;
        populateQuickList();
      });
    });

    document.getElementById("btnZoomIn").addEventListener("click", () => {
      state.zoom = Math.min(7.0, state.zoom * 1.3);
      clampPan();
      render();
    });
    document.getElementById("btnZoomOut").addEventListener("click", () => {
      state.zoom = Math.max(1.0, state.zoom / 1.3);
      clampPan();
      render();
    });
    document.getElementById("btnResetView").addEventListener("click", () => {
      state.zoom = 1.0;
      state.panX = 0;
      state.panY = 0;
      render();
    });

    canvas.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const factor = ev.deltaY < 0 ? 1.18 : 1 / 1.18;
      state.zoom = Math.max(1.0, Math.min(7.0, state.zoom * factor));
      clampPan();
      render();
    }, { passive: false });

    canvas.addEventListener("mousedown", (ev) => {
      state.dragging = true;
      state.dragMoved = false;
      state.lastMouseX = ev.clientX;
      state.lastMouseY = ev.clientY;
    });

    window.addEventListener("mouseup", () => {
      state.dragging = false;
    });

    canvas.addEventListener("mousemove", (ev) => {
      const rect = canvas.getBoundingClientRect();
      const scaleToCanvas = canvas.width / rect.width;

      if (state.dragging && state.zoom > 1.0) {
        const dx = (ev.clientX - state.lastMouseX) * scaleToCanvas;
        const dy = (ev.clientY - state.lastMouseY) * scaleToCanvas;
        if (Math.hypot(dx, dy) > 2) state.dragMoved = true;
        state.panX += dx;
        state.panY += dy;
        state.lastMouseX = ev.clientX;
        state.lastMouseY = ev.clientY;
        clampPan();
        render();
      }

      if (state.data) {
        const sx = (ev.clientX - rect.left) * scaleToCanvas;
        const sy = (ev.clientY - rect.top) * scaleToCanvas;
        const [nx, ny] = screenToNorm(sx, sy);
        if (nx >= 0 && nx <= 1 && ny >= 0 && ny <= 1) {
          const [wx, wy] = normToWorld(nx, ny, state.data.dimensions);
          const tx = Math.min(191, Math.max(0, Math.floor(nx * 192)));
          const wyRow = Math.min(191, Math.max(0, Math.floor((1 - ny) * 192)));
          const wpm = state.data.wpmGrid[wyRow][tx];
          let status = "Dry Buildable Land";
          if (wpm === 0x08) status = "Shallow Walkable Ford";
          else if (wpm === 0x0a) status = "Deep Water (Moat)";
          else if (wpm === 0x48) status = "Walkable Shore/Rock";
          else if (wpm & 0x02) status = "Map Boundary";
          cursorReadout.textContent = `WC3 World: (${Math.round(wx)}, ${Math.round(wy)}) • ${status}`;
        }
      }
    });

    canvas.addEventListener("click", handleCanvasClick);

    // Bulletproof Multi-Method Download Setup (Blob + Direct Server URL + Iframe-Safe Copy)
    const directUrl = new URL("./CrownOfWarMahdi.w3x", window.location.href).href;
    const directInput = document.getElementById("directUrlInput");
    const newTabLink = document.getElementById("linkNewTabDownload");
    const statusEl = document.getElementById("dlStatusMsg");
    const iframeNotice = document.getElementById("iframeNotice");
    const inIframe = (() => {
      try { return window.self !== window.top; } catch (_e) { return true; }
    })();

    if (inIframe && iframeNotice) {
      iframeNotice.classList.remove("hidden");
    }
    if (directInput) {
      directInput.value = directUrl;
      directInput.addEventListener("click", () => {
        directInput.focus();
        directInput.select();
      });
    }
    if (newTabLink) {
      newTabLink.href = directUrl;
    }

    function copyDirectUrlFallback() {
      let copied = false;
      if (directInput) {
        directInput.focus();
        directInput.select();
        directInput.setSelectionRange(0, directInput.value.length);
        try {
          copied = document.execCommand("copy");
        } catch (_err) {
          copied = false;
        }
      }
      return copied;
    }

    const btnBlob = document.getElementById("btnBlobDownload");
    if (btnBlob) {
      btnBlob.addEventListener("click", async () => {
        try {
          let blob;
          if (typeof window.W3X_MAP_B64 === "string" && window.W3X_MAP_B64.length > 100) {
            const binStr = atob(window.W3X_MAP_B64);
            const bytes = new Uint8Array(binStr.length);
            for (let i = 0; i < binStr.length; i++) {
              bytes[i] = binStr.charCodeAt(i);
            }
            blob = new Blob([bytes], { type: "application/octet-stream" });
          } else {
            const resp = await fetch("./CrownOfWarMahdi.w3x");
            blob = await resp.blob();
          }

          const blobUrl = URL.createObjectURL(blob);
          const tmpA = document.createElement("a");
          tmpA.href = blobUrl;
          tmpA.download = "(8)CrownOfWarMahdi.w3x";
          document.body.appendChild(tmpA);
          tmpA.click();
          document.body.removeChild(tmpA);
          setTimeout(() => URL.revokeObjectURL(blobUrl), 15000);

          if (inIframe) {
            copyDirectUrlFallback();
            statusEl.textContent = "اگر مرورگر دانلود داخل کادر را مسدود کرد، لینک دانلود کپی شد — در تب جدید Paste کنید!";
          } else {
            statusEl.textContent = "✓ دانلود فایل (8)CrownOfWarMahdi.w3x آغاز شد!";
          }
        } catch (err) {
          console.error(err);
          copyDirectUrlFallback();
          statusEl.textContent = "لینک دانلود کپی شد — در تب جدید مرورگر Paste کنید.";
        }
      });
    }

    const btnCopy = document.getElementById("btnCopyUrl");
    if (btnCopy) {
      btnCopy.addEventListener("click", async () => {
        let ok = false;
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(directUrl);
            ok = true;
          }
        } catch (_e) {
          ok = false;
        }
        if (!ok) {
          ok = copyDirectUrlFallback();
        }
        statusEl.textContent = ok
          ? "✓ لینک مستقیم کپی شد! در یک تب جدید مرورگر Paste و Enter کنید."
          : "روی کادر آدرس کلیک کرده و Ctrl+C بزنید.";
      });
    }

    // Modal controls
    const modal = document.getElementById("manifestModal");
    document.getElementById("btnOpenManifest").addEventListener("click", async () => {
      modal.classList.remove("hidden");
      try {
        const res = await fetch("./api/archive-manifest");
        const mf = await res.json();
        const ul = document.getElementById("verifyChecksList");
        ul.innerHTML = mf.checks.map((c) => `<li>✓ ${c}</li>`).join("");
        const tb = document.getElementById("mpqTableBody");
        tb.innerHTML = mf.entries
          .map((e) => `<tr><td><code>${e.name}</code></td><td>${e.rawBytes.toLocaleString()} B</td></tr>`)
          .join("");
      } catch (err) {
        console.error(err);
      }
    });

    document.getElementById("btnCloseManifest").addEventListener("click", () => {
      modal.classList.add("hidden");
    });
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });

    document.getElementById("btnLoadJass").addEventListener("click", async () => {
      const box = document.getElementById("jassCodeBox");
      box.classList.toggle("hidden");
      if (!box.textContent) {
        box.textContent = "Loading war3map.j from MPQ archive...";
        const res = await fetch("./api/jass");
        box.textContent = await res.text();
      }
    });
  }

  function renderRaceCard(raceId) {
    const box = document.getElementById("raceDetailBox");
    if (!box || !state.data || !Array.isArray(state.data.races)) return;
    const r = state.data.races.find((x) => x.id === raceId) || state.data.races[0];
    if (!r) return;
    box.innerHTML = `
      <div class="race-pill">${r.badge}</div>
      <div><strong style="color:${r.color}">${r.name}</strong></div>
      <div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">Lobby Pick: <code>${r.lobbyHandicap}</code></div>
      <h4>4 Playable Heroes</h4>
      <div>${r.heroes.map((h) => "• " + h).join("<br/>")}</div>
      <h4>Units &amp; Siege</h4>
      <div>${r.units.map((u) => "• " + u).join("<br/>")}</div>
      <h4>Buildings &amp; 3-Tier Halls</h4>
      <div>${r.buildings.map((b) => "• " + b).join("<br/>")}</div>
    `;
  }

  async function init() {
    bindEvents();
    const res = await fetch("./map_data.json");
    const data = await res.json();
    state.data = data;

    const numberFa = (value) => Number(value || 0).toLocaleString("fa-IR");
    const manifestButton = document.getElementById("btnOpenManifest");
    if (manifestButton) {
      const buildingModels = Number(data.stats.customBuildingModels || 0);
      const allModels = Number(data.stats.customVfxModels || 0) + buildingModels;
      manifestButton.textContent = `${numberFa(data.stats.archiveFiles)} فایل MPQ • ${numberFa(data.stats.blpFiles)} بافت BLP1 • ${numberFa(allModels)} مدل MDX (${numberFa(buildingModels)} ساختمان) • ۱۶ آزمون`;
    }
    const sizeBytes = Number(data.fileSizeBytes || 0);
    const sizeDisplay = document.getElementById("mapSizeDisplay");
    const bytesDisplay = document.getElementById("mapBytesDisplay");
    if (sizeDisplay && sizeBytes > 0) {
      sizeDisplay.textContent = `${(sizeBytes / (1024 * 1024)).toLocaleString("fa-IR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} مگابایت`;
    }
    if (bytesDisplay && sizeBytes > 0) {
      bytesDisplay.textContent = `${numberFa(sizeBytes)} bytes`;
    }

    document.getElementById("stPlayers").textContent = `${data.stats.playableRaces || 6} Races`;
    document.getElementById("stSize").textContent = `${data.dimensions.tilesW}×${data.dimensions.tilesH}`;
    document.getElementById("stMines").textContent = data.stats.goldMines;
    document.getElementById("stCamps").textContent = data.stats.creepCamps;
    document.getElementById("stShops").textContent = data.stats.neutralBuildings;
    document.getElementById("stTrees").textContent = data.stats.trees.toLocaleString();

    renderRaceCard("abyssal");
    document.querySelectorAll("#raceTabs .race-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#raceTabs .race-tab").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        renderRaceCard(btn.getAttribute("data-race"));
      });
    });

    buildOffscreenLayers(data);
    populateQuickList();

    // Pre-select Central Tavern on first load so Inspector is immediately rich!
    const tavern = data.neutralBuildings.find((n) => n.uid === "ntav");
    if (tavern) {
      state.selected = { kind: "neutral", x: tavern.x, y: tavern.y, item: tavern };
      renderInspector(state.selected);
    }
    render();
  }

  init().catch((err) => console.error("Failed to initialize map inspector:", err));
})();
