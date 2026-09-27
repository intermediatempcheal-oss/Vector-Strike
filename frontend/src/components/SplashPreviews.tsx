import { useEffect, useState } from 'react';

interface Demo {
    key: string;
    game: string;
    engine: string;
    line: string;
}

const DEMOS: Demo[] = [
    { key: 'pulse-timing', game: 'Pulse Timing', engine: 'pulse-timing', line: 'Read the lane, hit the pulse dead-centre.' },
    { key: 'vector-dodge', game: 'Vector Dodge', engine: 'vector-dodge', line: 'Thread incoming vectors — one life, no restarts.' },
    { key: 'cipher-sort', game: 'Cipher Sort', engine: 'cipher-sort', line: 'Drag scrambled values into ascending order.' },
    { key: 'synapse-match', game: 'Synapse Match', engine: 'synapse-match', line: 'Flip tiles, pair the matching synapses.' },
    { key: 'quanta-calc', game: 'Quanta Calc', engine: 'quanta-calc', line: 'Shatter the equation before the timer runs out.' },
];

const ROTATE_MS = 5000;

export default function SplashPreviews() {
    const [active, setActive] = useState(0);

    useEffect(() => {
        const id = window.setInterval(() => {
            setActive((a) => (a + 1) % DEMOS.length);
        }, ROTATE_MS);
        return () => window.clearInterval(id);
    }, []);

    return (
        <section className="vs-pv">
            <div className="vs-pv__top">
                <span className="vs-pv__eyebrow">See how it plays</span>
                <p>Five live previews of the Vector Strike engines.</p>
            </div>
            <div className="vs-pv__stage">
                {DEMOS.map((demo, i) => (
                    <div
                        key={demo.key}
                        className={`vs-pv__panel${i === active ? ' is-active' : ''}`}
                        role="tabpanel"
                        aria-hidden={i !== active}
                        style={{ zIndex: 10 - i }}
                    >
                        <div className={`vs-pv__scene vs-pv__scene--${demo.engine}`}>
                            <Scene engine={demo.engine} />
                        </div>
                        <div className="vs-pv__meta">
                            <b>{demo.game}</b>
                            <span>{demo.engine} engine</span>
                            <p>{demo.line}</p>
                        </div>
                    </div>
                ))}
            </div>
            <div className="vs-pv__dots">
                {DEMOS.map((d, i) => (
                    <button
                        key={d.key}
                        type="button"
                        className={`vs-pv__dot${i === active ? ' is-active' : ''}`}
                        aria-label={`Preview ${d.game}`}
                        onClick={() => setActive(i)}
                    />
                ))}
            </div>
        </section>
    );
}

function Scene({ engine }: { engine: string }) {
    switch (engine) {
        case 'pulse-timing':
            return (
                <div className="vs-demo vs-demo--pulse">
                    <div className="vs-demo__lane">
                        <span className="vs-demo__ring vs-demo__ring--1" />
                        <span className="vs-demo__ring vs-demo__ring--2" />
                        <span className="vs-demo__ring vs-demo__ring--3" />
                        <span className="vs-demo__tap" />
                        <span className="vs-demo__score">PERFECT</span>
                    </div>
                </div>
            );
        case 'vector-dodge':
            return (
                <div className="vs-demo vs-demo--dodge">
                    <span className="vs-demo__ship" />
                    <span className="vs-demo__shot" />
                    <span className="vs-demo__shot vs-demo__shot--2" />
                    <span className="vs-demo__shot vs-demo__shot--3" />
                    <span className="vs-demo__lives">1 LIFE · NO RESTART</span>
                </div>
            );
        case 'cipher-sort':
            return (
                <div className="vs-demo vs-demo--cipher">
                    <div className="vs-demo__rack">
                        <span className="vs-demo__chip">4</span>
                        <span className="vs-demo__chip">1</span>
                        <span className="vs-demo__chip">5</span>
                        <span className="vs-demo__chip">2</span>
                        <span className="vs-demo__chip">3</span>
                    </div>
                    <span className="vs-demo__asc">ascending</span>
                </div>
            );
        case 'synapse-match':
            return (
                <div className="vs-demo vs-demo--match">
                    {[0, 1, 2, 3, 4, 5].map((n) => (
                        <span key={n} className="vs-demo__tile" data-n={n} />
                    ))}
                    <span className="vs-demo__pair">MATCHED 3/3</span>
                </div>
            );
        case 'quanta-calc':
            return (
                <div className="vs-demo vs-demo--calc">
                    <span className="vs-demo__prompt">9 + 7 =</span>
                    <div className="vs-demo__opts">
                        <span className="vs-demo__opt">14</span>
                        <span className="vs-demo__opt is-right">16</span>
                        <span className="vs-demo__opt">12</span>
                    </div>
                    <span className="vs-demo__clock">0:08</span>
                </div>
            );
        default:
            return null;
    }
}