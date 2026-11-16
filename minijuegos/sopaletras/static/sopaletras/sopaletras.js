(function() {
  'use strict';

  // Conceptos y palabras fallback (RN-81, RN-83)
  const PALABRAS_FALLBACK = [
    {w: "REQUISITO", n: "Requisito", d: "Condición o capacidad que debe cumplir el sistema para satisfacer una necesidad del usuario.", e: "Describe qué debe hacer o cómo debe comportarse el software, no cómo se programa.", k: "Ejemplo", x: "“El jugador debe poder reiniciar un nivel” es un requisito funcional.", color: "#818cf8"},
    {w: "ACTOR", n: "Actor", d: "Rol externo que interactúa con el sistema dentro de un caso de uso.", e: "Puede ser una persona u otro sistema; representa un papel, no a un individuo concreto.", k: "Ejemplo", x: "En SoftQuest, el Jugador es el actor que inicia el caso de uso Jugar sopa de letras.", color: "#34d399"},
    {w: "SPRINT", n: "Sprint", d: "Iteración corta de tiempo fijo en la que un equipo Scrum entrega un incremento del producto.", e: "Suele durar de una a cuatro semanas y termina con una revisión del trabajo hecho.", k: "Cómo se aplica", x: "Un equipo planea un sprint de dos semanas para entregar el módulo de inicio de sesión.", color: "#fbbf24"},
    {w: "BACKLOG", n: "Backlog", d: "Lista priorizada de todo el trabajo pendiente de un producto.", e: "El dueño del producto la ordena según el valor y cambia conforme se aprende del proyecto.", k: "Cómo se aplica", x: "Antes de cada sprint, el equipo toma del backlog las historias de mayor prioridad.", color: "#a78bfa"},
    {w: "PRUEBA", n: "Prueba", d: "Actividad que ejecuta el software con casos definidos para verificar que se comporta como se espera.", e: "Ayuda a detectar defectos antes de que lleguen al usuario.", k: "Ejemplo", x: "Una prueba comprueba que, al encontrar las 8 palabras, el sistema marque la actividad como completada.", color: "#fb923c"},
    {w: "DEFECTO", n: "Defecto", d: "Falla en el código o en un documento que puede provocar un comportamiento incorrecto.", e: "Se registra, se prioriza y se corrige; entre más temprano se detecta, menos cuesta arreglarlo.", k: "Cómo se aplica", x: "Una revisión en pares encuentra un defecto en un caso de uso y lo anota en la bitácora.", color: "#f472b6"},
    {w: "VERSION", n: "Versión", d: "Estado identificable de un producto o documento en un momento determinado.", e: "Permite saber qué cambió, volver a un estado anterior y trabajar en equipo sin perder trabajo.", k: "Cómo se aplica", x: "Un equipo usa Git para guardar cada versión del SRS: V1, V2 y V3.", color: "#38bdf8"},
    {w: "REFACTOR", n: "Refactorización", d: "Mejorar la estructura interna del código sin cambiar su comportamiento visible.", e: "Hace el código más claro y fácil de mantener; se apoya en pruebas para no romper nada.", k: "Cómo se aplica", x: "Dividir una función de 200 líneas en funciones pequeñas con nombres claros.", color: "#a3e635"}
  ];

  const W = (window.CONFIG_SOPALETRAS && window.CONFIG_SOPALETRAS.palabras && window.CONFIG_SOPALETRAS.palabras.length === 8)
    ? window.CONFIG_SOPALETRAS.palabras
    : PALABRAS_FALLBACK;

  const URL_FINALIZAR = (window.CONFIG_SOPALETRAS && window.CONFIG_SOPALETRAS.urlFinalizar) || '';
  const URL_TEMARIO = (window.CONFIG_SOPALETRAS && window.CONFIG_SOPALETRAS.urlTemario) || '/';
  const CSRF_TOKEN = (window.CONFIG_SOPALETRAS && window.CONFIG_SOPALETRAS.csrfToken) || '';

  const $ = s => document.querySelector(s);
  const gridEl = $("#grid");
  if (!gridEl) return;

  // RN-81: 12x12
  const N = 12;
  // RN-82: Horizontal [0,1], vertical [1,0] o diagonal descendente [1,1]
  const D = [[0, 1], [1, 0], [1, 1]];
  const PAL = ["#818cf8", "#34d399", "#fbbf24", "#a78bfa", "#fb923c", "#f472b6", "#38bdf8", "#a3e635"];
  const A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

  let G, P, S, drag, cur, tm;

  const fmt = s => String((s / 60) | 0).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
  const el = (r, c) => $("#grid").children[r * N + c];
  const msg = t => {
    const m = $("#msg");
    if (!m) return;
    m.textContent = t;
    m.hidden = !t;
  };

  function show(id) {
    ["intro", "game", "end"].forEach(i => {
      const el = $("#" + i);
      if (el) el.hidden = (i !== id);
    });
    const hud = $("#hud");
    if (hud) hud.hidden = (id !== "game");
  }

  // Generador de cuadrícula 12x12 cumpliendo RN-81, RN-82, RN-83
  function gen() {
    for (;;) {
      const g = Array.from({ length: N }, () => Array(N).fill(""));
      const p = {};
      let ok = true;
      for (const o of [...W].sort((a, b) => b.w.length - a.w.length)) {
        let done = false;
        for (let t = 0; t < 300 && !done; t++) {
          const [dr, dc] = D[(Math.random() * 3) | 0];
          const L = o.w.length;
          const r = (Math.random() * (N - (dr ? L - 1 : 0))) | 0;
          const c = (Math.random() * (N - (dc ? L - 1 : 0))) | 0;
          let f = true;
          for (let i = 0; i < L; i++) {
            const v = g[r + dr * i][c + dc * i];
            if (v && v !== o.w[i]) {
              f = false;
              break;
            }
          }
          if (f) {
            for (let i = 0; i < L; i++) {
              g[r + dr * i][c + dc * i] = o.w[i];
            }
            p[o.w] = [r, c];
            done = true;
          }
        }
        if (!done) {
          ok = false;
          break;
        }
      }
      if (ok) {
        G = g.map(r => r.map(l => l || A[(Math.random() * 26) | 0]));
        P = p;
        return;
      }
    }
  }

  function start() {
    gen();
    S = {
      sel: null,
      found: {},
      err: 0,
      hint: false,
      t: 0,
      pause: false,
      col: G.map(r => r.map(() => []))
    };

    $("#grid").innerHTML = G.map((r, i) =>
      r.map((l, j) => `<div class="cell" data-r="${i}" data-c="${j}">${l}</div>`).join("")
    ).join("");

    $("#defs").innerHTML = W.map((o, i) =>
      `<li><button class="def" data-i="${i}"><span class="n">${i + 1}</span><span>${o.d}</span></button></li>`
    ).join("");

    show("game");
    msg("Elige una definición para empezar.");
    upd();

    // RN-88: Cronómetro progresivo que inicia al mostrarse la sopa de letras
    clearInterval(tm);
    tm = setInterval(() => {
      if (!S.pause) {
        S.t++;
        upd();
      }
    }, 1000);
  }

  function upd() {
    if (!S) return;
    const f = Object.keys(S.found).length;
    const tmEl = $("#tm");
    const fcEl = $("#fc");
    const barEl = $("#bar");
    const erEl = $("#er");
    const xpEl = $("#xp");
    const hintBtn = $("#hint");

    if (tmEl) tmEl.textContent = fmt(S.t);
    if (fcEl) fcEl.textContent = f + "/8";
    if (barEl) barEl.style.width = (f / 8 * 100) + "%";
    if (erEl) erEl.textContent = S.err;
    // RN-92: Cada error descuenta 5 XP, sin que el XP pueda ser menor a 0
    if (xpEl) xpEl.textContent = Math.max(0, 100 - 5 * S.err);
    if (hintBtn) hintBtn.disabled = S.hint;
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

  // RN-84: Selección de una definición antes de arrastrar
  const defsEl = $("#defs");
  if (defsEl) {
    defsEl.addEventListener("click", e => {
      const b = e.target.closest(".def");
      if (!b) return;
      const i = +b.dataset.i;
      if (S.found[W[i].w]) return;
      S.sel = i;
      document.querySelectorAll(".def").forEach(x => x.classList.toggle("on", x === b));
      msg("Ahora arrastra sobre las letras del concepto.");
    });
  }

  function cellAt(e) {
    const c = document.elementFromPoint(e.clientX, e.clientY)?.closest(".cell");
    return c ? { r: +c.dataset.r, c: +c.dataset.c } : null;
  }

  // RN-85: Línea recta (horizontal, vertical o diagonal)
  function line() {
    if (!drag || !cur) return null;
    const a = cur.r - drag.r;
    const b = cur.c - drag.c;
    const n = Math.max(Math.abs(a), Math.abs(b));
    if (a && b && Math.abs(a) !== Math.abs(b)) return null;
    const sr = Math.sign(a);
    const sc = Math.sign(b);
    return Array.from({ length: n + 1 }, (_, i) => [drag.r + sr * i, drag.c + sc * i]);
  }

  function paint() {
    document.querySelectorAll(".cell.sel").forEach(c => c.classList.remove("sel"));
    if (!drag) return;
    const l = line();
    (l || [[drag.r, drag.c]]).forEach(([r, c]) => {
      const cell = el(r, c);
      if (cell) cell.classList.add("sel");
    });
  }

  $("#grid").addEventListener("pointerdown", e => {
    const c = cellAt(e);
    if (!c) return;
    // RN-84 / Alt 1.3: Arrastre sin definición seleccionada
    if (S.sel == null) {
      msg("Primero selecciona una definición de la lista.");
      return;
    }
    drag = c;
    cur = c;
    paint();
    e.preventDefault();
  });

  document.addEventListener("pointermove", e => {
    if (!drag) return;
    const c = cellAt(e);
    if (c) {
      cur = c;
      paint();
    }
  });

  document.addEventListener("pointerup", () => {
    if (!drag) return;
    const cs = line();
    drag = null;
    paint();
    // RN-85 / Alt 1.2: Selección inválida (no forma línea recta o contiene una sola letra)
    if (!cs || cs.length < 2) {
      msg("Selección inválida: arrastra en línea recta (horizontal, vertical o diagonal de 2 o más letras).");
      return;
    }
    check(cs);
  });

  document.addEventListener("pointercancel", () => {
    drag = null;
    paint();
  });

  function check(cs) {
    const s = cs.map(([r, c]) => G[r][c]).join("");
    const o = W[S.sel];

    // RN-84: Se evalúa contra la palabra de esa definición sin importar el sentido del arrastre
    if (s === o.w || [...s].reverse().join("") === o.w) {
      return ok(cs, o);
    }

    // RN-87 / Alt 1.1: Selección incorrecta
    S.err++;
    msg("Incorrecto: esas letras no forman el concepto de la definición seleccionada (-5 XP).");
    const g = $("#grid");
    if (g) {
      g.classList.add("shake");
      setTimeout(() => g.classList.remove("shake"), 400);
    }
    upd();
  }

  function ok(cs, o) {
    const i = S.sel;
    const col = o.color || PAL[i];
    S.found[o.w] = 1;
    S.sel = null;
    S.pause = true; // RN-88: Detiene cronómetro mientras muestra explicación

    // RN-86: Marca letras con color
    cs.forEach(([r, c]) => {
      const k = S.col[r][c];
      k.push(col);
      const e = el(r, c);
      if (e) {
        e.classList.remove("hint");
        e.classList.add("fd");
        e.style.background = k.length > 1
          ? `linear-gradient(135deg, ${k[0]} 50%, ${k[k.length - 1]} 50%)`
          : k[0];
      }
    });

    // RN-86: Bloquea definición y muestra ícono de verificación
    const b = document.querySelector(`.def[data-i="${i}"]`);
    if (b) {
      b.classList.remove("on");
      b.classList.add("fd");
      b.disabled = true;
      b.style.borderColor = col;
      b.style.background = col + "40";
      b.style.color = "inherit";
      const nEl = b.querySelector(".n");
      if (nEl) nEl.textContent = "✓";
    }

    msg("¡Correcto!");
    upd();

    // RN-90: Explicación del concepto y ejemplo o cómo se aplica
    const modalHtml = `
      <div class="mh" style="background:${col}">
        <span class="lb">Concepto encontrado</span>
        <h2>${o.n}</h2>
      </div>
      <div class="mb">
        <span class="lb">Explicación</span>
        <p>${o.e}</p>
        <div class="ex">
          <span class="lb">${o.k || "Ejemplo"}</span>
          ${o.x}
        </div>
        <button class="btn" id="go">Continuar</button>
      </div>
    `;

    modal(modalHtml, () => {
      S.pause = false; // Reanuda cronómetro (Paso 10)
      if (Object.keys(S.found).length === W.length) {
        finish(); // RN-93: Completa actividad al encontrar las 8 palabras
      } else {
        msg("Elige otra definición.");
      }
    });
  }

  // RN-89 / Alt 1.4: Uso de la pista (resalta primera letra de la definición seleccionada)
  const hintBtn = $("#hint");
  if (hintBtn) {
    hintBtn.onclick = () => {
      if (S.sel == null) {
        msg("Selecciona una definición para pedir la pista.");
        return;
      }
      if (S.hint) return;
      S.hint = true;
      const [r, c] = P[W[S.sel].w];
      const cell = el(r, c);
      if (cell) cell.classList.add("hint");
      msg("Pista: la palabra empieza en la letra resaltada. No suma errores ni resta XP.");
      upd();
    };
  }

  // RN-112 / Alt 1.5: Abandonar actividad
  const exitBtn = $("#exit");
  if (exitBtn) {
    exitBtn.onclick = () => {
      modal(`
        <div class="mb">
          <h2 style="margin:0 0 8px;font-size:1.15rem;font-weight:800">¿Salir de la actividad?</h2>
          <p style="color:var(--mu)">No se conservará tu progreso y la actividad quedará sin completar. El cronómetro sigue corriendo.</p>
          <div class="row">
            <button class="btn g" id="cn">Cancelar</button>
            <button class="btn" id="go">Salir</button>
          </div>
        </div>
      `, () => {
        clearInterval(tm);
        window.location.href = URL_TEMARIO;
      });
    };
  }

  // RN-91, RN-92, RN-93, POST-2, POST-4: Finalización de la actividad
  function finish() {
    clearInterval(tm);
    const xp = Math.max(0, 100 - 5 * S.err);

    // Registrar resultado en el backend vía POST
    if (URL_FINALIZAR) {
      fetch(URL_FINALIZAR, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF_TOKEN
        },
        body: JSON.stringify({
          palabras_encontradas: Object.keys(S.found).length,
          errores: S.err,
          pista_usada: S.hint,
          tiempo_segundos: S.t,
          completada: true
        })
      }).then(res => res.json()).catch(err => {
        console.warn("No se pudo registrar el resultado en el servidor:", err);
      });
    }

    const endEl = $("#end");
    if (!endEl) return;

    endEl.innerHTML = `
      <div class="card" style="max-width:680px;margin:0 auto">
        <div class="bn">
          <div class="bi">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="m5 12 5 5 9-10"/>
            </svg>
          </div>
          <h2>¡Actividad completada!</h2>
        </div>
        <div class="bd">
          <p>¡Felicidades! Has encontrado todas las palabras. Siguiente actividad desbloqueada en el temario.</p>
          <div class="sg">
            <div class="hc sf"><span class="lb">Tiempo</span><b>${fmt(S.t)}</b></div>
            <div class="hc"><span class="lb">Errores</span><b>${S.err}</b></div>
            <div class="hc"><span class="lb">Pista</span><b>${S.hint ? "Usada" : "Sin usar"}</b></div>
            <div class="hc cr"><span class="lb">XP obtenido</span><b>${xp}/100</b></div>
          </div>
          <span class="lb" style="display:block;margin-bottom:8px">Repaso pedagógico</span>
          ${W.map((o, i) => `
            <article class="rv" style="border-left-color:${o.color || PAL[i]}">
              <h4>${o.n}</h4>
              <p>${o.d}</p>
              <p>${o.e}</p>
              <p><b>${o.k || "Ejemplo"}:</b> ${o.x}</p>
            </article>
          `).join("")}
          <div class="row" style="margin-top:16px">
            <button class="btn" id="again">Jugar de nuevo</button>
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

  const go0 = $("#go0");
  if (go0) go0.onclick = start;
})();
