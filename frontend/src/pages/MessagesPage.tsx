import AppChrome from '../components/hub/AppChrome';
import { EmptyState, SectionHead } from '../components/hub/HubBits';

export default function MessagesPage() {
    return (
        <AppChrome active="messages">
            <main className="vs-hub__main">
                <SectionHead
                    icon="message"
                    title="Messages"
                    subtitle="Direct conversations with players you've connected with."
                />
                <EmptyState
                    icon="message"
                    title="No conversations yet"
                    body="When players connect with you, their conversations will appear here. Messages require a real verified connection."
                />
            </main>
        </AppChrome>
    );
}