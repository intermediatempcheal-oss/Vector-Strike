import AppChrome from '../components/hub/AppChrome';
import { SectionHead } from '../components/hub/HubBits';
import Icon from '../components/Icon';
import { useAuthStore } from '../store/auth';

const GROUPS: Array<{ icon: 'user' | 'shield' | 'bell' | 'globe' | 'eye'; title: string; hint: string }> = [
    { icon: 'user', title: 'Account', hint: 'Username, email and contact details.' },
    { icon: 'shield', title: 'Security', hint: 'Password, verification and active sessions.' },
    { icon: 'bell', title: 'Notifications', hint: 'Choose what reaches your inbox.' },
    { icon: 'globe', title: 'Privacy', hint: 'Who can see your profile and activity.' },
    { icon: 'eye', title: 'Appearance', hint: 'Theme and accessibility preferences.' },
];

export default function SettingsPage() {
    const { user } = useAuthStore();

    return (
        <AppChrome active="settings">
            <main className="vs-hub__main">
                <SectionHead
                    icon="settings"
                    title="Settings"
                    subtitle="Preferences are owned by the backend — edits here save server-side when the endpoint is available."
                />
                <div className="vs-settings">
                    <section className="vs-settings__sec">
                        <div className="vs-settings__reality">
                            <Icon name="user" size={16} />
                            Live from your session:
                        </div>
                        <div className="vs-settings__rows">
                            <SettingRow label="Username" value={user?.username ?? '—'} />
                            <SettingRow label="Email" value={user?.email ?? '—'} />
                            <SettingRow label="Phone" value={user?.phone ?? '—'} />
                            <SettingRow label="Vector ID" value={user?.vector_id ?? '—'} />
                            <SettingRow label="Region" value={user?.region ? user.region.toUpperCase() : '—'} />
                            <SettingRow label="Age group" value={user?.age_group || '—'} />
                            <SettingRow label="Verification" value={user?.verification_status ?? 'pending'} />
                        </div>
                    </section>

                    <div className="vs-settings__groups">
                        {GROUPS.map((g) => (
                            <button key={g.title} className="vs-settings__group" disabled>
                                <span className="vs-settings__groupicon">
                                    <Icon name={g.icon} size={18} />
                                </span>
                                <span>
                                    <b>{g.title}</b>
                                    <small>{g.hint}</small>
                                </span>
                                <span className="vs-settings__soon">Soon</span>
                            </button>
                        ))}
                    </div>
                </div>
            </main>
        </AppChrome>
    );
}

function SettingRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="vs-settings__row">
            <span>{label}</span>
            <b>{value}</b>
        </div>
    );
}