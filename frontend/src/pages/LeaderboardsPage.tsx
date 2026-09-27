import AppChrome from '../components/hub/AppChrome';
import { EmptyState, SectionHead } from '../components/hub/HubBits';

export default function LeaderboardsPage() {
    return (
        <AppChrome active="leaderboards">
            <main className="vs-hub__main">
                <SectionHead
                    icon="trophy"
                    title="Leaderboards"
                    subtitle="Verified rankings from real, completed runs only."
                />
                <EmptyState
                    icon="trophy"
                    title="No rankings yet"
                    body="Standings are built exclusively from verified backend runs. As members complete eligible games, real rankings will appear here — no fake scores, ever."
                />
            </main>
        </AppChrome>
    );
}