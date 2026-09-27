import { useEffect, useMemo, useRef, useState } from 'react';
import type { JSX, ReactNode } from 'react';
import { cn } from '../../utils/cn';
import Icon from '../Icon';

// ---------------------------------------------------------------------------
// Genre runtimes — each play_kind is a distinct mechanic (typing, pattern,
// timing, dodge, order, match, sequence, collect). Every engine is fully
// client-side gameplay; the backend only ever stores the bounds-checked,
// server-computed result of a finished run.
// ---------------------------------------------------------------------------

export interface EngineOutcome {
    score: number;
    accuracy: number;
}

export interface EngineProps {
    round: number;
    difficulty: number;
    timeLimitMs: number;
    seed: number;
    onEnd: (outcome: EngineOutcome) => void;
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
    'pulse-timing': 10000,
    'vector-dodge': 9000,
    'cipher-sort': 24000,
    'synapse-match': 28000,
    'forge-order': 22000,
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
    return (PLAY_KIND_TIME_LIMIT as Record<string, number>)[kind] ? kind as PlayKind : 'logix-seq';
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

// --- shared round shell -----------------------------------------------------

function useCountdown(ms: number, onZero: () => void) {
    const [left, setLeft] = useState(ms);
    const fired = useRef(false);
    useEffect(() => {
        const id = window.setInterval(() => {
            setLeft((v) => {
                const next = v - 100;
                if (next <= 0) {
                    window.clearInterval(id);
                    return 0;
                }
                return next;
            });
        }, 100);
        return () => window.clearInterval(id);
    }, []);
    useEffect(() => {
        if (left <= 0 && !fired.current) {
            fired.current = true;
            onZero();
        }
    }, [left, onZero]);
    return left;
}

function RoundShell({
    left,
    timeLimitMs,
    label,
    children,
}: {
    left: number;
    timeLimitMs: number;
    label: string;
    children: ReactNode;
}) {
    const pct = Math.max(0, Math.min(100, (left / timeLimitMs) * 100));
    const color = pct > 50 ? '' : pct > 25 ? ' vs-game__bar--warn' : ' vs-game__bar--danger';
    return (
        <div className="vs-game">
            <div className="vs-game__barwrap">
                <span className={cn('vs-game__bar', color)} style={{ width: `${pct}%` }} />
            </div>
            <div className="vs-game__meta">
                <b>{label}</b>
                <span>{Math.ceil(left / 1000)}s</span>
            </div>
            {children}
        </div>
    );
}

// --- 1. QUANTA: speed arithmetic ---------------------------------------------

function QuantaCalc({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const total = 4 + difficulty;
    const tasks = useMemo(() => {
        const list: Array<{ text: string; answer: number }> = [];
        for (let i = 0; i < total; i++) {
            const d = Math.max(1, difficulty);
            const op = rng();
            let a = randInt(rng, 1 + d, 6 + d * 4);
            let b = randInt(rng, 1, 2 + d * 2);
            let answer = 0;
            let text = '';
            if (op < 0.25 || d <= 1) {
                answer = a + b;
                text = `${a} + ${b}`;
            } else if (op < 0.5) {
                const big = Math.max(a, b);
                const small = Math.min(a, b);
                answer = big - small;
                text = `${big} − ${small}`;
            } else if (op < 0.75) {
                b = randInt(rng, 2, 2 + d);
                answer = a * b;
                text = `${a} × ${b}`;
            } else {
                const mult = randInt(rng, 2, 2 + d);
                a = mult * randInt(rng, 2, 2 + d * 2);
                answer = a / mult;
                text = `${a} ÷ ${mult}`;
            }
            list.push({ text, answer });
        }
        return list;
    }, [rng, difficulty, total]);

    const done = useRef(false);
    const [idx, setIdx] = useState(0);
    const [value, setValue] = useState('');
    const [correct, setCorrect] = useState(0);
    const [score, setScore] = useState(0);
    const [flash, setFlash] = useState<'' | 'ok' | 'no'>('');

    const finish = (answered: number, ok: number, sc: number) => {
        if (done.current) return;
        done.current = true;
        onEnd({
            score: sc,
            accuracy: answered ? Math.round((ok / answered) * 100) : 0,
        });
    };

    const left = useCountdown(timeLimitMs, () => finish(idx, correct, score));
    if (done.current) return null;

    function submit() {
        const num = parseInt(value, 10);
        if (value.trim() === '' || Number.isNaN(num)) return;
        const task = tasks[idx];
        const isOk = num === task.answer;
        const newScore = score + (isOk ? 10 * difficulty : 0);
        const newCorrect = correct + (isOk ? 1 : 0);
        setCorrect(newCorrect);
        setScore(newScore);
        setFlash(isOk ? 'ok' : 'no');
        window.setTimeout(() => {
            if (idx + 1 >= total) finish(total, newCorrect, newScore);
            else {
                setIdx(idx + 1);
                setValue('');
                setFlash('');
            }
        }, 260);
    }

    const task = tasks[idx];
    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`Task ${idx + 1} of ${total}`}>
            <div className="vs-game__quanta">
                <span className="vs-game__quantaq">{task.text}</span>
                <span className="vs-game__quantaop">= ?</span>
                <input
                    className="vs-game__quantainput"
                    value={value}
                    onChange={(e) => setValue(e.target.value.replace(/[^0-9-]/g, ''))}
                    placeholder="Answer"
                    aria-label="Your answer"
                    autoFocus
                    inputMode="numeric"
                    onKeyDown={(e) => e.key === 'Enter' && submit()}
                />
                <button className="vs-btn vs-btn--solid vs-btn--lg" onClick={submit}>
                    Lock it in
                </button>
                {flash && (
                    <span className={cn('vs-game__flash', flash === 'ok' ? 'vs-game__flash--ok' : 'vs-game__flash--no')}>
                        {flash === 'ok' ? 'Correct' : 'Nope'}
                    </span>
                )}
            </div>
        </RoundShell>
    );
}

