import { useEffect, useState } from 'react';
import AppChrome from '../components/hub/AppChrome';
import { EmptyState, SectionHead } from '../components/hub/HubBits';
import Icon from '../components/Icon';
import { cn } from '../utils/cn';
import { useAppStore } from '../store/app';
import { Mission } from '../types/home';

export default function MissionsPage() {
    const feed = useAppStore((s) => s.feed);
    const loading = useAppStore((s) => s.loading);
    const [retry, setRetry] = useState(0);

    useEffect(() => {
        if (!useAppStore.getState().feed) {
            void useAppStore.getState().ensure().catch(() => undefined);
        }
    }, [retry]);

    if (loading && !feed) {
        return (
            <AppChrome active="missions">
                <main className="vs-hub__main">
                    <SectionHead icon="check" title="Missions" subtitle="Goals validated by the backend — never by React alone." />
                    <div className="vs-page-skel">
                        <div className="vs-page-skel__item" />
                        <div className="vs-page-skel__item" />
                        <div className="vs-page-skel__item" />
                    </div>
                </main>
            </AppChrome>
        );
    }

    const missions: Mission[] = feed?.missions ?? [];
    const done = missions.filter((m) => m.completed).length;

    return (
        <AppChrome active="missions">
            <main className="vs-hub__main">
                <SectionHead
                    icon="check"
                    title="Missions"
                    subtitle={`${done}/${missions.length} completed · progress is validated server-side`}
                />
                {!feed ? (
                    <EmptyState
                        icon="alert"
                        title="Couldn't load missions"
                        body="Something went wrong while loading your missions."
                        action={{ label: 'Retry', onClick: () => setRetry((r) => r + 1) }}
                    />
                ) : missions.length === 0 ? (
                    <EmptyState
                        icon="check"
                        title="No missions available"
                        body="Missions will appear here soon. Keep playing to unlock goals."
                    />
                ) : (
                    <div className="vs-hub__missions">
                        {missions.map((m) => (
                            <MissionCard key={m.slug} mission={m} />
                        ))}
                    </div>
                )}
            </main>
        </AppChrome>
    );
}

function MissionCard({ mission }: { mission: Mission }) {
    const pct = Math.min(100, Math.round((mission.progress / mission.target) * 100));
    return (
        <div className={cn('vs-hub__mission', mission.completed && 'vs-hub__mission--done')}>
            <span className="vs-hub__missionicon">
                <Icon name={mission.completed ? 'check' : 'target'} size={20} />
            </span>
            <div className="vs-hub__missionbody">
                <div className="vs-hub__missionhead">
                    <b>{mission.title}</b>
                    <span className="vs-hub__missionxp">+{mission.xp_reward} XP</span>
                </div>
                <p>{mission.description}</p>
                <div className="vs-hub__missionprogress">
                    <span className="vs-hub__bar">
                        <span className="vs-hub__barfill" style={{ width: `${pct}%` }} />
                    </span>
                    <small>{mission.completed ? 'Completed' : `${mission.progress} / ${mission.target}`}</small>
                </div>
            </div>
        </div>
    );
}