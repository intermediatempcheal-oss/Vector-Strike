import {
    AsYouType,
    CountryCode,
    getCountries,
    getCountryCallingCode,
    isValidPhoneNumber,
    parsePhoneNumberFromString,
} from 'libphonenumber-js';

export interface CountryOption {
    code: string;
    name: string;
    dial: string;
}

const COUNTRY_NAMES: Record<string, string> = {
    US: 'United States',
    GB: 'United Kingdom',
    CA: 'Canada',
    AU: 'Australia',
    IN: 'India',
    NG: 'Nigeria',
    KE: 'Kenya',
    ZA: 'South Africa',
    GH: 'Ghana',
    DE: 'Germany',
    FR: 'France',
    ES: 'Spain',
    IT: 'Italy',
    NL: 'Netherlands',
    BR: 'Brazil',
    MX: 'Mexico',
    AR: 'Argentina',
    PH: 'Philippines',
    MY: 'Malaysia',
    SG: 'Singapore',
    ID: 'Indonesia',
    TH: 'Thailand',
    VN: 'Vietnam',
    JP: 'Japan',
    KR: 'South Korea',
    CN: 'China',
    PK: 'Pakistan',
    BD: 'Bangladesh',
    AE: 'United Arab Emirates',
    SA: 'Saudi Arabia',
    TR: 'Türkiye',
    EG: 'Egypt',
    RU: 'Russia',
    UA: 'Ukraine',
    PL: 'Poland',
    SE: 'Sweden',
    NO: 'Norway',
    DK: 'Denmark',
    FI: 'Finland',
    IE: 'Ireland',
    NZ: 'New Zealand',
};

export const COUNTRIES: CountryOption[] = getCountries()
    .map<CountryOption>((code) => ({
        code,
        name: COUNTRY_NAMES[code] ?? code,
        dial: `+${getCountryCallingCode(code as CountryCode)}`,
    }))
    .sort((a, b) => a.name.localeCompare(b.name))
    .filter((c) => c.name !== c.code || c.code === 'US');

export function formatAsTyped(input: string, country?: string): string {
    if (!input) return '';
    try {
        const asYouType = new AsYouType((country as CountryCode) || undefined);
        return asYouType.input(input) || input;
    } catch {
        return input;
    }
}

export function isValidInternationalPhone(input: string): boolean {
    if (!input) return false;
    try {
        return isValidPhoneNumber(input);
    } catch {
        return false;
    }
}

export function parseToE164(input: string, defaultCountry?: string): string | null {
    if (!input) return null;
    try {
        const parsed = parsePhoneNumberFromString(
            input,
            defaultCountry ? (defaultCountry as CountryCode) : undefined
        );
        return parsed?.isValid() ? parsed.number : null;
    } catch {
        return null;
    }
}

export function inferCountry(input: string): string | null {
    const cleaned = input.replace(/[^\d+]/g, '');
    if (!cleaned.startsWith('+')) return null;
    for (const c of COUNTRIES) {
        if (cleaned.startsWith(c.dial)) return c.code;
    }
    return null;
}