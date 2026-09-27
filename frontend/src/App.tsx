import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import SplashPage from './pages/SplashPage';
import AuthChoicePage from './pages/AuthChoicePage';
import LoginPage from './pages/LoginPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import HomePage from './pages/HomePage';
import GameHubPage from './pages/GameHubPage';
import GameDetailPage from './pages/GameDetailPage';
import GamePlayPage from './pages/GamePlayPage';
import GameResultPage from './pages/GameResultPage';
import NotificationsPage from './pages/NotificationsPage';
import MessagesPage from './pages/MessagesPage';
import SocialPage from './pages/SocialPage';
import LeaderboardsPage from './pages/LeaderboardsPage';
import TournamentsPage from './pages/TournamentsPage';
import MissionsPage from './pages/MissionsPage';
import AchievementsPage from './pages/AchievementsPage';
import ProfilePage from './pages/ProfilePage';
import ProgressPage from './pages/ProgressPage';
import PremiumPage from './pages/PremiumPage';
import SettingsPage from './pages/SettingsPage';
import AccountPage from './pages/AccountPage';
import { ChallengesPage } from './pages/PlatformPages';
import WelcomeStep from './pages/onboarding/WelcomeStep';
import AgeStep from './pages/onboarding/AgeStep';
import InterestsStep from './pages/onboarding/InterestsStep';
import PlayStyleStep from './pages/onboarding/PlayStyleStep';
import ProfileStep from './pages/onboarding/ProfileStep';
import GuardianStep from './pages/onboarding/GuardianStep';
import VerificationStep from './pages/onboarding/VerificationStep';
import TermsStep from './pages/onboarding/TermsStep';
import CreatingStep from './pages/onboarding/CreatingStep';
import CompleteStep from './pages/onboarding/CompleteStep';
import { OnboardingGuard, RequireAuth } from './routes/guards';

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<SplashPage />} />
                <Route path="/landing" element={<LandingPage />} />
                <Route path="/splash" element={<SplashPage />} />
                <Route path="/auth-choice" element={<AuthChoicePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/verify-email" element={<VerifyEmailPage />} />

                <Route
                    path="/onboarding/:step"
                    element={
                        <OnboardingGuard>
                            <OnboardingStepSwitch />
                        </OnboardingGuard>
                    }
                />

                <Route
                    path="/home"
                    element={
                        <RequireAuth>
                            <HomePage />
                        </RequireAuth>
                    }
                />

                <Route
                    path="/game-hub"
                    element={
                        <RequireAuth>
                            <GameHubPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/game-hub/:ident"
                    element={
                        <RequireAuth>
                            <GameHubPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/challenges"
                    element={
                        <RequireAuth>
                            <ChallengesPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/leaderboards"
                    element={
                        <RequireAuth>
                            <LeaderboardsPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/tournaments"
                    element={
                        <RequireAuth>
                            <TournamentsPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/missions"
                    element={
                        <RequireAuth>
                            <MissionsPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/social"
                    element={
                        <RequireAuth>
                            <SocialPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/messages"
                    element={
                        <RequireAuth>
                            <MessagesPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/notifications"
                    element={
                        <RequireAuth>
                            <NotificationsPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/achievements"
                    element={
                        <RequireAuth>
                            <AchievementsPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/profile"
                    element={
                        <RequireAuth>
                            <ProfilePage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/progress"
                    element={
                        <RequireAuth>
                            <ProgressPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/premium"
                    element={
                        <RequireAuth>
                            <PremiumPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/settings"
                    element={
                        <RequireAuth>
                            <SettingsPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/account"
                    element={
                        <RequireAuth>
                            <AccountPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/games/:slug"
                    element={
                        <RequireAuth>
                            <GameDetailPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/games/:slug/play"
                    element={
                        <RequireAuth>
                            <GamePlayPage />
                        </RequireAuth>
                    }
                />
                <Route
                    path="/games/:slug/result"
                    element={
                        <RequireAuth>
                            <GameResultPage />
                        </RequireAuth>
                    }
                />

                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    );
}

function OnboardingStepSwitch() {
    const { step } = useParams<{ step: string }>();
    if (!step) return <Navigate to="/onboarding/welcome" replace />;
    switch (step) {
        case 'welcome':
            return <WelcomeStep />;
        case 'age':
            return <AgeStep />;
        case 'interests':
            return <InterestsStep />;
        case 'play-style':
            return <PlayStyleStep />;
        case 'profile':
            return <ProfileStep />;
        case 'guardian':
            return <GuardianStep />;
        case 'verification':
            return <VerificationStep />;
        case 'terms':
            return <TermsStep />;
        case 'creating':
            return <CreatingStep />;
        case 'complete':
            return <CompleteStep />;
        default:
            return <Navigate to="/onboarding/welcome" replace />;
    }
}