// --- 2. LOGIX: next-in-pattern ------------------------------------------------

function LogixSeq({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const total = 5;
    const questions = useMemo(() => {
        const list: Array<{ terms: number[]; choices: number[]; answerIdx: number }> = [];
        for (let q = 0; q < total; q++) {
            const d = Math.max(1, difficulty);
            const style = rng();
            const terms = [0, 0, 0, 0, 0];
            let answer: number;
            if (style < 0.4) {
                const step = randInt(rng, 1, d + 2);
                const start = randInt(rng, 1, 5);
                for (let i = 0; i < 5; i++) terms[i] = start + i * step;
                answer = terms[4];
            } else if (style < 0.7) {
                const mult = randInt(rng, 2, d + 1);
                const start = randInt(rng, 1, 3);
                for (let i = 0; i < 5; i++) terms[i] = start * Math.pow(mult, i);
                answer = terms[4];
            } else {
                const step = randInt(rng, 2, d + 2);
                const start = randInt(rng, 5, 10);
                for (let i = 0; i < 5; i++) terms[i] = i % 2 === 0 ? start + i * step : start + i * step * 2;
                answer = terms[4];
            }
            const wrong = new Set<number>();
            while (wrong.size < 4) wrong.add(answer + randInt(rng, 1, 3) * (rng() < 0.5 ? -1 : 1));
            const choices = shuffle([...wrong, answer], rng);
            list.push({ terms, choices, answerIdx: choices.indexOf(answer) });
        }
        return list;
    }, [rng, difficulty]);

    const done = useRef(false);
    const [idx, setIdx] = useState(0);
    const [correct, setCorrect] = useState(0);
    const [score, setScore] = useState(0);
    const [locked, setLocked] = useState<number | null>(null);

    const finish = (answered: number, ok: number, sc: number) => {
        if (done.current) return;
        done.current = true;
        onEnd({ score: sc, accuracy: answered ? Math.round((ok / answered) * 100) : 0 });
    };
    const left = useCountdown(timeLimitMs, () => finish(idx, correct, score));
    if (done.current) return null;

    const q = questions[idx];
    function pick(i: number) {
        if (locked !== null) return;
        setLocked(i);
        const isOk = i === q.answerIdx;
        const newScore = score + (isOk ? 10 * difficulty : 0);
        const newCorrect = correct + (isOk ? 1 : 0);
        setScore(newScore);
        setCorrect(newCorrect);
        window.setTimeout(() => {
            if (idx + 1 >= total) finish(total, newCorrect, newScore);
            else {
                setIdx(idx + 1);
                setLocked(null);
            }
        }, 300);
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`Pattern ${idx + 1} of ${total}`}>
            <div className="vs-game__logix">
                <span className="vs-game__logixlabel">What comes next?</span>
                <div className="vs-game__logixterms">
                    {q.terms.slice(0, 4).map((t, i) => (
                        <span key={i} className="vs-game__logixterm">{t}</span>
                    ))}
                    <span className="vs-game__logixq">?</span>
                </div>
                <div className="vs-game__logixopts">
                    {q.choices.map((c, i) => (
                        <button
                            key={i}
                            className={cn(
                                'vs-game__logixopt',
                                locked === i && (i === q.answerIdx ? 'vs-game__logixopt--ok' : 'vs-game__logixopt--no')
                            )}
                            onClick={() => pick(i)}
                        >
                            {c}
                        </button>
                    ))}
                </div>
            </div>
        </RoundShell>
    );
}

