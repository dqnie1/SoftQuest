(() => {
    const FRUTAS = JSON.parse(document.getElementById('ninjacode-frutas').textContent);
    const CFG = JSON.parse(document.getElementById('ninjacode-config').textContent);
    const URLS = JSON.parse(document.getElementById('ninjacode-urls').textContent);
    const SHAPES = ['manzana', 'naranja', 'sandia', 'fresa', 'limon', 'pera', 'platano'];
    const TOTAL = CFG.frutasNivel || 16;
    const OK_COUNT = CFG.aciertosMazo || 10;
    const PTS = CFG.puntosAcierto || 25;
    const GRAVITY = 620;

    const FUNCIONALES = FRUTAS.filter((f) => f.tipo === 'FUNCIONAL');
    const NO_FUNCIONALES = FRUTAS.filter((f) => f.tipo === 'NO_FUNCIONAL');

    const els = {
        arena: document.getElementById('arena'),
        frutas: document.getElementById('frutas'),
        slash: document.getElementById('slash'),
        toast: document.getElementById('toast'),
        comboPop: document.getElementById('combo-pop'),
        overlay: document.getElementById('overlay'),
        modal: document.getElementById('modal'),
        score: document.getElementById('hud-score'),
        lives: document.getElementById('hud-lives'),
        combo: document.getElementById('hud-combo'),
        nivel: document.getElementById('hud-nivel'),
        barra: document.getElementById('barra'),
        pill: document.getElementById('pill'),
        sonido: document.getElementById('btn-sonido'),
    };
    const ctx = els.slash.getContext('2d');

    const Sfx = {
        on: true,
        ac: null,
        beep(freq, dur = 0.08, type = 'sine', vol = 0.04) {
            if (!this.on) return;
            this.ac = this.ac || new (window.AudioContext || window.webkitAudioContext)();
            const o = this.ac.createOscillator();
            const g = this.ac.createGain();
            o.type = type;
            o.frequency.value = freq;
            g.gain.setValueAtTime(vol, this.ac.currentTime);
            g.gain.exponentialRampToValueAtTime(0.001, this.ac.currentTime + dur);
            o.connect(g); g.connect(this.ac.destination);
            o.start(); o.stop(this.ac.currentTime + dur);
        },
        ok() { this.beep(620, 0.08); this.beep(880, 0.12); },
        bad() { this.beep(180, 0.16, 'sawtooth', 0.035); },
        combo() { this.beep(740, 0.08); },
        win() { this.beep(523, 0.1); setTimeout(() => this.beep(784, 0.16), 90); },
        lose() { this.beep(160, 0.28, 'sawtooth', 0.04); },
    };

    let mode = 'intro';
    let paused = false;
    let slicing = false;
    let trail = [];
    let fruits = [];
    let lastTs = 0;
    let toastT = 0;
    let spawnT = 0;
    let spawned = 0;
    let size = { w: 1000, h: 560 };
    let deck = [];
    let cortes = [];
    let erroresNivel = [];
    let erroresN1 = [];
    let erroresN2 = [];
    let guardando = false;

    const state = {
        level: 1, lives: CFG.vidas || 3, score: 0, combo: 0, maxCombo: 0,
        hits: 0, errors: 0, score1: 0, score2: 0, hits1: 0, errors1: 0, missed: 0,
    };

    function shuffle(a) {
        const x = a.slice();
        for (let i = x.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [x[i], x[j]] = [x[j], x[i]];
        }
        return x;
    }

    function hearts(n) {
        return '❤️'.repeat(Math.max(0, n)) || '🖤🖤🖤';
    }

    function showScreen(id) {
        document.querySelectorAll('.pantalla').forEach((p) => p.classList.toggle('activa', p.id === id));
        if (id === 'play') fitSlash();
    }

    function progress(n) {
        els.barra.style.width = `${n}%`;
        els.pill.textContent = n >= 100 ? '2/2' : n >= 50 ? '1/2' : '0/2';
    }

    function hud() {
        els.score.textContent = String(state.score);
        els.lives.textContent = hearts(state.lives);
        els.combo.textContent = `x${state.combo}`;
        if (state.level === 1) {
            els.nivel.innerHTML = "<div class='label'>NIVEL 1 · REQUERIMIENTOS FUNCIONALES</div><div class='value'>Corta solo RF</div>";
            els.arena.classList.remove('n2');
        } else {
            els.nivel.innerHTML = "<div class='label'>NIVEL 2 · REQUERIMIENTOS NO FUNCIONALES</div><div class='value'>Corta solo RNF</div>";
            els.arena.classList.add('n2');
        }
    }

    function toast(text, type) {
        els.toast.hidden = false;
        els.toast.className = `toast ${type}`;
        els.toast.textContent = text;
        toastT = 1.35;
    }

    function fitSlash() {
        const r = els.arena.getBoundingClientRect();
        size = { w: r.width, h: r.height };
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        els.slash.width = size.w * dpr;
        els.slash.height = size.h * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function esCorrecta(tipo, nivel) {
        return nivel === 1 ? tipo === 'FUNCIONAL' : tipo === 'NO_FUNCIONAL';
    }

    function porQueError(tipo) {
        if (tipo === 'NO_FUNCIONAL') {
            return 'Es no funcional: describe calidad o restricción (tiempo, seguridad, disponibilidad), no una función.';
        }
        return 'Es funcional: describe una acción que el sistema debe hacer, no una característica de calidad.';
    }

    function escapeHtml(texto) {
        return String(texto)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function htmlRetro(errores, tituloNivel) {
        if (!errores.length) {
            return `<h3>${tituloNivel}</h3><p>No te equivocaste en este nivel.</p>`;
        }
        const items = errores.map((e) => `
            <li>
                <span class="fruta-txt">${escapeHtml(e.texto)}</span>
                <span class="porque">${escapeHtml(e.porque)}</span>
            </li>
        `).join('');
        return `<h3>${tituloNivel}</h3><ul>${items}</ul>`;
    }

    function pintarRetro(id, html, conErrores) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.toggle('ok', !conErrores);
        el.innerHTML = html;
        el.hidden = false;
    }

    function pick(pool, index) {
        return pool[index % pool.length];
    }

    function deckForLevel(level) {
        const correct = shuffle(level === 1 ? FUNCIONALES : NO_FUNCIONALES);
        const wrong = shuffle(level === 1 ? NO_FUNCIONALES : FUNCIONALES);
        const items = [];
        for (let i = 0; i < TOTAL; i += 1) {
            const fuente = i < OK_COUNT ? pick(correct, i) : pick(wrong, i - OK_COUNT);
            items.push({
                requisitoId: fuente.id,
                text: fuente.texto,
                tipo: fuente.tipo,
                ok: esCorrecta(fuente.tipo, level),
                shape: SHAPES[i % SHAPES.length],
            });
        }
        return shuffle(items);
    }

    function resetRun() {
        Object.assign(state, {
            level: 1, lives: CFG.vidas || 3, score: 0, combo: 0, maxCombo: 0,
            hits: 0, errors: 0, score1: 0, score2: 0, hits1: 0, errors1: 0, missed: 0,
        });
        fruits = [];
        spawned = 0;
        spawnT = 0;
        paused = false;
        cortes = [];
        erroresNivel = [];
        erroresN1 = [];
        erroresN2 = [];
        els.frutas.innerHTML = '';
        hideOverlay();
        progress(0);
    }

    function startLevel(level) {
        mode = 'play';
        paused = false;
        state.level = level;
        state.combo = 0;
        fruits = [];
        spawned = 0;
        spawnT = 0.8;
        deck = deckForLevel(level);
        erroresNivel = [];
        els.frutas.innerHTML = '';
        showScreen('play');
        fitSlash();
        hud();
        progress(level === 1 ? 0 : 50);
        toast(level === 1 ? '¡Corta requerimientos funcionales!' : '¡Ahora corta los no funcionales!', 'ok');
    }

    function spawnFruit(item) {
        const f = {
            ...item,
            x: 90 + Math.random() * Math.max(80, size.w - 180),
            y: size.h + 40,
            vx: (Math.random() - 0.5) * 240,
            vy: -560 - Math.random() * 140,
            rot: Math.random() * 40 - 20,
            vr: (Math.random() - 0.5) * 140,
            sliced: false,
        };
        const el = document.createElement('div');
        el.className = 'fruta';
        el.innerHTML = `<svg class="dibujo"><use href="#${f.shape}"></use></svg>`;
        const etiqueta = document.createElement('span');
        etiqueta.className = 'etiqueta';
        etiqueta.textContent = f.text;
        el.append(etiqueta);
        els.frutas.append(el);
        f.el = el;
        fruits.push(f);
        place(f);
        return f;
    }

    function place(f) {
        f.el.style.transform = `translate(${f.x}px, ${f.y}px) rotate(${f.rot}deg)`;
    }

    function lineHits(x1, y1, x2, y2, cx, cy, r) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const len2 = dx * dx + dy * dy || 1;
        let t = ((cx - x1) * dx + (cy - y1) * dy) / len2;
        t = Math.max(0, Math.min(1, t));
        const px = x1 + t * dx;
        const py = y1 + t * dy;
        return (cx - px) ** 2 + (cy - py) ** 2 <= r * r;
    }

    function sliceFruit(f) {
        if (f.sliced || paused) return;
        f.sliced = true;
        f.el.remove();
        const ok = esCorrecta(f.tipo, state.level);
        cortes.push({ id: f.requisitoId, nivel: state.level });
        const corte = document.createElement('div');
        corte.className = 'corte';
        corte.style.left = `${f.x}px`;
        corte.style.top = `${f.y}px`;
        corte.innerHTML = `
            <div class="tajo"></div>
            <div class="mitad izq"><svg class="dibujo"><use href="#${f.shape}"></use></svg></div>
            <div class="mitad der"><svg class="dibujo"><use href="#${f.shape}"></use></svg></div>
            <div class="xp ${ok ? 'ok' : 'mal'}">${ok ? `+${PTS}` : '×'}</div>
        `;
        const juice = document.createElement('div');
        for (let i = 0; i < 5; i += 1) {
            const g = document.createElement('i');
            g.className = 'gota';
            g.style.left = `${20 + i * 14}%`;
            g.style.top = `${10 + (i % 3) * 16}%`;
            g.style.background = ok ? '#ef4444' : '#facc15';
            juice.append(g);
        }
        corte.append(juice);
        els.frutas.append(corte);
        setTimeout(() => corte.remove(), 750);

        if (ok) {
            state.combo += 1;
            state.maxCombo = Math.max(state.maxCombo, state.combo);
            state.score += PTS;
            state.hits += 1;
            toast('¡Correcto!', 'ok');
            Sfx.ok();
            if (state.combo >= 2) {
                Sfx.combo();
                els.comboPop.hidden = false;
                els.comboPop.textContent = `x${state.combo}`;
                setTimeout(() => { els.comboPop.hidden = true; }, 500);
            }
        } else {
            state.combo = 0;
            state.errors += 1;
            state.lives -= 1;
            erroresNivel.push({ texto: f.text, tipo: f.tipo, porque: porQueError(f.tipo) });
            toast(state.level === 1 ? 'Este requerimiento es NO FUNCIONAL' : 'Este requerimiento es FUNCIONAL', 'bad');
            Sfx.bad();
            if (state.lives <= 0) {
                hud();
                gameOver();
                return;
            }
        }
        hud();
    }

    function hideOverlay() {
        els.overlay.classList.remove('on');
        els.modal.innerHTML = '';
    }

    function openOverlay(html) {
        els.modal.innerHTML = html;
        els.overlay.classList.add('on');
    }

    function finishLevel() {
        paused = true;
        fruits.forEach((f) => f.el.remove());
        fruits = [];
        Sfx.win();
        if (state.level === 1) {
            state.score1 = state.score;
            state.hits1 = state.hits;
            state.errors1 = state.errors;
            mode = 'summary';
            progress(50);
            showScreen('summary-1');
            erroresN1 = erroresNivel.slice();
            document.getElementById('medidas-n1').innerHTML = `
                <div class="medida gold"><span>Puntaje</span><strong>${state.score}</strong></div>
                <div class="medida"><span>Aciertos</span><strong>${state.hits}</strong></div>
                <div class="medida"><span>Errores</span><strong>${state.errors}</strong></div>
                <div class="medida"><span>Combo máximo</span><strong>x${state.maxCombo}</strong></div>
                <div class="medida"><span>Vidas restantes</span><strong>${state.lives}</strong></div>
                <div class="medida"><span>No cortados</span><strong>${state.missed}</strong></div>
            `;
            pintarRetro('retro-n1', htmlRetro(erroresN1, 'En qué te equivocaste'), erroresN1.length > 0);
        } else {
            state.score2 = state.score - state.score1;
            guardarYMostrarFinal();
        }
    }

    function mostrarFinal(puntaje) {
        mode = 'final';
        paused = true;
        progress(100);
        showScreen('final');
        const total = puntaje == null ? state.score : puntaje;
        document.getElementById('medidas-final').innerHTML = `
            <div class="medida"><span>Puntuación Nivel 1</span><strong>${state.score1}</strong></div>
            <div class="medida"><span>Puntuación Nivel 2</span><strong>${state.score2}</strong></div>
            <div class="medida gold"><span>Puntuación total</span><strong>${total}</strong></div>
            <div class="medida"><span>Aciertos totales</span><strong>${state.hits}</strong></div>
            <div class="medida"><span>Errores totales</span><strong>${state.errors}</strong></div>
            <div class="medida"><span>Combo máximo</span><strong>x${state.maxCombo}</strong></div>
        `;
        erroresN2 = erroresNivel.slice();
        pintarRetro(
            'retro-final',
            htmlRetro(erroresN1, 'Nivel 1 · en qué te equivocaste')
            + htmlRetro(erroresN2, 'Nivel 2 · en qué te equivocaste'),
            erroresN1.length + erroresN2.length > 0,
        );
    }

    function guardarYMostrarFinal() {
        if (guardando) return;
        guardando = true;
        fetch(URLS.guardar, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': URLS.csrf },
            body: JSON.stringify({
                cortes,
                niveles_completados: 2,
            }),
        }).then((r) => r.json()).then((data) => {
            guardando = false;
            mostrarFinal(data.puntaje != null ? data.puntaje : state.score);
        }).catch(() => {
            guardando = false;
            mostrarFinal(state.score);
        });
    }

    function gameOver() {
        mode = 'gameover';
        paused = true;
        fruits.forEach((f) => f.el && f.el.remove());
        fruits = [];
        Sfx.lose();
        showScreen('gameover');
        document.getElementById('medidas-go').innerHTML = `
            <div class="medida"><span>Nivel alcanzado</span><strong>${state.level}</strong></div>
            <div class="medida gold"><span>Puntuación</span><strong>${state.score}</strong></div>
            <div class="medida"><span>Aciertos</span><strong>${state.hits}</strong></div>
            <div class="medida"><span>Errores</span><strong>${state.errors}</strong></div>
        `;
        const n2 = state.level === 2 ? erroresNivel : [];
        const n1 = state.level === 1 ? erroresNivel : erroresN1;
        pintarRetro(
            'retro-go',
            htmlRetro(n1, 'Nivel 1 · en qué te equivocaste')
            + (state.level === 2 ? htmlRetro(n2, 'Nivel 2 · en qué te equivocaste') : ''),
            n1.length + n2.length > 0,
        );
    }

    function goTemario() {
        paused = true;
        fruits.forEach((f) => f.el && f.el.remove());
        fruits = [];
        window.location.href = URLS.temario;
    }

    function askExit() {
        if (mode !== 'play') {
            goTemario();
            return;
        }
        paused = true;
        openOverlay(`
            <h2>¿Deseas volver al temario?</h2>
            <p>Si sales ahora, el progreso de esta partida no se conservará.</p>
            <div class="acciones">
                <button class="btn" id="stay" type="button">Seguir jugando</button>
                <button class="btn ghost" id="leave" type="button">Volver al temario</button>
            </div>
        `);
        document.getElementById('stay').onclick = () => {
            hideOverlay();
            paused = false;
        };
        document.getElementById('leave').onclick = goTemario;
    }

    function update(dt) {
        spawnT -= dt;
        if (spawnT <= 0 && spawned < TOTAL) {
            spawnFruit(deck[spawned]);
            spawned += 1;
            spawnT = 1.55 + Math.random() * 0.55;
        }
        for (const f of fruits) {
            if (f.sliced) continue;
            f.vy += GRAVITY * dt;
            f.x += f.vx * dt;
            f.y += f.vy * dt;
            f.rot += f.vr * dt;
            if (f.x < 70) { f.x = 70; f.vx = Math.abs(f.vx); }
            if (f.x > size.w - 70) { f.x = size.w - 70; f.vx = -Math.abs(f.vx); }
            place(f);
        }
        const gone = [];
        for (const f of fruits) {
            if (f.sliced) { gone.push(f); continue; }
            if (f.y > size.h + 90 && f.vy > 0) {
                if (esCorrecta(f.tipo, state.level)) {
                    state.missed += 1;
                    toast('Requerimiento correcto no cortado', 'info');
                }
                f.el.remove();
                gone.push(f);
            }
        }
        fruits = fruits.filter((f) => !gone.includes(f));
        if (spawned >= TOTAL && fruits.length === 0 && !paused && mode === 'play') finishLevel();
        if (toastT > 0) {
            toastT -= dt;
            if (toastT <= 0) els.toast.hidden = true;
        }
        drawTrail(dt);
    }

    function drawTrail(dt) {
        ctx.clearRect(0, 0, size.w, size.h);
        trail = trail.filter((p) => {
            p.life -= dt * 3.2;
            return p.life > 0;
        });
        if (trail.length < 2) return;
        ctx.strokeStyle = '#fff';
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        ctx.moveTo(trail[0].x, trail[0].y);
        for (let i = 1; i < trail.length; i += 1) ctx.lineTo(trail[i].x, trail[i].y);
        ctx.lineWidth = 7;
        ctx.shadowColor = '#5B5BF0';
        ctx.shadowBlur = 12;
        ctx.globalAlpha = 0.9;
        ctx.stroke();
        ctx.globalAlpha = 1;
        ctx.shadowBlur = 0;
    }

    function arenaPoint(e) {
        const r = els.arena.getBoundingClientRect();
        return { x: e.clientX - r.left, y: e.clientY - r.top };
    }

    function trySliceAt(x1, y1, x2, y2) {
        for (const f of fruits) {
            if (!f.sliced && lineHits(x1, y1, x2, y2, f.x, f.y, 58)) sliceFruit(f);
        }
    }

    function tryClick(x, y) {
        for (const f of fruits) {
            if (f.sliced) continue;
            const dx = x - f.x;
            const dy = y - f.y;
            if (dx * dx + dy * dy < 70 * 70) sliceFruit(f);
        }
    }

    function loop(ts) {
        requestAnimationFrame(loop);
        const dt = Math.min(0.033, (ts - lastTs) / 1000 || 0.016);
        lastTs = ts;
        if (mode === 'play' && !paused) update(dt);
        else {
            ctx.clearRect(0, 0, size.w, size.h);
            if (toastT > 0) {
                toastT -= dt;
                if (toastT <= 0) els.toast.hidden = true;
            }
        }
    }

    els.arena.addEventListener('pointerdown', (e) => {
        if (mode !== 'play' || paused) return;
        slicing = true;
        const p = arenaPoint(e);
        trail = [{ x: p.x, y: p.y, life: 1 }];
        tryClick(p.x, p.y);
        els.arena.setPointerCapture(e.pointerId);
    });
    els.arena.addEventListener('pointermove', (e) => {
        if (!slicing || paused) return;
        const p = arenaPoint(e);
        const prev = trail[trail.length - 1];
        trail.push({ x: p.x, y: p.y, life: 1 });
        if (prev) trySliceAt(prev.x, prev.y, p.x, p.y);
    });
    window.addEventListener('pointerup', () => { slicing = false; });

    document.getElementById('btn-n1').onclick = () => { resetRun(); startLevel(1); };
    document.getElementById('btn-n2').onclick = () => startLevel(2);
    document.getElementById('btn-a-n2').onclick = () => {
        mode = 'intro';
        showScreen('intro-2');
        progress(50);
    };
    document.getElementById('btn-retry').onclick = () => {
        resetRun();
        showScreen('intro-1');
    };
    document.getElementById('btn-salir').onclick = askExit;
    document.getElementById('btn-sonido').onclick = () => {
        Sfx.on = !Sfx.on;
        els.sonido.textContent = Sfx.on ? '🔊' : '🔇';
        if (Sfx.ac && Sfx.ac.state === 'suspended') Sfx.ac.resume();
    };
    window.addEventListener('resize', () => { if (mode === 'play') fitSlash(); });
    requestAnimationFrame(loop);
})();
