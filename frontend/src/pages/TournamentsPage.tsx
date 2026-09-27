import AppChrome from '../components/hub/AppChrome';
import { EmptyState, SectionHead } from '../components/hub/HubBits';

export default function TournamentsPage() {
    return (
        <AppChrome active="tournaments">
            <main className="vs-hub__main">
                <SectionHead
                    icon="medal"
                    title="Tournaments"
                    subtitle="Structured competitions with backend-controlled eligibility."
                />
                <EmptyState
                    icon="medal"
                    title="No tournaments open"
                    body="Tournaments appear here when one is live. Entry, matches and standings are always owned and verified by the backend."
                />
            </main>
        </AppChrome>
    );
}