import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppChrome from '../components/hub/AppChrome';
import { SectionHead } from '../components/hub/HubBits';
import Button from '../components/Button';
import Icon from '../components/Icon';
import { useAuthStore } from '../store/auth';

export default function AccountPage() {
    const navigate = useNavigate();
    const { user, logout } = useAuthStore();
    const [signingOut, setSigningOut] = useState(false);

    async function handleLogout() {
        setSigningOut(true);
        await logout();
        navigate('/login', { replace: true });
    }

    return (
        <AppChrome active="account">
            <main className="vs-hub__main">
                <SectionHead icon="shield" title="Account & Security" subtitle="Your account details, straight from the backend." />
                <section className="vs-settings__sec">
                    <div className="vs-settings__rows">
                        <SettingRow label="Name" value={user?.full_name ?? '—'} />
                        <SettingRow label="Username" value={user?.username ?? '—'} />
                        <SettingRow label="Email" value={user?.email ?? '—'} />
                        <SettingRow label="Phone" value={user?.phone ?? '—'} />
                        <SettingRow label="Vector ID" value={user?.vector_id ?? '—'} />
                        <SettingRow label="Account status" value={user?.account_status ?? '—'} />
                        <SettingRow label="Verification" value={user?.verification_status ?? 'pending'} />
                        <SettingRow label="Date of birth" value={user?.date_of_birth ? String(user.date_of_birth) : '—'} />
                        <SettingRow label="Onboarding" value={user?.onboarding_completed ? 'Complete' : 'Incomplete'} />
                    </div>
                    <p className="vs-account__reality">
                        <Icon name="shield" size={14} />
                        Authorization is always owned by the backend. React never decides ownership or access.
                    </p>
                    <div className="vs-account__actions">
                        <Button variant="outline" size="md" icon="lock" onClick={() => navigate('/forgot-password')}>
                            Reset password
                        </Button>
                        <Button variant="danger" size="md" icon="logout" loading={signingOut} onClick={() => void handleLogout()}>
                            Sign out of this device
                        </Button>
                    </div>
                </section>
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