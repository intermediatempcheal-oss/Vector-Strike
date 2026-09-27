import { useEffect, useState } from 'react';
import AppChrome from '../components/hub/AppChrome';
import { EmptyState, SectionHead, formatDate } from '../components/hub/HubBits';
import Icon, { IconName } from '../components/Icon';
import { useAppStore } from '../store/app';
import { Achievement } from '../types/home';

const ACHIEVEMENT_ICONS: Record<string, IconName> = {
    gamepad: 'gamepad',
    puzzle: 'puzzle',
    bolt: 'bolt',
    rocket: 'rocket',
    compass: 'compass',
    star: 'star',
    shield: 'shield',
    brain: 'brain',
};

export default function AchievementsPage() {
    const feed = useAppStore((s) => s.feed);
    const loading = useAppStore((s) => s.loading);
    const [retry, setRetry] = useState(0);

    useEffect(() => {
        if (!useAppStore.getState().feed) {
            void useAppStore.getState().ensure().catch(() => undefined);
        }
    }, [retry]);

    const achievements: Achievement[] = feed?.achievements ?? [];

    return (
        <AppChrome active="achievements">
            <main className="vs-hub__main">
                <SectionHead
                    icon="star"
                    title="Achievements"
                    subtitle={`${achievements.length} unlocked · earned only from verified play`}
                />
                {loading && !feed ? (
                    <div className="vs-page-skel">
                        <div className="vs-page-skel__item" />
                        <div className="vs-page-skel__item" />
                        <div className="vs-page-skel__item" />
                    </div>
                ) : !feed ? (
                    <EmptyState
                        icon="alert"
                        title="Couldn't load achievements"
                        body="Something went wrong while loading your achievements."
                        action={{ label: 'Retry', onClick: () => setRetry((r) => r + 1) }}
                    />
                ) : achievements.length === 0 ? (
                    <EmptyState
                        icon="star"
                        title="Your first achievement is waiting."
                        body="Complete games, keep streaks and explore new categories to unlock badges."
                    />
                ) : (
                    <div className="vs-hub__achgrid">
                        {achievements.map((a) => (
                            <AchievementCard key={a.slug} ach={a} />
                        ))}
                    </div>
                )}
            </main>
        </AppChrome>
    );
}

function AchievementCard({ ach }: { ach: Achievement }) {
    const icon = ACHIEVEMENT_ICONS[ach.icon] ?? 'star';
    return (
        <div className="vs-hub__ach">
            <span className="vs-hub__achicon">
                <Icon name={icon} size={22} />
            </span>
            <div>
                <b>{ach.title}</b>
                <p>{ach.description}</p>
                <small>Unlocked {formatDate(ach.earned_at)}</small>
            </div>
        </div>
    );
}