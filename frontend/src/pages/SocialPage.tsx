import AppChrome from '../components/hub/AppChrome';
import { EmptyState, SectionHead } from '../components/hub/HubBits';

export default function SocialPage() {
    return (
        <AppChrome active="social">
            <main className="vs-hub__main">
                <SectionHead
                    icon="users"
                    title="Social"
                    subtitle="Discover players, follow friends and share the grid."
                />
                <EmptyState
                    icon="users"
                    title="Discover players"
                    body="Player discovery is backend-controlled. Profiles, follows and activity will appear here once the social graph is enabled — with real privacy rules enforced server-side."
                />
            </main>
        </AppChrome>
    );
}