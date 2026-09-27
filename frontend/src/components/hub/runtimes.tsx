import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { JSX, ReactNode } from 'react';
import { cn } from '../../utils/cn';
import Icon from '../Icon';
import { sfx } from './audio';

// ---------------------------------------------------------------------------
// Genre runtimes — each play_kind is a distinct mechanic (calculate, pattern,
// timing, dodge, order, match, build, collect). Every engine is fully
// client-side gameplay; the backend only stores the bounds-checked,
// server-computed result of a finished run.
// ---------------------------------------------------------------------------

export interface EngineOutcome {
    score: number;
    accuracy: number;
    mistakes: number;
    bestCombo: number;
    /** 0–100: how much of the stage the player got through. */
    completion: number;
}

export interface EngineProps {
    round: number;
    difficulty: number;
    timeLimitMs: number;
    seed: number;
    paused: boolean;
    onEnd: (outcome: EngineOutcome) => void;
    onCombo?: (combo: number) => void;
}

export type PlayKind =
    | 'quanta-calc'
    | 'logix-seq'
    | 'pulse-timing'
    | 'vector-dodge'
    | 'cipher-sort'
    | 'synapse-match'
    | 'forge-order'
    | 'orbit-gather';

export const PLAY_KIND_TIME_LIMIT: Record<PlayKind, number> = {
    'quanta-calc': 24000,
    'logix-seq': 20000,
    'pulse-timing': 12000,
    'vector-dodge': 12000,
    'cipher-sort': 26000,
    'synapse-match': 30000,
    'forge-order': 24000,
    'orbit-gather': 16000,
};

export const PLAY_KIND_ICONS: Record<string, string> = {
    'quanta-calc': 'bolt',
    'logix-seq': 'puzzle',
    'pulse-timing': 'timer',
    'vector-dodge': 'arrow',
    'cipher-sort': 'layers',
    'synapse-match': 'grid',
    'forge-order': 'list',
    'orbit-gather': 'compass',
};

export function playKindFor(kind: string): PlayKind {
    return (PLAY_KIND_TIME_LIMIT as Record<string, number>)[kind] ? (kind as PlayKind) : 'logix-seq';
}

// --- deterministic helpers -------------------------------------------------

