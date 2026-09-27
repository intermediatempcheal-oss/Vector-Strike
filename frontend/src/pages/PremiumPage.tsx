import AppChrome from '../components/hub/AppChrome';
import { SectionHead } from '../components/hub/HubBits';
import Button from '../components/Button';
import Icon from '../components/Icon';

const PLANS = [
    {
        name: 'Starter',
        price: 'Free',
        highlight: false,
        copy: 'Everything you need to start the journey.',
        perks: ['Full game catalog access', 'Unlimited verified runs', 'XP and rank tracking', 'All achievements'],
    },
    {
        name: 'Vector Plus',
        price: '₹149 / month',
        highlight: true,
        copy: 'For players who want the extra lane.',
        perks: [
            'All Starter benefits',
            'Early access to new drop games',
            'Advanced run analytics',
            'Priority tournament entry',
            'Premium badge on your profile',
        ],
    },
    {
        name: 'Apex Elite',
        price: '₹399 / month',
        highlight: false,
        copy: 'The top-of-the-podium tier.',
        perks: [
            'All Plus benefits',
            'Exclusive elite tournaments',
            'Personal run coach insights',
            'Custom avatar frame',
            'Annual standings showcase',
        ],
    },
];

export default function PremiumPage() {
    return (
        <AppChrome active="premium">
            <main className="vs-hub__main">
                <SectionHead
                    icon="rocket"
                    title="Premium"
                    subtitle="Plans and entitlements — powered by real backend subscription state."
                />
                <div className="vs-premium__note">
                    <Icon name="info" size={16} />
                    Payments are not enabled yet. Subscriptions and entitlements will be verified server-side before any premium access is granted — the frontend will never mark premium active on its own.
                </div>
                <div className="vs-premium__grid">
                    {PLANS.map((p) => (
                        <div key={p.name} className={`vs-premium__plan${p.highlight ? ' vs-premium__plan--hl' : ''}`}>
                            <h3>{p.name}</h3>
                            <b className="vs-premium__price">{p.price}</b>
                            <p>{p.copy}</p>
                            <ul>
                                {p.perks.map((f) => (
                                    <li key={f}>
                                        <Icon name="check" size={15} /> {f}
                                    </li>
                                ))}
                            </ul>
                            <Button variant={p.highlight ? 'primary' : 'outline'} size="md" fullWidth disabled>
                                {p.highlight ? 'Coming soon' : 'Free'}
                            </Button>
                        </div>
                    ))}
                </div>
            </main>
        </AppChrome>
    );
}