// --- 3. PULSE: reaction timing --------------------------------------------------

function PulseTiming({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const attempts = 3;
    const [tries, setTries] = useState(0);
    const [target] = useState(() => randInt(rng, 20, 80));
    const [pos, setPos] = useState(0);
    const [dir, setDir] = useState(1);
    const [score, setScore] = useState(0);
    const [accepted, setAccepted] = useState(0);
    const [last, setLast] = useState<{ d: number; ok: boolean } | null>(null);
    const done = useRef(false);
    const speed = 1.1 + difficulty * 0.25;

    const finish = (sc: number, acc: number) => {
        if (done.current) return;
        done.current = true;
        onEnd({ score: sc, accuracy: acc });
    };
    const left = useCountdown(timeLimitMs, () => finish(score, accepted ? Math.round(score / (attempts * 10 * difficulty) * 100) : 0));
    if (done.current) return null;

    useEffect(() => {
        let raf = 0;
        const tick = () => {
            setPos((p) => {
                const next = p + dir * speed;
                if (next > 100) {
                    setDir(-1);
                    return 100;
                }
                if (next < 0) {
                    setDir(1);
                    return 0;
                }
                return next;
            });
            raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(raf);
    }, [dir, speed]);

    function tap() {
        if (done.current) return;
        const d = Math.abs(pos - target);
        const pct = Math.max(0, 100 - Math.round(d * 9));
        const gained = pct >= 80 ? 10 * difficulty : pct >= 45 ? 7 * difficulty : 3 * difficulty;
        const newScore = score + gained;
        const newAccepted = accepted + 1;
        setScore(newScore);
        setAccepted(newAccepted);
        setLast({ d, ok: pct >= 45 });
        setTries((t) => t + 1);
        if (tries + 1 >= attempts) {
            finish(newScore, newAccepted ? Math.round((newScore / (attempts * 10 * difficulty)) * 100) : 0);
        }
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`Tap ${Math.min(tries + 1, attempts)} of ${attempts}`}>
            <div className="vs-game__pulse">
                <span className="vs-game__pulselabel">Hit SPACE or tap when the marker crosses the zone</span>
                <div className="vs-game__pulserail">
                    <span className="vs-game__pulsezone" style={{ left: `${target}%` }} />
                    <span className="vs-game__pulsemarker" style={{ left: `${pos}%` }} />
                </div>
                <button className="vs-btn vs-btn--solid vs-btn--lg" onClick={tap}>
                    Fire
                </button>
                {last && (
                    <span className={cn('vs-game__pulsefback', last.ok ? 'vs-game__pulsefback--ok' : 'vs-game__pulsefback--no')}>
                        {last.ok ? 'In the zone' : 'Just missed'} · {Math.round(last.d)} off
                    </span>
                )}
            </div>
        </RoundShell>
    );
}

// --- 4. VECTOR: lane dodge -------------------------------------------------------

const LANES = 5;

function VectorDodge({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const [playerCol, setPlayerCol] = useState(2);
    const [obstacles, setObstacles] = useState<Array<{ col: number; row: number }>>([]);
    const [hits, setHits] = useState(0);
    const [dodges, setDodges] = useState(0);
    const [shake, setShake] = useState(false);
    const done = useRef(false);

    const finish = (dge: number, ht: number) => {
        if (done.current) return;
        done.current = true;
        const acc = dge + ht ? Math.round((dge / (dge + ht)) * 100) : 100;
        onEnd({ score: dge * 10 * difficulty - ht * 5 * difficulty, accuracy: acc });
    };
    const left = useCountdown(timeLimitMs, () => finish(dodges, hits));
    if (done.current) return null;

    useEffect(() => {
        const spawn = window.setInterval(() => {
            setObstacles((prev) => {
                const col = randInt(rng, 0, LANES - 1);
                return [...prev.slice(-14), { col, row: 0 }];
            });
        }, 340 - difficulty * 20);
        const move = window.setInterval(() => {
            setObstacles((prev) => {
                let nextHits = 0;
                let nextDodges = 0;
                const updated = prev.map((o) => {
                    const row = o.row + 1;
                    if (row >= 4 && o.col === playerCol) nextHits += 1;
                    else if (row >= 4) nextDodges += 1;
                    return { col: o.col, row };
                });
                if (nextHits > 0) {
                    setHits((h) => h + nextHits);
                    setShake(true);
                    window.setTimeout(() => setShake(false), 120);
                }
                if (nextDodges > 0) setDodges((d) => d + nextDodges);
                return updated.filter((o) => o.row < 4);
            });
        }, 220);
        const keys = (e: KeyboardEvent) => {
            if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') setPlayerCol((c) => Math.max(0, c - 1));
            if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') setPlayerCol((c) => Math.min(LANES - 1, c + 1));
        };
        window.addEventListener('keydown', keys);
        return () => {
            window.clearInterval(spawn);
            window.clearInterval(move);
            window.removeEventListener('keydown', keys);
        };
    }, [playerCol, rng, difficulty]);

    const grid: ReactNode[] = [];
    for (let row = 3; row >= 0; row--) {
        for (let col = 0; col < LANES; col++) {
            const obstacle = obstacles.some((o) => o.col === col && o.row === row);
            const isPlayer = row === 0 && col === playerCol;
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
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`Dodge ${dodges} · hits ${hits}`}>
            <div className="vs-game__dodge">
                <div className={cn('vs-game__dodgegrid', shake && 'vs-game__dodgegrid--shake')} style={{ gridTemplateColumns: `repeat(${LANES}, 1fr)` }}>
                    {grid}
                </div>
                <div className="vs-game__dodgekeys" aria-hidden>
                    <button className="vs-btn vs-btn--outline vs-btn--sm" onClick={() => setPlayerCol((c) => Math.max(0, c - 1))}>
                        <Icon name="chevron-left" size={16} />
                    </button>
                    <span>← → to move · survive</span>
                    <button className="vs-btn vs-btn--outline vs-btn--sm" onClick={() => setPlayerCol((c) => Math.min(LANES - 1, c + 1))}>
                        <Icon name="chevron-right" size={16} />
                    </button>
                </div>
            </div>
        </RoundShell>
    );
}

// --- 5. CIPHER: reorder tiles -----------------------------------------------------

function CipherSort({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const total = 4;
    const tasks = useMemo(() => {
        const list: Array<{ values: number[] }> = [];
        for (let i = 0; i < total; i++) {
            const d = Math.max(1, difficulty);
            const base = randInt(rng, 1, 10 + d * 3);
            const step = randInt(rng, 1, d + 2);
            const sorted: number[] = [];
            for (let k = 0; k < 4; k++) sorted.push(base + k * step);
            const values = shuffle(sorted, rng);
            list.push({ values });
        }
        return list;
    }, [rng, difficulty]);

    const done = useRef(false);
    const [idx, setIdx] = useState(0);
    const [order, setOrder] = useState<number[]>(tasks[0].values);
    const [correct, setCorrect] = useState(0);
    const [score, setScore] = useState(0);
    const [moves, setMoves] = useState(0);
    const [picked, setPicked] = useState<number | null>(null);

    const finish = (answered: number, ok: number, sc: number) => {
        if (done.current) return;
        done.current = true;
        onEnd({ score: sc, accuracy: answered ? Math.round((ok / answered) * 100) : 0 });
    };
    const left = useCountdown(timeLimitMs, () => finish(idx, correct, score));
    if (done.current) return null;

    const current = tasks[idx];
    function choose(j: number) {
        if (picked === null || picked === j) {
            setPicked(null);
            return;
        }
        const nextOrder = order.slice();
        [nextOrder[picked], nextOrder[j]] = [nextOrder[j], nextOrder[picked]];
        const newMoves = moves + 1;
        setOrder(nextOrder);
        setMoves(newMoves);
        setPicked(null);
        const exact = nextOrder.join(',') === [...nextOrder].sort((a, b) => a - b).join(',');
        if (exact) {
            const newScore = score + 10 * difficulty;
            const newCorrect = correct + 1;
            setScore(newScore);
            setCorrect(newCorrect);
            window.setTimeout(() => {
                if (idx + 1 >= total) finish(total, newCorrect, newScore);
                else {
                    const next = tasks[idx + 1].values;
                    setIdx(idx + 1);
                    setOrder(next);
                    setMoves(0);
                }
            }, 350);
        }
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`Grid ${idx + 1} of ${total} · ${moves} moves`}>
            <div className="vs-game__cipher">
                <span className="vs-game__cipherlabel">Tap two tiles to swap them into ascending order</span>
                <div className="vs-game__ciphertiles">
                    {order.map((v, i) => (
                        <button
                            key={`${idx}-${i}`}
                            className={cn('vs-game__ciphertile', picked === i && 'vs-game__ciphertile--picked')}
                            onClick={() => choose(i)}
                        >
                            {String(v).padStart(2, '0')}
                        </button>
                    ))}
                </div>
                {moves > 0 && <button className="vs-btn vs-btn--ghost vs-btn--sm" onClick={() => { setOrder(current.values); setMoves(0); setPicked(null); }}>Reset</button>}
            </div>
        </RoundShell>
    );
}

// --- 6. SYNAPSE: card match ---------------------------------------------------------

const SYNAPSE_PAIRS = 4;

function SynapseMatch({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const deck = useMemo(() => {
        const symbols = ['◆', '●', '▲', '★'];
        return shuffle(symbols.concat(symbols), rng);
    }, [rng]);

    const done = useRef(false);
    const [revealed, setRevealed] = useState<boolean[]>(() => deck.map(() => false));
    const [matched, setMatched] = useState<Set<number>>(new Set());
    const [moves, setMoves] = useState(0);
    const [peeked, setPeeked] = useState(false);

    useEffect(() => {
        const id = window.setTimeout(() => setPeeked(true), 1400);
        return () => window.clearTimeout(id);
    }, []);

    const finished = matched.size === deck.length;
    const accuracy = finished ? Math.max(0, 100 - (moves - SYNAPSE_PAIRS) * 12) : 0;

    const finish = (sc: number, acc: number) => {
        if (done.current) return;
        done.current = true;
        onEnd({ score: sc, accuracy: acc });
    };
    const left = useCountdown(timeLimitMs, () => finish(matched.size * 10 * difficulty, accuracy));
    if (done.current) return null;

    useEffect(() => {
        if (finished) {
            finish(SYNAPSE_PAIRS * 10 * difficulty, accuracy);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [finished]);

    function flip(i: number) {
        if (!peeked || matched.has(i) || revealed[i]) return;
        const next = revealed.slice();
        next[i] = true;
        setRevealed(next);
        const open = next.map((v, idx) => (v && !matched.has(idx) ? idx : -1)).filter((v) => v >= 0);
        if (open.length === 2) {
            const [a, b] = open;
            setMoves((m) => m + 1);
            if (deck[a] === deck[b]) {
                setMatched((prev) => new Set([...prev, a, b]));
                setRevealed(() => deck.map(() => false));
            } else {
                window.setTimeout(() => setRevealed(() => deck.map(() => false)), 700);
            }
        }
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`${matched.size}/${deck.length / 2} pairs · ${moves} moves`}>
            <div className="vs-game__synapse">
                <span className="vs-game__synapselabel">{peeked ? 'Flip two cards to match the symbols' : 'Memorize the symbols…'}</span>
                <div className="vs-game__synapsegrid">
                    {deck.map((sym, i) => {
                        const up = revealed[i] || (finished && matched.has(i));
                        return (
                            <button
                                key={i}
                                className={cn('vs-game__synapsecard', up && 'vs-game__synapsecard--up', matched.has(i) && 'vs-game__synapsecard--done')}
                                onClick={() => flip(i)}
                                disabled={!peeked}
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

// --- 7. FORGE: next build step -------------------------------------------------------

const FORGE_STEPS = ['LOAD', 'CHECK', 'COMPILE', 'RUN', 'SHIP', 'SCAN', 'BOOT', 'ASSEMBLE'];

function ForgeOrder({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const total = 4;
    const builds = useMemo(() => {
        const list: Array<{ steps: string[] }> = [];
        for (let q = 0; q < total; q++) {
            const count = 3 + Math.min(2, difficulty);
            const pool = shuffle(FORGE_STEPS, rng);
            list.push({ steps: pool.slice(0, count) });
        }
        return list;
    }, [rng, difficulty]);

    const done = useRef(false);
    const [idx, setIdx] = useState(0);
    const [built, setBuilt] = useState<string[]>([]);
    const [remaining, setRemaining] = useState<string[]>(builds[0].steps);
    const [options, setOptions] = useState<string[]>(builds[0].steps);
    const [, setAttempts] = useState(0);
    const [mistakes, setMistakes] = useState(0);
    const [last, setLast] = useState<'' | 'ok' | 'no'>('');

    const finish = (err: number) => {
        if (done.current) return;
        done.current = true;
        const answered = total;
        const ok = Math.max(0, answered - err);
        onEnd({ score: Math.max(0, answered * 10 * difficulty - err * 5 * difficulty), accuracy: ok ? Math.round((ok / answered) * 100) : 0 });
    };
    const left = useCountdown(timeLimitMs, () => finish(mistakes));
    if (done.current) return null;

    const build = builds[idx];
    function pick(step: string) {
        const nextBuilt = [...built, step];
        const nextRemaining = remaining.filter((s) => s !== step);
        const isOk = nextBuilt.join(',') === build.steps.slice(0, nextBuilt.length).join(',');
        setLast(isOk ? 'ok' : 'no');
        setAttempts((a) => a + 1);
        if (!isOk) setMistakes((m) => m + 1);
        setBuilt(nextBuilt);
        setRemaining(nextRemaining);
        if (nextBuilt.length === build.steps.length) {
            window.setTimeout(() => {
                if (idx + 1 >= total) finish(mistakes + (isOk ? 0 : 1));
                else {
                    const next = builds[idx + 1];
                    setIdx(idx + 1);
                    setBuilt([]);
                    setOptions(next.steps);
                    setRemaining(next.steps);
                    setLast('');
                }
            }, 320);
        }
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`Build ${idx + 1} of ${total}`}>
            <div className="vs-game__forge">
                <span className="vs-game__forgelabel">Assemble the pipeline — pick steps in the safe order</span>
                <div className="vs-game__forgebuilt">
                    {build.steps.map((s, i) => (
                        <span key={s} className={cn('vs-game__forgeslot', built[i] === s && 'vs-game__forgeslot--filled')}>
                            {built[i] === s ? s : i + 1}
                        </span>
                    ))}
                </div>
                <div className="vs-game__forgets">
                    {options.map((opt) => (
                        <button
                            key={opt}
                            className="vs-game__forgeopt"
                            onClick={() => pick(opt)}
                            disabled={built.includes(opt)}
                        >
                            {opt}
                        </button>
                    ))}
                </div>
                {last && (
                    <span className={cn('vs-game__forgestate', last === 'ok' ? 'vs-game__forgestate--ok' : 'vs-game__forgestate--no')}>
                        {last === 'ok' ? 'Step locked in' : 'Step out of place'}
                    </span>
                )}
            </div>
        </RoundShell>
    );
}

// --- 8. ORBIT: collect beacons --------------------------------------------------------

function OrbitGather({ difficulty, timeLimitMs, seed, onEnd }: EngineProps) {
    const rng = useMemo(() => mulberry32(seed), [seed]);
    const total = 6;
    const [beacon, setBeacon] = useState<number | null>(null);
    const [collected, setCollected] = useState(0);
    const [missed, setMissed] = useState(0);
    const [streak, setStreak] = useState(0);
    const done = useRef(false);
    const shown = useRef(0);

    const finish = (col: number, mis: number) => {
        if (done.current) return;
        done.current = true;
        onEnd({
            score: col * 10 * difficulty + streak * 4,
            accuracy: col + mis ? Math.round((col / (col + mis)) * 100) : 100,
        });
    };
    const left = useCountdown(timeLimitMs, () => finish(collected, missed));
    if (done.current) return null;

    useEffect(() => {
        if (beacon !== null) {
            const id = window.setTimeout(() => {
                setMissed((m) => m + 1);
                setStreak(0);
                shown.current += 1;
                setBeacon(null);
                if (shown.current >= total) finish(collected, missed + 1);
                else window.setTimeout(() => setBeacon(randInt(rng, 0, 8)), 350);
            }, Math.max(900, 1900 - difficulty * 150));
            return () => window.clearTimeout(id);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [beacon]);

    useEffect(() => {
        if (beacon === null && shown.current === 0) {
            const id = window.setTimeout(() => setBeacon(randInt(rng, 0, 8)), 500);
            return () => window.clearTimeout(id);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [beacon]);

    function tap(i: number) {
        if (beacon === i) {
            shown.current += 1;
            setCollected((c) => c + 1);
            setStreak((s) => s + 1);
            setBeacon(null);
            if (shown.current >= total) finish(collected + 1, missed);
            else window.setTimeout(() => setBeacon(randInt(rng, 0, 8)), 300);
        } else {
            setStreak(0);
        }
    }

    return (
        <RoundShell left={left} timeLimitMs={timeLimitMs} label={`Collected ${collected}/${total} · streak ${streak}`}>
            <div className="vs-game__orbit">
                <span className="vs-game__orbitlabel">Tap the beacon before it fades</span>
                <div className="vs-game__orbitgrid">
                    {Array.from({ length: 9 }, (_, i) => (
                        <button
                            key={i}
                            className={cn('vs-game__orbitcell', beacon === i && 'vs-game__orbitcell--beacon', collected + missed >= total && 'vs-game__orbitcell--done')}
                            onClick={() => tap(i)}
                            aria-label={`Sector ${i + 1}`}
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