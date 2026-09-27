export const USERNAME_RE = /^[A-Za-z0-9._]{3,30}$/;
export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const RESERVED = new Set([
    'vector',
    'vectorstrike',
    'vs',
    'admin',
    'administrator',
    'system',
    'support',
    'moderator',
    'staff',
    'root',
    'help',
    'official',
    'team',
    'guest',
]);

export interface UsernameValidation {
    valid: boolean;
    reason: string | null;
}

export function validateUsername(value: string): UsernameValidation {
    const v = (value ?? '').trim();
    if (!v) {
        return { valid: false, reason: 'Choose a username.' };
    }
    if (!USERNAME_RE.test(v)) {
        return {
            valid: false,
            reason: 'Use 3–30 characters: letters, numbers, periods or underscores.',
        };
    }
    const lower = v.toLowerCase().replace(/^[._]+|[._]+$/g, '');
    if (RESERVED.has(lower)) {
        return { valid: false, reason: 'That username is reserved and cannot be used.' };
    }
    return { valid: true, reason: null };
}

export function validateEmail(value: string): boolean {
    return EMAIL_RE.test((value ?? '').trim());
}

export function isFutureDate(iso: string): boolean {
    if (!iso) return false;
    const chosen = new Date(`${iso}T00:00:00`);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return chosen.getTime() > today.getTime();
}

export function formatDateForInput(date: Date): string {
    const y = date.getFullYear();
    const m = `${date.getMonth() + 1}`.padStart(2, '0');
    const d = `${date.getDate()}`.padStart(2, '0');
    return `${y}-${m}-${d}`;
}

export function dateMax2026Plus(): string {
    return formatDateForInput(new Date());
}

export function ageFromBirthdate(iso: string): number {
    if (!iso) return -1;
    const dob = new Date(`${iso}T00:00:00`);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age -= 1;
    return age;
}