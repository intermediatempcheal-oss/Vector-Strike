import AppChrome from '../components/hub/AppChrome';
import { EmptyState, SectionHead } from '../components/hub/HubBits';

export default function NotificationsPage() {
    return (
        <AppChrome active="notifications">
            <main className="vs-hub__main">
                <SectionHead
                    icon="bell"
                    title="Notifications"
                    subtitle="Your activity, challenge and security updates."
                />
                <EmptyState
                    icon="bell"
                    title="You're all caught up"
                    body="Achievements, challenge updates and security alerts will appear here as they happen. Nothing is fabricated."
                />
            </main>
        </AppChrome>
    );
}