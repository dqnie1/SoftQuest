(function() {
  'use strict';

  // Configuración de conceptos (fallback en caso de que no se inyecte desde el servidor)
  const CONCEPTOS_FALLBACK = [
    {id: 1, nombre:"Refactorización", tipo:"positivo", es_positivo:true, nombre_corto:"Refactor", efecto_clave:"wide", efecto_descripcion:"Paleta 50 % más ancha durante 10 s.", definicion:"Mejorar la estructura interna del código sin cambiar su comportamiento visible.", explicacion:"Hace el código más claro y fácil de mantener; se apoya en pruebas para no romper nada.", tipo_ejemplo:"Cómo se aplica", ejemplo:"Dividir una función de 200 líneas en funciones pequeñas con nombres claros.", color:"#818cf8"},
    {id: 2, nombre:"Pruebas unitarias", tipo:"positivo", es_positivo:true, nombre_corto:"Unit tests", efecto_clave:"shield", efecto_descripcion:"Red de seguridad bajo la paleta: rescata la pelota una sola vez.", definicion:"Pruebas que verifican que una pieza pequeña de código funcione de forma aislada.", explicacion:"Detectan fallos pronto y dan seguridad para cambiar el código.", tipo_ejemplo:"Ejemplo", ejemplo:"Una prueba comprueba que el cálculo de XP devuelva 80 cuando se pierden dos vidas.", color:"#34d399"},
    {id: 3, nombre:"Integración continua", tipo:"positivo", es_positivo:true, nombre_corto:"CI", efecto_clave:"multi", efecto_descripcion:"Se duplican las pelotas en juego (máximo 6 simultáneas).", definicion:"Práctica de integrar y probar el código del equipo con frecuencia.", explicacion:"Cada cambio se compila y se prueba de forma automática, así los fallos aparecen pronto.", tipo_ejemplo:"Cómo se aplica", ejemplo:"Cada vez que alguien sube código, un servidor corre todas las pruebas del proyecto.", color:"#fbbf24"},
    {id: 4, nombre:"Depuración", tipo:"positivo", es_positivo:true, nombre_corto:"Debug", efecto_clave:"slow", efecto_descripcion:"La velocidad de las pelotas se reduce 35 % durante 10 s.", definicion:"Proceso de encontrar la causa de un error y corregirlo.", explicacion:"Se reproduce el fallo, se localiza la causa y se comprueba que la corrección funcione.", tipo_ejemplo:"Cómo se aplica", ejemplo:"Poner un punto de interrupción para ver por qué el XP sale negativo.", color:"#a78bfa"},
    {id: 5, nombre:"Revisión de código", tipo:"positivo", es_positivo:true, nombre_corto:"Code review", efecto_clave:"pierce", efecto_descripcion:"La pelota atraviesa hasta 3 bloques en total y luego vuelve a rebotar de forma normal.", definicion:"Revisión que otra persona hace del código antes de integrarlo.", explicacion:"Detecta defectos y errores de diseño, y comparte conocimiento dentro del equipo.", tipo_ejemplo:"Cómo se aplica", ejemplo:"Un compañero señala que una función no valida entradas vacías antes de aprobarla.", color:"#fb923c"},
    {id: 6, nombre:"Control de versiones", tipo:"positivo", es_positivo:true, nombre_corto:"Git", efecto_clave:"revert", efecto_descripcion:"Revierte los efectos negativos activos.", definicion:"Sistema que guarda el historial de cambios y permite volver a estados anteriores.", explicacion:"Permite trabajar en equipo sin perder trabajo y deshacer cambios que salieron mal.", tipo_ejemplo:"Cómo se aplica", ejemplo:"Un equipo usa git revert para deshacer un commit que introdujo un error.", color:"#f472b6"},
    {id: 7, nombre:"Bug", tipo:"negativo", es_positivo:false, nombre_corto:"Bug", efecto_clave:"narrow", efecto_descripcion:"Paleta 35 % más angosta durante 8 s.", definicion:"Defecto en el software que provoca un resultado incorrecto o inesperado.", explicacion:"Se registra, se prioriza y se corrige; entre más tarde se detecta, más cuesta arreglarlo.", tipo_ejemplo:"Ejemplo", ejemplo:"El botón de reiniciar nivel borra también el progreso guardado.", color:"#38bdf8"},
    {id: 8, nombre:"Deuda técnica", tipo:"negativo", es_positivo:false, nombre_corto:"Deuda técnica", efecto_clave:"fast", efecto_descripcion:"Velocidad de las pelotas 40 % mayor durante 8 s.", definicion:"Costo futuro de elegir una solución rápida en lugar de la mejor.", explicacion:"Acelera la entrega hoy, pero hace más lento y riesgoso cambiar el sistema después.", tipo_ejemplo:"Ejemplo", ejemplo:"Copiar el mismo código en cinco pantallas para entregar antes.", color:"#a3e635"}
  ];

  const C = (window.CONFIG_CODEBREAKER && window.CONFIG_CODEBREAKER.conceptos && window.CONFIG_CODEBREAKER.conceptos.length === 8)
    ? window.CONFIG_CODEBREAKER.conceptos
    : CONCEPTOS_FALLBACK;

  const URL_FINALIZAR = (window.CONFIG_CODEBREAKER && window.CONFIG_CODEBREAKER.urlFinalizar) || '';
  const URL_TEMARIO = (window.CONFIG_CODEBREAKER && window.CONFIG_CODEBREAKER.urlTemario) || '/';
  const CSRF_TOKEN = (window.CONFIG_CODEBREAKER && window.CONFIG_CODEBREAKER.csrfToken) || '';

  const $ = s => document.querySelector(s);
  const cv = $("#cv");
  if (!cv) return;

  const ctx = cv.getContext("2d");
  const W = 640, H = 480;
  const COLS = 10, ROWS = 6, BW = 56, BH = 20, GAP = 4, LEFT = 22, TOP = 30, PY = H - 34, PH = 12, R = 7, SP = 5.2;
  const ROW_COLORS = ["#c7d2fe", "#a7f3d0", "#fde68a", "#ddd6fe", "#fed7aa", "#fbcfe8"];
  const PAL = ["#818cf8", "#34d399", "#fbbf24", "#a78bfa", "#fb923c", "#f472b6", "#38bdf8", "#a3e635"];

  let S = null;
  let keys = { l: 0, r: 0 };
  let last = 0;
  let prev = "play";

  // Cálculo dinámico del ancho de la paleta según efectos activos (RN-101, RN-103)
  const pw = () => 90 * (S.fx.wide > 0 ? 1.5 : 1) * (S.fx.narrow > 0 ? 0.65 : 1);

  const msg = t => {
    const el = $("#msg");
    if (!el) return;
    el.textContent = t;
    el.hidden = !t;
  };

  function show(id) {
    ["intro", "game", "end"].forEach(i => {
      const el = $("#" + i);
      if (el) el.hidden = (i !== id);
    });
    const hud = $("#hud");
    if (hud) hud.hidden = (id !== "game");
  }

  function modal(html, onGo, onCn) {
    const md = $("#md");
    const ov = $("#ov");
    if (!md || !ov) return;
    md.innerHTML = html;
    ov.hidden = false;

    const goBtn = $("#go");
    if (goBtn) {
      goBtn.onclick = () => {
        ov.hidden = true;
        if (onGo) onGo();
      };
      goBtn.focus();
    }
    const cnBtn = $("#cn");
    if (cnBtn) {
      cnBtn.onclick = () => {
        ov.hidden = true;
        if (onCn) onCn();
      };
    }
  }

  function start() {
    // RN-96 y RN-97: 60 bloques (6x10), 8 bloques especiales ubicados aleatoriamente en cada partida
    const pos = [...Array(ROWS * COLS).keys()].sort(() => Math.random() - 0.5).slice(0, 8);
    const br = [];
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        br.push({
          x: LEFT + c * (BW + GAP),
          y: TOP + r * (BH + GAP),
          r: r,
          a: 1, // activo
          cid: -1 // índice de concepto (0..7) o -1 si bloque normal
        });
      }
    }
    pos.forEach((p, i) => {
      br[p].cid = i;
    });

    // Estado de la partida
    S = {
      br: br,
      balls: [],
      drops: [],
      lives: 3, // RN-105: 3 vidas por partida
      lost: 0,  // vidas perdidas acumuladas
      fx: { wide: 0, narrow: 0, slow: 0, fast: 0 },
      shield: false, // RN-101: Pruebas unitarias
      pierce: 0,     // RN-102: Revisión de código (hasta 3 bloques)
      px: W / 2 - 45,
      st: "ready",   // ready | play | pause | end
      got: new Set(),
      left: 60,
      chips: ""
    };

    newBall();

    const defsEl = $("#defs");
    if (defsEl) {
      defsEl.innerHTML = C.map((c, i) =>
        `<li><div class="def" id="d${i}"><span class="n">?</span><span>Concepto por descubrir</span></div></li>`
      ).join("");
    }

    show("game");
    msg("Mueve la paleta y lanza la pelota con clic, toque o barra espaciadora.");
    upd();
  }

  function newBall() {
    S.balls = [{
      x: S.px + pw() / 2,
      y: PY - R,
      dx: 0,
      dy: -1
    }];
  }

  function norm(b) {
    if (Math.abs(b.dy) < 0.22) {
      b.dy = (b.dy < 0 ? -1 : 1) * 0.22;
    }
    const m = Math.hypot(b.dx, b.dy);
    if (m > 0) {
      b.dx /= m;
      b.dy /= m;
    }
  }

  function upd() {
    if (!S) return;
    const bc = $("#bc");
    const bar = $("#bar");
    const lv = $("#lv");
    const cc = $("#cc");
    const xp = $("#xp");

    if (bc) bc.textContent = (60 - S.left) + "/60";
    if (bar) bar.style.width = ((60 - S.left) / 60 * 100) + "%";
    if (lv) lv.textContent = "♥".repeat(S.lives) + "♡".repeat(3 - S.lives);
    if (cc) cc.textContent = S.got.size + "/8";
    if (xp) xp.textContent = Math.max(0, 100 - 10 * S.lost);

    const f = S.fx;
    const ch = [];
    if (f.wide > 0) ch.push(["Paleta ancha " + Math.ceil(f.wide) + " s", "#0cc08b"]);
    if (f.narrow > 0) ch.push(["Paleta angosta " + Math.ceil(f.narrow) + " s", "#ef4444"]);
    if (f.slow > 0) ch.push(["Pelota lenta " + Math.ceil(f.slow) + " s", "#0cc08b"]);
    if (f.fast > 0) ch.push(["Pelota rápida " + Math.ceil(f.fast) + " s", "#ef4444"]);
    if (S.shield) ch.push(["Red de seguridad", "#5b5bf0"]);
    if (S.pierce > 0) ch.push(["Atraviesa " + S.pierce + " bloque" + (S.pierce > 1 ? "s" : ""), "#d97706"]);

    const h = ch.map(c => `<span style="background:${c[1]}">${c[0]}</span>`).join("");
    if (h !== S.chips) {
      S.chips = h;
      const fxs = $("#fxs");
      if (fxs) fxs.innerHTML = h;
    }
  }

  function spawn(k) {
    // RN-99: Suelta una cápsula con el nombre de su concepto
    S.drops.push({
      x: k.x + BW / 2,
      y: k.y + BH / 2,
      i: k.cid
    });
  }

  function apply(c) {
    // RN-101, RN-103, RN-104: Aplicación y cancelación de efectos
    const f = S.fx;
    if (c.efecto_clave === "wide") {
      f.wide = 10;
      f.narrow = 0; // RN-104: Cancela efecto contrario
    }
    if (c.efecto_clave === "narrow") {
      f.narrow = 8;
      f.wide = 0;   // RN-104: Cancela efecto contrario
    }
    if (c.efecto_clave === "slow") {
      f.slow = 10;
      f.fast = 0;   // RN-104: Cancela efecto contrario
    }
    if (c.efecto_clave === "fast") {
      f.fast = 8;
      f.slow = 0;   // RN-104: Cancela efecto contrario
    }
    if (c.efecto_clave === "shield") {
      S.shield = true;
    }
    if (c.efecto_clave === "pierce") {
      S.pierce = 3; // RN-102: Atraviesa hasta 3 bloques
    }
    if (c.efecto_clave === "revert") {
      f.narrow = 0;
      f.fast = 0;   // Revierte efectos negativos
    }
    if (c.efecto_clave === "multi") {
      // RN-101: Duplica pelotas en juego (máximo 6 simultáneas)
      const add = [];
      for (const b of S.balls) {
        if (S.balls.length + add.length >= 6) break;
        const a = Math.atan2(b.dy, b.dx) + 0.5;
        const n = { x: b.x, y: b.y, dx: Math.cos(a), dy: Math.sin(a) };
        norm(n);
        add.push(n);
      }
      S.balls.push(...add);
    }
  }

  function collect(i) {
    const c = C[i];
    S.st = "pause"; // RN-100: Pausa la partida
    S.got.add(i);

    const d = $("#d" + i);
    if (d) {
      d.classList.add("fd");
      d.style.borderColor = c.color || PAL[i];
      d.style.background = (c.color || PAL[i]) + "40";
      const esPos = (c.tipo === "positivo" || c.es_positivo);
      d.innerHTML = `<span class="n">✓</span><span>${c.nombre}</span><small style="color:${esPos ? '#0a9a70' : '#dc2626'}">${esPos ? 'Positivo' : 'Negativo'}</small>`;
    }
    upd();

    const esPos = (c.tipo === "positivo" || c.es_positivo);
    const modalHtml = `
      <div class="mh" style="background:${c.color || PAL[i]}">
        <span class="lb">Concepto recolectado · ${esPos ? "efecto positivo" : "efecto negativo"}</span>
        <h2>${c.nombre}</h2>
      </div>
      <div class="mb">
        <span class="lb">Definición</span>
        <p>${c.definicion}</p>
        <span class="lb">Explicación</span>
        <p>${c.explicacion}</p>
        <div class="ex">
          <span class="lb">${c.tipo_ejemplo || "Ejemplo"}</span>
          ${c.ejemplo}
        </div>
        <div class="ef ${esPos ? "g" : "b"}">
          <span class="lb">Efecto en la partida</span>
          ${c.efecto_descripcion}
        </div>
        <button class="btn" id="go">Continuar</button>
      </div>
    `;

    modal(modalHtml, () => {
      // Al presionar Continuar: se reanuda y se aplica el efecto
      apply(c);
      S.st = "play";
      upd();
      msg(esPos ? ("Efecto activado: " + c.nombre + ".") : ("Efecto negativo: " + c.nombre + "."));
    });
  }

  function launch() {
    if (S && S.st === "ready" && $("#ov").hidden) {
      const b = S.balls[0];
      b.dx = 0.3 * (Math.random() < 0.5 ? -1 : 1);
      b.dy = -1;
      norm(b);
      S.st = "play";
      msg("");
    }
  }

  function update(dt) {
    if (!S || (S.st !== "play" && S.st !== "ready")) return;

    const w = pw();
    S.px += (keys.r - keys.l) * 8 * dt;
    S.px = Math.max(0, Math.min(W - w, S.px));

    // Tiempo de efectos (se detiene cuando está en pausa gracias al check de estado arriba)
    for (const k in S.fx) {
      if (S.fx[k] > 0) {
        S.fx[k] = Math.max(0, S.fx[k] - dt / 60);
      }
    }

    if (S.st === "ready") {
      S.balls[0].x = S.px + w / 2;
      S.balls[0].y = PY - R;
      upd();
      return;
    }

    const mul = (S.fx.slow > 0 ? 0.65 : 1) * (S.fx.fast > 0 ? 1.4 : 1);

    for (const b of S.balls) {
      b.x += b.dx * SP * mul * dt;
      b.y += b.dy * SP * mul * dt;

      // Colisiones con bordes
      if (b.x < R) { b.x = R; b.dx = Math.abs(b.dx); }
      if (b.x > W - R) { b.x = W - R; b.dx = -Math.abs(b.dx); }
      if (b.y < R) { b.y = R; b.dy = Math.abs(b.dy); }

      // Colisión con paleta
      if (b.dy > 0 && b.y + R >= PY && b.y - R <= PY + PH && b.x >= S.px - R && b.x <= S.px + w + R) {
        const a = Math.max(-1, Math.min(1, (b.x - (S.px + w / 2)) / (w / 2))) * 1.05;
        b.dx = Math.sin(a);
        b.dy = -Math.cos(a);
        b.y = PY - R;
      }

      // Colisión con bloques
      for (const k of S.br) {
        if (!k.a) continue;
        const cx = Math.max(k.x, Math.min(b.x, k.x + BW));
        const cy = Math.max(k.y, Math.min(b.y, k.y + BH));
        const ddx = b.x - cx;
        const ddy = b.y - cy;

        if (ddx * ddx + ddy * ddy <= R * R) {
          k.a = 0;
          S.left--;
          if (k.cid >= 0) spawn(k);

          // RN-102: Revisión de código atraviesa bloques
          if (S.pierce > 0) {
            S.pierce--;
            continue;
          }

          if (ddx === 0 && ddy === 0) {
            b.dy = -b.dy;
          } else if (Math.abs(ddx) > Math.abs(ddy)) {
            b.dx = -b.dx;
          } else {
            b.dy = -b.dy;
          }
          norm(b);
          break;
        }
      }

      // RN-101 / Alt 1.2: Red de seguridad rescata la pelota una vez
      if (S.shield && b.dy > 0 && b.y + R >= H - 6) {
        b.dy = -Math.abs(b.dy);
        b.y = H - 6 - R;
        S.shield = false;
        msg("La red de seguridad rescató la pelota.");
      }
    }

    // Filtrar pelotas que cayeron
    S.balls = S.balls.filter(b => b.y < H + R * 2);

    // Caída de cápsulas (RN-99)
    for (const d of S.drops) d.y += 2.2 * dt;
    S.drops = S.drops.filter(d => {
      // Atrapada por la paleta
      if (S.st === "play" && d.y + 10 >= PY && d.y - 10 <= PY + PH && d.x >= S.px - 34 && d.x <= S.px + w + 34) {
        collect(d.i);
        return false;
      }
      // Llega al borde inferior sin penalización (Alt 1.4)
      return d.y < H + 20;
    });

    if (S.st === "play") {
      if (S.left === 0) {
        finish(true);
      } else if (!S.balls.length) {
        // RN-106: Se pierde la última pelota en juego
        S.lives--;
        S.lost++;
        S.fx = { wide: 0, narrow: 0, slow: 0, fast: 0 };
        S.shield = false;
        S.pierce = 0;
        S.drops = [];

        if (S.lives === 0) {
          finish(false); // RN-107: Pierde las 3 vidas
        } else {
          S.st = "ready";
          newBall();
          msg("Perdiste una vida. Lanza de nuevo cuando estés listo.");
        }
      }
    }

    upd();
  }

  function rr(x, y, w, h, r) {
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(x, y, w, h, r);
    } else {
      ctx.rect(x, y, w, h);
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    if (!S) return;

    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    // Bloques
    for (const k of S.br) {
      if (!k.a) continue;
      ctx.fillStyle = k.cid >= 0 ? "#ffb400" : ROW_COLORS[k.r];
      rr(k.x, k.y, BW, BH, 5);
      ctx.fill();
      if (k.cid >= 0) {
        ctx.fillStyle = "#1e293b";
        ctx.font = "800 13px monospace";
        ctx.fillText("{ }", k.x + BW / 2, k.y + BH / 2 + 1);
      }
    }

    // Red de seguridad (Pruebas unitarias)
    if (S.shield) {
      ctx.fillStyle = "#0cc08b";
      ctx.fillRect(0, H - 6, W, 4);
    }

    // Paleta
    const w = pw();
    ctx.fillStyle = S.fx.narrow > 0 ? "#ef4444" : (S.fx.wide > 0 ? "#0cc08b" : "#5b5bf0");
    rr(S.px, PY, w, PH, 6);
    ctx.fill();

    // Pelotas
    ctx.fillStyle = S.pierce > 0 ? "#ffb400" : "#1e293b";
    for (const b of S.balls) {
      ctx.beginPath();
      ctx.arc(b.x, b.y, R, 0, Math.PI * 2);
      ctx.fill();
    }

    // Cápsulas cayendo
    ctx.font = "700 11px 'Plus Jakarta Sans', sans-serif";
    for (const d of S.drops) {
      const c = C[d.i];
      const esPos = (c.tipo === "positivo" || c.es_positivo);
      ctx.fillStyle = esPos ? "#0cc08b" : "#ef4444";
      rr(d.x - 36, d.y - 10, 72, 20, 10);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.fillText(c.nombre_corto || c.nombre, d.x, d.y + 1);
    }

    // Indicador en estado listo para lanzar
    if (S.st === "ready") {
      ctx.fillStyle = "#eceffd";
      rr(W / 2 - 150, PY - 70, 300, 30, 15);
      ctx.fill();
      ctx.fillStyle = "#3730a3";
      ctx.font = "700 13px 'Plus Jakarta Sans', sans-serif";
      ctx.fillText("Clic, toque o espacio para lanzar", W / 2, PY - 55);
    }
  }

  function finish(win) {
    S.st = "end";

    // RN-111: Máx 100 XP, descuenta 10 por vida perdida. 0 XP si no se completa.
    const xp = win ? Math.max(0, 100 - 10 * S.lost) : 0;
    // RN-109: Al ganar muestra los 8 conceptos indicando cuáles recolectó
    // RN-110: Al perder muestra sólo los conceptos recolectados
    const idx = win ? C.map((c, i) => i) : [...S.got].sort((a, b) => a - b);
    const bc = win ? "var(--amb)" : "#f87171";

    const conceptosIds = [...S.got].map(i => C[i].id || i);

    // RN-113: Registrar resultado en el backend
    if (URL_FINALIZAR) {
      fetch(URL_FINALIZAR, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF_TOKEN
        },
        body: JSON.stringify({
          vidas_perdidas: S.lost,
          conceptos_ids: conceptosIds,
          completada: win
        })
      }).then(res => res.json()).catch(err => {
        console.warn("No se pudo registrar el resultado en el servidor:", err);
      });
    }

    const endEl = $("#end");
    if (!endEl) return;

    endEl.innerHTML = `
      <div class="card" style="max-width:680px;margin:0 auto">
        <div class="bn" style="background:${bc}">
          <div class="bi">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="${win ? "m5 12 5 5 9-10" : "M6 6l12 12M18 6 6 18"}"/>
            </svg>
          </div>
          <h2>${win ? "¡Actividad completada!" : "Te quedaste sin vidas"}</h2>
        </div>
        <div class="bd">
          <p>${win ? "¡Felicidades! Siguiente actividad desbloqueada en el temario." : "La actividad no se completó y no se otorga XP. Inténtalo de nuevo para avanzar."}</p>
          <div class="sg">
            <div class="hc hr"><span class="lb">Vidas perdidas</span><b>${S.lost}</b></div>
            <div class="hc sf"><span class="lb">Conceptos</span><b>${S.got.size}/8</b></div>
            <div class="hc cr"><span class="lb">XP obtenido</span><b>${xp}/100</b></div>
          </div>
          <span class="lb" style="display:block;margin-bottom:8px">Repaso${win ? "" : " de los conceptos recolectados"}</span>
          ${idx.length ? idx.map(i => {
            const c = C[i];
            const recolectado = S.got.has(i);
            return `
              <article class="rv" style="border-left-color:${c.color || PAL[i]}">
                <h4>${c.nombre}${win && !recolectado ? "<em>No recolectado</em>" : ""}</h4>
                <p>${c.definicion}</p>
                <p>${c.explicacion}</p>
                <p><b>${c.tipo_ejemplo || "Ejemplo"}:</b> ${c.ejemplo}</p>
              </article>
            `;
          }).join("") : `<p>No recolectaste ningún concepto en esta partida.</p>`}
          <div class="row" style="margin-top:16px">
            <button class="btn" id="again">${win ? "Jugar de nuevo" : "Reintentar actividad"}</button>
            <button class="btn g" id="back">Regresar al temario</button>
          </div>
        </div>
      </div>
    `;

    show("end");
    $("#again").onclick = start;
    $("#back").onclick = () => {
      window.location.href = URL_TEMARIO;
    };
    window.scrollTo(0, 0);
  }

  // RN-112, Alt 1.6: El jugador decide salir o abandonar la actividad
  const exitBtn = $("#exit");
  if (exitBtn) {
    exitBtn.onclick = () => {
      if (!S) return;
      prev = S.st;
      if (S.st === "play") S.st = "pause";
      modal(`
        <div class="mb">
          <h2 style="margin:0 0 8px;font-size:1.15rem;font-weight:800">¿Salir de la actividad?</h2>
          <p style="color:var(--mu)">No se conservará tu progreso y la actividad quedará sin completar. La partida está en pausa.</p>
          <div class="row">
            <button class="btn g" id="cn">Cancelar</button>
            <button class="btn" id="go">Salir</button>
          </div>
        </div>
      `, () => {
        S.st = "end";
        window.location.href = URL_TEMARIO;
      }, () => {
        S.st = prev;
      });
    };
  }

  function moveTo(e) {
    if (!S || (S.st !== "play" && S.st !== "ready")) return;
    const r = cv.getBoundingClientRect();
    S.px = Math.max(0, Math.min(W - pw(), (e.clientX - r.left) * W / r.width - pw() / 2));
  }

  cv.addEventListener("pointermove", moveTo);
  cv.addEventListener("pointerdown", e => {
    moveTo(e);
    launch();
  });

  addEventListener("keydown", e => {
    if ($("#game").hidden || !$("#ov").hidden) return;
    if (e.key === "ArrowLeft" || e.key === "a" || e.key === "A") keys.l = 1;
    if (e.key === "ArrowRight" || e.key === "d" || e.key === "D") keys.r = 1;
    if (e.key === " ") {
      e.preventDefault();
      launch();
    }
  });

  addEventListener("keyup", e => {
    if (e.key === "ArrowLeft" || e.key === "a" || e.key === "A") keys.l = 0;
    if (e.key === "ArrowRight" || e.key === "d" || e.key === "D") keys.r = 0;
  });

  function frame(t) {
    const dt = Math.min(2.5, (t - last) / 16.667);
    last = t;
    update(dt);
    draw();
    requestAnimationFrame(frame);
  }

  const go0 = $("#go0");
  if (go0) go0.onclick = start;

  requestAnimationFrame(t => {
    last = t;
    frame(t);
  });
})();
