import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Button from '../../components/Button';
import Icon from '../../components/Icon';
import { useOnboardingStore } from '../../store/onboarding';
import { getInterestVisual } from '../../constants/interests';
import { OnboardingService } from '../../services/onboarding';
import { useAuthStore } from '../../store/auth';
import { SessionUser } from '../../types/auth';
import { GameCard } from '../../types/onboarding';

export default function CompleteStep() {
    const navigate = useNavigate();
    const registerResult = useOnboardingStore((s) => s.registerResult);
    const registeredUser = useOnboardingStore((s) => s.registeredUser);
    const applySession = useAuthStore((s) => s.applySession);

    const [recommendations, setRecommendations] = useState<GameCard[]>(
        registerResult?.recommendations ?? []
    );

    useEffect(() => {
        let alive = true;
        if (registerResult) {
            applySession({
                authenticated: true,
                onboarding_complete: true,
                user: buildUserFromResult(registerResult, registeredUser),
            });
        }
        OnboardingService.fetchFirstExperience()
            .then((data) => {
                if (!alive) return;
                setRecommendations(data.recommendations ?? []);
            })
            .catch(() => {
                /* fall back to register-time recommendations */
            });
        return () => {
            alive = false;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const user = useMemo(() => {
        if (registerResult) return buildUserFromResult(registerResult, registeredUser);
        return null;
    }, [registerResult, registeredUser]);

    const displayName = user?.full_name || user?.username || 'Player';
    const vectorId = user?.vector_id ?? '';
    const interests = registerResult?.interests ?? user?.interests ?? [];
    const profileAvatar = (user?.profile as { avatar?: string; avatar_url?: string } | null)?.avatar_url
        || (user?.profile as { avatar?: string; avatar_url?: string } | null)?.avatar
        || '';
    const initials = (displayName || 'P')
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0])
        .join('')
        .toUpperCase();

    return (
        <OnboardingLayout step="complete" showProgress={false}>
            <StepShell
                eyebrow="WELCOME TO THE GRID"
                title={`Welcome aboard, ${displayName}!`}
                subtitle={
                    <>
                        Your Vector ID is live. Here’s what your fresh arcade profile looks like —
                        you can fine-tune everything from your dashboard.
                    </>
                }
            >
                <div className="vs-complete">
                    <div className="vs-complete__idcard">
                        <span className="vs-complete__idlabel">YOUR VECTOR ID</span>
                        <span className="vs-complete__idcode">{vectorId}</span>
                        <span className="vs-complete__idmeta">
                            Status: <b>Active & verified</b> · Shown on your public profile only
                        </span>
                    </div>

                    <div className="vs-complete__interests">
                        <span className="vs-complete__col-label">Your tags</span>
                        <div className="vs-complete__chips">
                            {interests.map((slug) => (
                                <span key={slug} className="vs-capture-chip">
                                    <span
                                        className="vs-capture-chip__dot"
                                        style={{ background: getInterestVisual(slug).gradient }}
                                    />
                                    {slug}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className="vs-complete__recs">
                        <span className="vs-complete__col-label">Recommended first picks</span>
                        <div className="vs-complete__cardgrid">
                            {(recommendations.length ? recommendations : [])
                                .slice(0, 4)
                                .map((g) => (
                                    <div key={g.id} className="vs-reco">
                                        <div className="vs-reco__icon">
                                            <Icon name="gamepad" size={20} />
                                        </div>
                                        <div>
                                            <h4>{g.title}</h4>
                                            <p>{g.tagline}</p>
                                            <span className="vs-reco__why">{g.reason}</span>
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                </div>

                <div className="vs-complete__summary">
                    <div className="vs-complete__summarycard">
                        <div className="vs-complete__avatarwrap">
                            {profileAvatar ? (
                                <img src={profileAvatar} alt="Profile" className="vs-complete__avatar" />
                            ) : (
                                <span className="vs-complete__avatar vs-complete__avatar--fallback">{initials || 'VS'}</span>
                            )}
                        </div>
                        <div className="vs-complete__credentials">
                            <span className="vs-complete__label">Account snapshot</span>
                            <h3>{displayName}</h3>
                            <p>@{user?.username ?? 'pilot'}</p>
                            <p>{user?.email ?? 'email pending'}</p>
                            <p>{vectorId}</p>
                        </div>
                    </div>
                </div>

                <div className="vs-step__actions">
                    <Button size="xl" iconRight="arrow" onClick={() => navigate('/home', { replace: true })}>
                        Enter Vector Strike
                    </Button>
                    <span className="vs-complete__auto">
                        Opening your home in a few seconds —
                    </span>
                </div>
            </StepShell>
        </OnboardingLayout>
    );
}

function buildUserFromResult(
    res: NonNullable<ReturnType<typeof useOnboardingStore.getState>['registerResult']>,
    serverUser: SessionUser | null
): SessionUser {
    return {
        vector_id: res.vector_id,
        username: serverUser?.username ?? res.username,
        email: serverUser?.email ?? '',
        phone: serverUser?.phone ?? null,
        full_name: serverUser?.full_name ?? res.full_name,
        date_of_birth: serverUser?.date_of_birth ?? null,
        age_group: serverUser?.age_group ?? '',
        age: serverUser?.age ?? null,
        age_verified: serverUser?.age_verified ?? true,
        verification_status: serverUser?.verification_status ?? 'verified',
        account_status: serverUser?.account_status ?? 'active',
        onboarding_completed: serverUser?.onboarding_completed ?? true,
        region: serverUser?.region ?? '',
        profile: serverUser?.profile ?? null,
        interests: serverUser?.interests ?? res.interests,
        play_styles: serverUser?.play_styles ?? res.play_styles,
    };
}