function mulberry32(seed: number) {
    let a = seed >>> 0;
    return () => {
        a = (a + 0x6d2b79f5) | 0;
        let t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

export function seedFor(slug: string, round: number): number {
    let h = 2166136261;
    for (let i = 0; i < slug.length; i++) {
        h ^= slug.charCodeAt(i);
        h = Math.imul(h, 16777619);
    }
    return (h + round * 2654435761) >>> 0;
}

function randInt(rng: () => number, min: number, max: number): number {
    return min + Math.floor(rng() * (max - min + 1));
}

function shuffle<T>(arr: readonly T[], rng: () => number): T[] {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(rng() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

const pct = (part: number, whole: number) => (whole > 0 ? Math.round((part / whole) * 100) : 0);

// --- shared hooks -----------------------------------------------------------

/** Pause-aware countdown. `onZero` fires exactly once. */
function useCountdown(ms: number, paused: boolean, onZero: () => void) {
    const [left, setLeft] = useState(ms);
    const pausedRef = useRef(paused);
    pausedRef.current = paused;
    const onZeroRef = useRef(onZero);
    onZeroRef.current = onZero;
    const fired = useRef(false);

    useEffect(() => {
        const id = window.setInterval(() => {
            if (pausedRef.current) return;
            setLeft((v) => Math.max(0, v - 100));
        }, 100);
        return () => window.clearInterval(id);
    }, []);

    useEffect(() => {
        if (left <= 0 && !fired.current) {
            fired.current = true;
            onZeroRef.current();
        }
    }, [left]);
    return left;
}

/** Streak tracking shared by every engine so combos feel the same everywhere. */
function useCombo(onCombo?: (combo: number) => void) {
    const [combo, setCombo] = useState(0);
    const comboRef = useRef(0);
    const bestRef = useRef(0);
    const mistakesRef = useRef(0);
    const hit = useCallback(() => {
        comboRef.current += 1;
        bestRef.current = Math.max(bestRef.current, comboRef.current);
        setCombo(comboRef.current);
        onCombo?.(comboRef.current);
        sfx(comboRef.current >= 3 ? 'combo' : 'hit');
    }, [onCombo]);
    const miss = useCallback(() => {
        comboRef.current = 0;
        mistakesRef.current += 1;
        setCombo(0);
        onCombo?.(0);
        sfx('miss');
    }, [onCombo]);
    return { combo, hit, miss, best: bestRef, mistakes: mistakesRef, comboRef };
}

/** Guarantees `onEnd` fires once per engine instance. */
function useFinisher(onEnd: (o: EngineOutcome) => void) {
    const done = useRef(false);
    const [ended, setEnded] = useState(false);
    const finish = useCallback(
        (o: EngineOutcome) => {
            if (done.current) return;
            done.current = true;
            setEnded(true);
            onEnd({
                score: Math.max(0, Math.round(o.score)),
                accuracy: Math.max(0, Math.min(100, Math.round(o.accuracy))),
                mistakes: Math.max(0, o.mistakes),
                bestCombo: Math.max(0, o.bestCombo),
                completion: Math.max(0, Math.min(100, Math.round(o.completion))),
            });
        },
        [onEnd]
    );
    return { finish, ended, doneRef: done };
}

function RoundShell({
    left,
    timeLimitMs,
    label,
    combo,
    children,
}: {
    left: number;
    timeLimitMs: number;
    label: string;
    combo: number;
    children: ReactNode;
}) {
    const width = Math.max(0, Math.min(100, (left / timeLimitMs) * 100));
    const color = width > 50 ? '' : width > 25 ? ' vs-game__bar--warn' : ' vs-game__bar--danger';
    return (
        <div className="vs-game">
            <div className="vs-game__barwrap">
                <span className={cn('vs-game__bar', color)} style={{ width: `${width}%` }} />
            </div>
            <div className="vs-game__meta">
                <b>{label}</b>
                {combo >= 2 && <span className="vs-game__combo">{`x${combo} combo`}</span>}
                <span>{Math.ceil(left / 1000)}s</span>
            </div>
            {children}
        </div>
    );
}

// --- 1. QUANTA: speed arithmetic ---------------------------------------------

function QuantaCalc({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const total = 4 + difficulty;
    const tasks = useMemo(() => {
        const rng = mulberry32(seed);
        const list: Array<{ text: string; answer: number }> = [];
        const d = Math.max(1, difficulty);
        for (let i = 0; i < total; i++) {
            const op = rng();
            let a = randInt(rng, 1 + d, 6 + d * 4);
            let b = randInt(rng, 1, 2 + d * 2);
            if (op < 0.25 || d <= 1) {
                list.push({ text: `${a} + ${b}`, answer: a + b });
            } else if (op < 0.5) {
                const big = Math.max(a, b);
                const small = Math.min(a, b);
                list.push({ text: `${big} − ${small}`, answer: big - small });
            } else if (op < 0.75) {
                b = randInt(rng, 2, 2 + d);
                list.push({ text: `${a} × ${b}`, answer: a * b });
            } else {
                const mult = randInt(rng, 2, 2 + d);
                a = mult * randInt(rng, 2, 2 + d * 2);
                list.push({ text: `${a} ÷ ${mult}`, answer: a / mult });
            }
        }
        return list;
    }, [seed, difficulty, total]);

    const { finish, ended } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [idx, setIdx] = useState(0);
    const [value, setValue] = useState('');
    const [correct, setCorrect] = useState(0);
    const [score, setScore] = useState(0);
    const [flash, setFlash] = useState<'' | 'ok' | 'no'>('');

    const end = (answered: number, ok: number, sc: number) =>
        finish({
            score: sc,
            accuracy: pct(ok, answered),
            mistakes: c.mistakes.current,
            bestCombo: c.best.current,
            completion: pct(answered, total),
        });

    const left = useCountdown(timeLimitMs, paused, () => end(idx, correct, score));
    if (ended) return null;

    function submit() {
        if (paused || flash) return;
        const num = parseInt(value, 10);
        if (value.trim() === '' || Number.isNaN(num)) return;
        const isOk = num === tasks[idx].answer;
        if (isOk) c.hit();
        else c.miss();
        const bonus = isOk ? 10 * difficulty + Math.min(c.comboRef.current, 5) * 2 : 0;
        const newScore = score + bonus;
        const newCorrect = correct + (isOk ? 1 : 0);
        setCorrect(newCorrect);
        setScore(newScore);
        setFlash(isOk ? 'ok' : 'no');
        window.setTimeout(() => {
            if (idx + 1 >= total) end(total, newCorrect, newScore);
            else {
                setIdx(idx + 1);
                setValue('');
                setFlash('');
            }
        }, 260);
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} combo={c.combo} label={`Task ${idx + 1} of ${total}`}>
            <div className="vs-game__quanta">
                <span className="vs-game__quantaq">{tasks[idx].text}</span>
                <span className="vs-game__quantaop">= ?</span>
                <input
                    className="vs-game__quantainput"
                    value={value}
                    onChange={(e) => setValue(e.target.value.replace(/[^0-9-]/g, ''))}
                    placeholder="Answer"
                    aria-label="Your answer"
                    autoFocus
                    inputMode="numeric"
                    disabled={paused}
                    onKeyDown={(e) => {
                        if (e.key !== 'Enter' || e.nativeEvent.isComposing || e.keyCode === 229) return;
                        submit();
                    }}
                />
                <button className="vs-btn vs-btn--solid vs-btn--lg" onClick={submit} disabled={paused}>
                    Lock it in
                </button>
                {flash && (
                    <span className={cn('vs-game__flash', flash === 'ok' ? 'vs-game__flash--ok' : 'vs-game__flash--no')}>
                        {flash === 'ok' ? 'Correct' : `Answer: ${tasks[idx].answer}`}
                    </span>
                )}
            </div>
        </RoundShell>
    );
}

// --- 2. LOGIX: next-in-pattern ------------------------------------------------

function LogixSeq({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const total = 5;
    const questions = useMemo(() => {
        const rng = mulberry32(seed);
        const d = Math.max(1, difficulty);
        const list: Array<{ terms: number[]; choices: number[]; answerIdx: number }> = [];
        for (let q = 0; q < total; q++) {
            const style = rng();
            const terms = [0, 0, 0, 0, 0];
            if (style < 0.4) {
                const step = randInt(rng, 1, d + 2);
                const start = randInt(rng, 1, 5);
                for (let i = 0; i < 5; i++) terms[i] = start + i * step;
            } else if (style < 0.7) {
                const mult = randInt(rng, 2, Math.min(d + 1, 4));
                const start = randInt(rng, 1, 3);
                for (let i = 0; i < 5; i++) terms[i] = start * Math.pow(mult, i);
            } else {
                // Alternating: two interleaved arithmetic sequences.
                const stepA = randInt(rng, 1, d + 2);
                const stepB = randInt(rng, 2, d + 4);
                const startA = randInt(rng, 1, 6);
                const startB = randInt(rng, 10, 20);
                for (let i = 0; i < 5; i++) {
                    terms[i] = i % 2 === 0 ? startA + (i / 2) * stepA : startB + ((i - 1) / 2) * stepB;
                }
            }
            const answer = terms[4];
            const wrong = new Set<number>();
            let guard = 0;
            while (wrong.size < 3 && guard++ < 50) {
                const candidate = answer + randInt(rng, 1, 4) * (rng() < 0.5 ? -1 : 1);
                if (candidate !== answer && candidate >= 0) wrong.add(candidate);
            }
            const choices = shuffle([...wrong, answer], rng);
            list.push({ terms, choices, answerIdx: choices.indexOf(answer) });
        }
        return list;
    }, [seed, difficulty]);

    const { finish, ended } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [idx, setIdx] = useState(0);
    const [correct, setCorrect] = useState(0);
    const [score, setScore] = useState(0);
    const [locked, setLocked] = useState<number | null>(null);

    const end = (answered: number, ok: number, sc: number) =>
        finish({
            score: sc,
            accuracy: pct(ok, answered),
            mistakes: c.mistakes.current,
            bestCombo: c.best.current,
            completion: pct(answered, total),
        });
    const left = useCountdown(timeLimitMs, paused, () => end(idx, correct, score));
    if (ended) return null;

    const q = questions[idx];
    function pick(i: number) {
        if (paused || locked !== null) return;
        setLocked(i);
        const isOk = i === q.answerIdx;
        if (isOk) c.hit();
        else c.miss();
        const newScore = score + (isOk ? 10 * difficulty + Math.min(c.comboRef.current, 5) * 2 : 0);
        const newCorrect = correct + (isOk ? 1 : 0);
        setScore(newScore);
        setCorrect(newCorrect);
        window.setTimeout(() => {
            if (idx + 1 >= total) end(total, newCorrect, newScore);
            else {
                setIdx(idx + 1);
                setLocked(null);
            }
        }, 420);
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} combo={c.combo} label={`Pattern ${idx + 1} of ${total}`}>
            <div className="vs-game__logix">
                <span className="vs-game__logixlabel">What comes next?</span>
                <div className="vs-game__logixterms">
                    {q.terms.slice(0, 4).map((t, i) => (
                        <span key={i} className="vs-game__logixterm">{t}</span>
                    ))}
                    <span className="vs-game__logixq">?</span>
                </div>
                <div className="vs-game__logixopts">
                    {q.choices.map((choice, i) => (
                        <button
                            key={i}
                            className={cn(
                                'vs-game__logixopt',
                                locked !== null && i === q.answerIdx && 'vs-game__logixopt--ok',
                                locked === i && i !== q.answerIdx && 'vs-game__logixopt--no'
                            )}
                            onClick={() => pick(i)}
                            disabled={paused}
                        >
                            {choice}
                        </button>
                    ))}
                </div>
            </div>
        </RoundShell>
    );
}

// --- 3. PULSE: reaction timing --------------------------------------------------

function PulseTiming({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const attempts = 5;
    const targets = useMemo(() => {
        const rng = mulberry32(seed);
        return Array.from({ length: attempts }, () => randInt(rng, 15, 85));
    }, [seed]);
    const zoneWidth = Math.max(6, 14 - difficulty * 1.5);
    const speed = 45 + difficulty * 14; // % of rail per second

    const { finish, ended, doneRef } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [tries, setTries] = useState(0);
    const [score, setScore] = useState(0);
    const [hits, setHits] = useState(0);
    const [last, setLast] = useState<{ off: number; grade: 'perfect' | 'good' | 'miss' } | null>(null);
    const markerRef = useRef<HTMLSpanElement>(null);
    const posRef = useRef(0);
    const dirRef = useRef(1);
    const pausedRef = useRef(paused);
    pausedRef.current = paused;

    useEffect(() => {
        let raf = 0;
        let prev = performance.now();
        const tick = (now: number) => {
            const dt = (now - prev) / 1000;
            prev = now;
            if (!pausedRef.current) {
                let next = posRef.current + dirRef.current * speed * dt;
                if (next >= 100) {
                    next = 100;
                    dirRef.current = -1;
                } else if (next <= 0) {
                    next = 0;
                    dirRef.current = 1;
                }
                posRef.current = next;
                if (markerRef.current) markerRef.current.style.left = `${next}%`;
            }
            raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(raf);
    }, [speed]);

    const end = (sc: number, h: number, t: number) =>
        finish({
            score: sc,
            accuracy: pct(h, Math.max(1, t)),
            mistakes: c.mistakes.current,
            bestCombo: c.best.current,
            completion: pct(t, attempts),
        });

    const left = useCountdown(timeLimitMs, paused, () => end(score, hits, tries));

    const tapRef = useRef<() => void>(() => undefined);
    tapRef.current = () => {
        if (doneRef.current || pausedRef.current || tries >= attempts) return;
        const target = targets[tries];
        const off = Math.abs(posRef.current - target);
        const half = zoneWidth / 2;
        const grade = off <= half * 0.4 ? 'perfect' : off <= half ? 'good' : 'miss';
        const gained = grade === 'perfect' ? 15 * difficulty : grade === 'good' ? 8 * difficulty : 0;
        if (grade === 'miss') c.miss();
        else c.hit();
        const newScore = score + gained + (grade !== 'miss' ? Math.min(c.comboRef.current, 5) * 2 : 0);
        const newHits = hits + (grade !== 'miss' ? 1 : 0);
        const newTries = tries + 1;
        setScore(newScore);
        setHits(newHits);
        setTries(newTries);
        setLast({ off, grade });
        if (newTries >= attempts) window.setTimeout(() => end(newScore, newHits, newTries), 400);
    };

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.code === 'Space' || e.key === ' ') {
                e.preventDefault();
                tapRef.current();
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, []);

    if (ended) return null;
    const target = targets[Math.min(tries, attempts - 1)];

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} combo={c.combo} label={`Pulse ${Math.min(tries + 1, attempts)} of ${attempts}`}>
            <div className="vs-game__pulse">
                <span className="vs-game__pulselabel">Press Space or tap Fire when the marker is inside the zone</span>
                <div className="vs-game__pulserail">
                    <span
                        className="vs-game__pulsezone"
                        style={{ left: `${target}%`, width: `${zoneWidth}%` }}
                    />
                    <span ref={markerRef} className="vs-game__pulsemarker" style={{ left: '0%' }} />
                </div>
                <button className="vs-btn vs-btn--solid vs-btn--lg" onClick={() => tapRef.current()} disabled={paused}>
                    Fire
                </button>
                {last && (
                    <span className={cn('vs-game__pulsefback', last.grade !== 'miss' ? 'vs-game__pulsefback--ok' : 'vs-game__pulsefback--no')}>
                        {last.grade === 'perfect' ? 'Perfect' : last.grade === 'good' ? 'Good' : 'Missed'}
                        {` · ${Math.round(last.off)} off`}
                    </span>
                )}
            </div>
        </RoundShell>
    );
}

// --- 4. VECTOR: lane dodge -------------------------------------------------------

const LANES = 5;
const ROWS = 6;

function VectorDodge({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const lives = 3;
    const { finish, ended, doneRef } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [playerCol, setPlayerCol] = useState(2);
    const playerRef = useRef(2);
    const [obstacles, setObstacles] = useState<Array<{ id: number; col: number; row: number }>>([]);
    const [hits, setHits] = useState(0);
    const [dodges, setDodges] = useState(0);
    const [shake, setShake] = useState(false);
    const hitsRef = useRef(0);
    const dodgesRef = useRef(0);
    const pausedRef = useRef(paused);
    pausedRef.current = paused;

    const end = useCallback(
        (survived: boolean) => {
            const d = dodgesRef.current;
            const h = hitsRef.current;
            finish({
                score: d * 6 * difficulty + (survived ? 40 * difficulty : 0),
                accuracy: d + h ? pct(d, d + h) : 100,
                mistakes: h,
                bestCombo: c.best.current,
                completion: survived ? 100 : 0,
            });
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [finish, difficulty]
    );

    const move = useCallback((delta: number) => {
        if (pausedRef.current) return;
        const next = Math.max(0, Math.min(LANES - 1, playerRef.current + delta));
        playerRef.current = next;
        setPlayerCol(next);
    }, []);

    useEffect(() => {
        const rng = mulberry32(seed);
        let nextId = 0;
        const spawnEvery = Math.max(260, 520 - difficulty * 50);
        const stepEvery = Math.max(120, 240 - difficulty * 20);
        const spawn = window.setInterval(() => {
            if (pausedRef.current || doneRef.current) return;
            setObstacles((prev) => {
                const col = randInt(rng, 0, LANES - 1);
                return [...prev, { id: nextId++, col, row: 0 }];
            });
        }, spawnEvery);
        const step = window.setInterval(() => {
            if (pausedRef.current || doneRef.current) return;
            setObstacles((prev) => {
                const kept: typeof prev = [];
                for (const o of prev) {
                    const row = o.row + 1;
                    if (row === ROWS - 1) {
                        if (o.col === playerRef.current) {
                            hitsRef.current += 1;
                            setHits(hitsRef.current);
                            setShake(true);
                            window.setTimeout(() => setShake(false), 160);
                            c.miss();
                            if (hitsRef.current >= lives) window.setTimeout(() => end(false), 0);
                            continue;
                        }
                    }
                    if (row >= ROWS) {
                        dodgesRef.current += 1;
                        setDodges(dodgesRef.current);
                        if (dodgesRef.current % 5 === 0) c.hit();
                        continue;
                    }
                    kept.push({ ...o, row });
                }
                return kept;
            });
        }, stepEvery);
        const keys = (e: KeyboardEvent) => {
            if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
                e.preventDefault();
                move(-1);
            }
            if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
                e.preventDefault();
                move(1);
            }
        };
        window.addEventListener('keydown', keys);
        return () => {
            window.clearInterval(spawn);
            window.clearInterval(step);
            window.removeEventListener('keydown', keys);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [seed, difficulty]);

    const left = useCountdown(timeLimitMs, paused, () => end(true));
    if (ended) return null;

    const grid: ReactNode[] = [];
    for (let row = 0; row < ROWS; row++) {
        for (let col = 0; col < LANES; col++) {
            const obstacle = obstacles.some((o) => o.col === col && o.row === row);
            const isPlayer = row === ROWS - 1 && col === playerCol;
            grid.push(
                <div
                    key={`${row}-${col}`}
                    className={cn(
                        'vs-game__dodgecell',
                        obstacle && 'vs-game__dodgecell--block',
                        isPlayer && 'vs-game__dodgecell--player'
                    )}
                />
            );
        }
    }

    return (
        <RoundShell
            left={left}
            timeLimitMs={timeLimitMs}
            combo={c.combo}
            label={`Dodged ${dodges} · shields ${Math.max(0, lives - hits)}/${lives}`}
        >
            <div className="vs-game__dodge">
                <div
                    className={cn('vs-game__dodgegrid', shake && 'vs-game__dodgegrid--shake')}
                    style={{ gridTemplateColumns: `repeat(${LANES}, 1fr)` }}
                >
                    {grid}
                </div>
                <div className="vs-game__dodgekeys">
                    <button className="vs-btn vs-btn--outline vs-btn--sm" onClick={() => move(-1)} aria-label="Move left" disabled={paused}>
                        <Icon name="chevron-left" size={16} />
                    </button>
                    <span>{'← → or A / D to switch lanes · survive the timer'}</span>
                    <button className="vs-btn vs-btn--outline vs-btn--sm" onClick={() => move(1)} aria-label="Move right" disabled={paused}>
                        <Icon name="chevron-right" size={16} />
                    </button>
                </div>
            </div>
        </RoundShell>
    );
}

// --- 5. CIPHER: reorder tiles -----------------------------------------------------

function CipherSort({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const total = 4;
    const size = difficulty >= 4 ? 5 : 4;
    const tasks = useMemo(() => {
        const rng = mulberry32(seed);
        const d = Math.max(1, difficulty);
        const list: Array<{ values: number[]; par: number }> = [];
        for (let i = 0; i < total; i++) {
            const base = randInt(rng, 1, 10 + d * 3);
            const step = randInt(rng, 1, d + 2);
            const sorted = Array.from({ length: size }, (_, k) => base + k * step);
            let values = shuffle(sorted, rng);
            if (values.join(',') === sorted.join(',')) values = [...values.slice(1), values[0]];
            // Minimum swaps needed = n - cycles.
            const seen = new Array(size).fill(false);
            let cycles = 0;
            for (let k = 0; k < size; k++) {
                if (seen[k]) continue;
                cycles++;
                let j = k;
                while (!seen[j]) {
                    seen[j] = true;
                    j = sorted.indexOf(values[j]);
                }
            }
            list.push({ values, par: size - cycles });
        }
        return list;
    }, [seed, difficulty, size]);

    const { finish, ended } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [idx, setIdx] = useState(0);
    const [order, setOrder] = useState<number[]>(() => tasks[0].values);
    const [solved, setSolved] = useState(0);
    const [score, setScore] = useState(0);
    const [moves, setMoves] = useState(0);
    const [extraMoves, setExtraMoves] = useState(0);
    const [picked, setPicked] = useState<number | null>(null);
    const [clear, setClear] = useState(false);

    const end = (done: number, sc: number, extra: number) =>
        finish({
            score: sc,
            accuracy: done ? Math.max(0, 100 - extra * 8) : 0,
            mistakes: extra,
            bestCombo: c.best.current,
            completion: pct(done, total),
        });
    const left = useCountdown(timeLimitMs, paused, () => end(solved, score, extraMoves));
    if (ended) return null;

    const current = tasks[idx];
    function choose(j: number) {
        if (paused || clear) return;
        if (picked === null) {
            setPicked(j);
            return;
        }
        if (picked === j) {
            setPicked(null);
            return;
        }
        const nextOrder = order.slice();
        [nextOrder[picked], nextOrder[j]] = [nextOrder[j], nextOrder[picked]];
        const newMoves = moves + 1;
        setOrder(nextOrder);
        setMoves(newMoves);
        setPicked(null);
        const sortedNow = nextOrder.every((v, k) => k === 0 || nextOrder[k - 1] <= v);
        if (!sortedNow) return;
        const extra = Math.max(0, newMoves - current.par);
        if (extra === 0) c.hit();
        else c.miss();
        const newScore = score + 10 * difficulty + (extra === 0 ? 5 * difficulty : 0);
        const newSolved = solved + 1;
        const newExtra = extraMoves + extra;
        setScore(newScore);
        setSolved(newSolved);
        setExtraMoves(newExtra);
        setClear(true);
        window.setTimeout(() => {
            if (idx + 1 >= total) end(newSolved, newScore, newExtra);
            else {
                setIdx(idx + 1);
                setOrder(tasks[idx + 1].values);
                setMoves(0);
                setClear(false);
            }
        }, 420);
    }

    return (
        <RoundShell
            left={left}
            timeLimitMs={timeLimitMs}
            combo={c.combo}
            label={`Grid ${idx + 1} of ${total} · ${moves}/${current.par} swaps`}
        >
            <div className="vs-game__cipher">
                <span className="vs-game__cipherlabel">Tap two tiles to swap them into ascending order — match par for a bonus</span>
                <div className={cn('vs-game__ciphertiles', clear && 'vs-game__ciphertiles--clear')}>
                    {order.map((v, i) => (
                        <button
                            key={`${idx}-${i}`}
                            className={cn('vs-game__ciphertile', picked === i && 'vs-game__ciphertile--picked')}
                            onClick={() => choose(i)}
                            aria-pressed={picked === i}
                            disabled={paused}
                        >
                            {String(v).padStart(2, '0')}
                        </button>
                    ))}
                </div>
                {moves > 0 && !clear && (
                    <button
                        className="vs-btn vs-btn--ghost vs-btn--sm"
                        onClick={() => {
                            setOrder(current.values);
                            setMoves(0);
                            setPicked(null);
                        }}
                    >
                        Reset grid
                    </button>
                )}
            </div>
        </RoundShell>
    );
}

// --- 6. SYNAPSE: card match ---------------------------------------------------------

const SYNAPSE_SYMBOLS = ['◆', '●', '▲', '★', '■', '✚'];

function SynapseMatch({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const pairs = difficulty >= 4 ? 6 : 4;
    const deck = useMemo(() => {
        const rng = mulberry32(seed);
        const symbols = SYNAPSE_SYMBOLS.slice(0, pairs);
        return shuffle(symbols.concat(symbols), rng);
    }, [seed, pairs]);

    const { finish, ended } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [open, setOpen] = useState<number[]>([]);
    const [matched, setMatched] = useState<Set<number>>(() => new Set());
    const [moves, setMoves] = useState(0);
    const [peeked, setPeeked] = useState(false);
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        const id = window.setTimeout(() => setPeeked(true), Math.max(900, 1800 - difficulty * 150));
        return () => window.clearTimeout(id);
    }, [difficulty]);

    const accuracyFor = (m: number, found: number) => (found ? Math.max(0, 100 - Math.max(0, m - found) * 10) : 0);

    const left = useCountdown(timeLimitMs, paused, () =>
        finish({
            score: (matched.size / 2) * 10 * difficulty,
            accuracy: accuracyFor(moves, matched.size / 2),
            mistakes: c.mistakes.current,
            bestCombo: c.best.current,
            completion: pct(matched.size / 2, pairs),
        })
    );
    if (ended) return null;

    function flip(i: number) {
        if (!peeked || paused || busy || matched.has(i) || open.includes(i)) return;
        const nextOpen = [...open, i];
        setOpen(nextOpen);
        if (nextOpen.length < 2) return;
        const [a, b] = nextOpen;
        const newMoves = moves + 1;
        setMoves(newMoves);
        if (deck[a] === deck[b]) {
            c.hit();
            const nextMatched = new Set([...matched, a, b]);
            setMatched(nextMatched);
            setOpen([]);
            if (nextMatched.size === deck.length) {
                const found = pairs;
                window.setTimeout(
                    () =>
                        finish({
                            score: found * 10 * difficulty + Math.round((left / 1000) * difficulty),
                            accuracy: accuracyFor(newMoves, found),
                            mistakes: c.mistakes.current,
                            bestCombo: c.best.current,
                            completion: 100,
                        }),
                    400
                );
            }
        } else {
            c.miss();
            setBusy(true);
            window.setTimeout(() => {
                setOpen([]);
                setBusy(false);
            }, 650);
        }
    }

    return (
        <RoundShell
            left={left}
            timeLimitMs={timeLimitMs}
            combo={c.combo}
            label={`${matched.size / 2}/${pairs} pairs · ${moves} moves`}
        >
            <div className="vs-game__synapse">
                <span className="vs-game__synapselabel">{peeked ? 'Flip two cards to match the symbols' : 'Memorize the symbols…'}</span>
                <div className={cn('vs-game__synapsegrid', pairs > 4 && 'vs-game__synapsegrid--wide')}>
                    {deck.map((sym, i) => {
                        const up = !peeked || open.includes(i) || matched.has(i);
                        return (
                            <button
                                key={i}
                                className={cn(
                                    'vs-game__synapsecard',
                                    up && 'vs-game__synapsecard--up',
                                    matched.has(i) && 'vs-game__synapsecard--done'
                                )}
                                onClick={() => flip(i)}
                                disabled={!peeked || paused}
                                aria-label={up ? `Card ${sym}` : `Hidden card ${i + 1}`}
                            >
                                <span className="vs-game__synapseback">?</span>
                                <span className="vs-game__synapsefront">{sym}</span>
                            </button>
                        );
                    })}
                </div>
            </div>
        </RoundShell>
    );
}

// --- 7. FORGE: build pipeline in canonical order ---------------------------------------

/** The canonical pipeline. Each build uses a subset, in this order. */
const FORGE_PIPELINE = ['LOAD', 'SCAN', 'CHECK', 'COMPILE', 'ASSEMBLE', 'BOOT', 'RUN', 'SHIP'];

function ForgeOrder({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const total = 4;
    const builds = useMemo(() => {
        const rng = mulberry32(seed);
        const count = 3 + Math.min(3, difficulty);
        return Array.from({ length: total }, () => {
            const subset = shuffle(FORGE_PIPELINE, rng).slice(0, count);
            const steps = FORGE_PIPELINE.filter((s) => subset.includes(s));
            return { steps, options: shuffle(steps, rng) };
        });
    }, [seed, difficulty]);

    const { finish, ended } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [idx, setIdx] = useState(0);
    const [built, setBuilt] = useState<string[]>([]);
    const [score, setScore] = useState(0);
    const [placed, setPlaced] = useState(0);
    const [last, setLast] = useState<{ step: string; ok: boolean } | null>(null);

    const totalSteps = builds.reduce((n, b) => n + b.steps.length, 0);
    const end = (sc: number, good: number, buildsDone: number) =>
        finish({
            score: sc,
            accuracy: pct(good, good + c.mistakes.current),
            mistakes: c.mistakes.current,
            bestCombo: c.best.current,
            completion: pct(buildsDone, total),
        });
    const left = useCountdown(timeLimitMs, paused, () => end(score, placed, idx));
    if (ended) return null;

    const build = builds[idx];
    function pick(step: string) {
        if (paused || built.includes(step) || built.length >= build.steps.length) return;
        const expected = build.steps[built.length];
        if (step !== expected) {
            c.miss();
            setLast({ step, ok: false });
            return;
        }
        c.hit();
        const nextBuilt = [...built, step];
        const newScore = score + 5 * difficulty + Math.min(c.comboRef.current, 5);
        const newPlaced = placed + 1;
        setBuilt(nextBuilt);
        setScore(newScore);
        setPlaced(newPlaced);
        setLast({ step, ok: true });
        if (nextBuilt.length === build.steps.length) {
            window.setTimeout(() => {
                if (idx + 1 >= total) end(newScore + 10 * difficulty, newPlaced, total);
                else {
                    setScore(newScore + 10 * difficulty);
                    setIdx(idx + 1);
                    setBuilt([]);
                    setLast(null);
                }
            }, 380);
        }
    }

    return (
        <RoundShell
            left={left}
            timeLimitMs={timeLimitMs}
            combo={c.combo}
            label={`Build ${idx + 1} of ${total} · ${placed}/${totalSteps} steps`}
        >
            <div className="vs-game__forge">
                <span className="vs-game__forgelabel">
                    {'Assemble in pipeline order: LOAD → SCAN → CHECK → COMPILE → ASSEMBLE → BOOT → RUN → SHIP'}
                </span>
                <div className="vs-game__forgebuilt">
                    {build.steps.map((s, i) => (
                        <span key={s} className={cn('vs-game__forgeslot', built[i] === s && 'vs-game__forgeslot--filled')}>
                            {built[i] === s ? s : i + 1}
                        </span>
                    ))}
                </div>
                <div className="vs-game__forgets">
                    {build.options.map((opt) => (
                        <button
                            key={opt}
                            className={cn('vs-game__forgeopt', last && !last.ok && last.step === opt && 'vs-game__forgeopt--no')}
                            onClick={() => pick(opt)}
                            disabled={paused || built.includes(opt)}
                        >
                            {opt}
                        </button>
                    ))}
                </div>
                {last && (
                    <span className={cn('vs-game__forgestate', last.ok ? 'vs-game__forgestate--ok' : 'vs-game__forgestate--no')}>
                        {last.ok ? 'Step locked in' : `${last.step} is out of order`}
                    </span>
                )}
            </div>
        </RoundShell>
    );
}

// --- 8. ORBIT: collect beacons --------------------------------------------------------

function OrbitGather({ difficulty, timeLimitMs, seed, paused, onEnd, onCombo }: EngineProps) {
    const total = 8;
    const cells = 9;
    const sequence = useMemo(() => {
        const rng = mulberry32(seed);
        const list: number[] = [];
        for (let i = 0; i < total; i++) {
            let next = randInt(rng, 0, cells - 1);
            if (next === list[i - 1]) next = (next + 1 + randInt(rng, 0, cells - 2)) % cells;
            list.push(next);
        }
        return list;
    }, [seed]);
    const fadeMs = Math.max(700, 1700 - difficulty * 150);

    const { finish, ended, doneRef } = useFinisher(onEnd);
    const c = useCombo(onCombo);
    const [shown, setShown] = useState(0);
    const [active, setActive] = useState(false);
    const [collected, setCollected] = useState(0);
    const [misses, setMisses] = useState(0);
    const [score, setScore] = useState(0);
    const collectedRef = useRef(0);
    const scoreRef = useRef(0);
    const pausedRef = useRef(paused);
    pausedRef.current = paused;

    const end = useCallback(() => {
        finish({
            score: scoreRef.current,
            accuracy: pct(collectedRef.current, total),
            mistakes: c.mistakes.current,
            bestCombo: c.best.current,
            completion: pct(collectedRef.current, total),
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [finish]);

    const advance = useCallback(() => {
        setActive(false);
        setShown((s) => {
            const next = s + 1;
            if (next >= total) window.setTimeout(end, 250);
            return next;
        });
    }, [end]);

    useEffect(() => {
        if (doneRef.current || shown >= total) return;
        if (!active) {
            const id = window.setTimeout(() => {
                if (!pausedRef.current) setActive(true);
            }, shown === 0 ? 500 : 300);
            return () => window.clearTimeout(id);
        }
        if (paused) return;
        const id = window.setTimeout(() => {
            c.miss();
            setMisses((m) => m + 1);
            advance();
        }, fadeMs);
        return () => window.clearTimeout(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [active, shown, paused, fadeMs]);

    const left = useCountdown(timeLimitMs, paused, end);
    if (ended) return null;

    const beacon = active && shown < total ? sequence[shown] : null;
    function tap(i: number) {
        if (paused || beacon === null) return;
        if (i === beacon) {
            c.hit();
            collectedRef.current += 1;
            scoreRef.current += 10 * difficulty + Math.min(c.comboRef.current, 6) * 3;
            setCollected(collectedRef.current);
            setScore(scoreRef.current);
            advance();
        } else {
            c.miss();
            scoreRef.current = Math.max(0, scoreRef.current - 2 * difficulty);
            setScore(scoreRef.current);
        }
    }

    return (
        <RoundShell
            left={left}
            timeLimitMs={timeLimitMs}
            combo={c.combo}
            label={`Collected ${collected}/${total} · missed ${misses} · ${score} pts`}
        >
            <div className="vs-game__orbit">
                <span className="vs-game__orbitlabel">Tap the beacon before it fades — wrong sectors cost points</span>
                <div className="vs-game__orbitgrid">
                    {Array.from({ length: cells }, (_, i) => (
                        <button
                            key={i}
                            className={cn(
                                'vs-game__orbitcell',
                                beacon === i && 'vs-game__orbitcell--beacon',
                                shown >= total && 'vs-game__orbitcell--done'
                            )}
                            style={beacon === i ? { animationDuration: `${fadeMs}ms` } : undefined}
                            onClick={() => tap(i)}
                            aria-label={beacon === i ? `Sector ${i + 1}, beacon active` : `Sector ${i + 1}`}
                            disabled={paused}
                        />
                    ))}
                </div>
            </div>
        </RoundShell>
    );
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

const ENGINES: Record<PlayKind, (props: EngineProps) => JSX.Element | null> = {
    'quanta-calc': QuantaCalc,
    'logix-seq': LogixSeq,
    'pulse-timing': PulseTiming,
    'vector-dodge': VectorDodge,
    'cipher-sort': CipherSort,
    'synapse-match': SynapseMatch,
    'forge-order': ForgeOrder,
    'orbit-gather': OrbitGather,
};

export function EngineFor({ kind, props }: { kind: PlayKind; props: EngineProps }): JSX.Element | null {
    const Engine = ENGINES[kind];
    if (!Engine) return null;
    return <Engine {...props} />;
}
