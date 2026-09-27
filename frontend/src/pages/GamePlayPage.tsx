import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Logo from '../components/Logo';
import Icon from '../components/Icon';
import Button from '../components/Button';
import { fetchGameDetail, completeSession, startSession } from '../services/hub';
import { GameDetail, GameSessionState, RunReport } from '../types/hub';
import {
    EngineFor,
    EngineOutcome,
    playKindFor,
    PLAY_KIND_TIME_LIMIT,
    seedFor,
} from '../components/hub/runtimes';

type Phase = 'boot' | 'countdown' | 'announce' | 'playing' | 'saving' | 'error';

const ROUNDS = 6;

export default function GamePlayPage() {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();

    const [phase, setPhase] = useState<Phase>('boot');
    const [detail, setDetail] = useState<GameDetail | null>(null);
    const [session, setSession] = useState<GameSessionState | null>(null);
    const [errorMsg, setErrorMsg] = useState('');
    const [count, setCount] = useState(3);
    const [round, setRound] = useState(1);
    const [score, setScore] = useState(0);
    const [accuracies, setAccuracies] = useState<number[]>([]);
    const [confirmQuit, setConfirmQuit] = useState(false);
    const [saving, setSaving] = useState(false);

    const startedTs = useRef(Date.now());
    const reported = useRef(false);

    useEffect(() => {
        let cancelled = false;
        if (!slug) {
            navigate('/game-hub', { replace: true });
            return;
        }
        (async () => {
            try {
                const game = await fetchGameDetail(slug);
                const started = await startSession(slug);
                if (cancelled) return;
                startedTs.current = Date.now();
                setDetail(game);
                setSession(started.session);
                setPhase('countdown');
                setCount(3);
            } catch (err) {
                if (cancelled) return;
                setErrorMsg(err instanceof Error ? err.message : 'Something went wrong.');
                setPhase('error');
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [slug, navigate]);

    // Boot countdown 3 -> 0
    useEffect(() => {
        if (phase !== 'countdown') return;
        if (count === 0) {
            setPhase('announce');
            return;
        }
        const id = window.setTimeout(() => setCount((c) => c - 1), 700);
        return () => window.clearTimeout(id);
    }, [phase, count]);

    // Announce next level briefly, then play
    useEffect(() => {
        if (phase !== 'announce') return;
        const id = window.setTimeout(() => setPhase('playing'), 850);
        return () => window.clearTimeout(id);
    }, [phase]);

    const kind = playKindFor(detail?.play_kind ?? '');
    const timeLimit = PLAY_KIND_TIME_LIMIT[kind];

    async function finishRun(outcome: 'completed' | 'failed', finalScore: number, finalAcc: number, levels: number) {
        if (reported.current || !session) return;
        reported.current = true;
        setPhase('saving');
        const duration = Math.max(1, Math.floor((Date.now() - startedTs.current) / 1000));
        const report: RunReport = {
            score: finalScore,
            accuracy: Math.max(0, Math.min(100, Math.round(finalAcc))),
            level_reached: Math.max(1, Math.min(8, levels)),
            duration_seconds: duration,
            outcome,
        };
        try {
            setSaving(true);
            const result = await completeSession(session.id, report);
            setSaving(false);
            navigate(`/games/${slug}/result`, {
                replace: true,
                state: { detail, result, report },
            });
        } catch (err) {
            setSaving(false);
            navigate(`/games/${slug}/result`, {
                replace: true,
                state: {
                    detail,
                    result: null,
                    report,
                    error: err instanceof Error ? err.message : 'We couldn’t save this run.',
                },
            });
        }
    }

    function handleRoundEnd(outcome: EngineOutcome) {
        const newRound = round + 1;
        const newScore = score + outcome.score;
        const nextAcc = [...accuracies, outcome.accuracy];
        setScore(newScore);
        setAccuracies(nextAcc);
        if (newRound > ROUNDS) {
            const acc = nextAcc.length ? Math.round(nextAcc.reduce((a, b) => a + b, 0) / nextAcc.length) : 0;
            void finishRun('completed', newScore, acc, ROUNDS);
            return;
        }
        setRound(newRound);
        setPhase('announce');
    }

    function quit() {
        const acc = accuracies.length ? Math.round(accuracies.reduce((a, b) => a + b, 0) / accuracies.length) : 0;
        void finishRun('failed', score, acc, Math.max(0, round - 1));
    }

    if (phase === 'error' || !slug) {
        return (
            <div className="vs-play">
                <PlayTopBar
                    title={detail?.title ?? 'Run'}
                    onQuit={() => setConfirmQuit(true)}
                />
                <div className="vs-play__center">
                    <div className="vs-hub__errorcard animate-pop">
                        <span className="vs-hub__erroricon">
                            <Icon name="alert" size={28} />
                        </span>
                        <h1>We couldn’t start this game.</h1>
                        <p>{errorMsg || 'Please try again in a moment.'}</p>
                        <div className="vs-hub__erroractions">
                            <Button variant="outline" size="lg" icon="refresh" onClick={() => navigate(0)}>
                                Retry
                            </Button>
                            <Button variant="ghost" size="lg" onClick={() => navigate('/game-hub')}>
                                Back to hub
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="vs-play">
            <PlayTopBar
                title={detail ? `${detail.title} — L${round}` : 'Loading…'}
                onQuit={() => setConfirmQuit(true)}
            />

            {(phase === 'boot' || !detail || !session) && (
                <div className="vs-play__center">
                    <div className="vs-play__boot">
                        <Logo size="lg" showWordmark={false} />
                        <p>Warming up the engines…</p>
                    </div>
                </div>
            )}

            {phase === 'countdown' && detail && (
                <div className="vs-play__center">
                    <div className="vs-play__count" key={count}>
                        <span>{count > 0 ? count : 'GO'}</span>
                        <p>{detail.title}</p>
                    </div>
                </div>
            )}

            {phase === 'announce' && detail && (
                <div className="vs-play__center">
                    <div className="vs-play__announce">
                        <span className="vs-play__announcechip">
                            <Icon name={detail.play_kind ? playIcon(detail.play_kind) : 'play'} size={18} />
                        </span>
                        <h1>Round {round}</h1>
                        <p>Score {score} · difficulty climbs with every round</p>
                    </div>
                </div>
            )}

            {phase === 'playing' && detail && !saving && (
                <div className="vs-play__engine">
                    <EngineFor
                        kind={kind}
                        props={{
                            round,
                            difficulty: Math.min(6, round),
                            timeLimitMs: timeLimit,
                            seed: seedFor(slug, round),
                            onEnd: handleRoundEnd,
                        }}
                    />
                    <div className="vs-play__hud">
                        <span>
                            <Icon name="play" size={13} /> Score {score}
                        </span>
                        <span>Round {round} / {ROUNDS}</span>
                    </div>
                </div>
            )}

            {phase === 'saving' && (
                <div className="vs-play__center">
                    <div className="vs-play__boot">
                        <div className="vs-play__savingring" />
                        <p>Saving your run…</p>
                    </div>
                </div>
            )}

            {confirmQuit && (
                <div className="vs-hub__confirm vs-play__confirm">
                    <div className="vs-hub__confirmcard animate-pop" role="dialog" aria-modal="true" aria-labelledby="quit-title">
                        <span className="vs-hub__confirmlogo">
                            <Logo size="md" showWordmark={false} />
                        </span>
                        <h2 id="quit-title">End this run?</h2>
                        <p>This run will be recorded as failed — no XP is awarded for abandoned runs.</p>
                        <div className="vs-hub__confirmactions">
                            <Button variant="ghost" size="lg" onClick={() => setConfirmQuit(false)} disabled={saving}>
                                Keep playing
                            </Button>
                            <Button variant="danger" size="lg" loading={saving} onClick={() => void quit()}>
                                End run
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function playIcon(kind: string): 'bolt' | 'puzzle' | 'timer' | 'arrow' | 'layers' | 'grid' | 'list' | 'compass' {
    const map: Record<string, 'bolt' | 'puzzle' | 'timer' | 'arrow' | 'layers' | 'grid' | 'list' | 'compass'> = {
        'quanta-calc': 'bolt',
        'logix-seq': 'puzzle',
        'pulse-timing': 'timer',
        'vector-dodge': 'arrow',
        'cipher-sort': 'layers',
        'synapse-match': 'grid',
        'forge-order': 'list',
        'orbit-gather': 'compass',
    };
    return map[kind] ?? 'play';
}

function PlayTopBar({ title, onQuit }: { title: string; onQuit: () => void }) {
    return (
        <header className="vs-play__top">
            <div className="vs-play__topbrand">
                <Logo size="sm" showWordmark={false} />
                <b>VECTOR STRIKE</b>
            </div>
            <span className="vs-play__toptitle">{title}</span>
            <button className="vs-btn vs-btn--ghost vs-btn--sm" onClick={onQuit}>
                <Icon name="x" size={16} /> Quit
            </button>
        </header>
    );
}