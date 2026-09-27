import { request } from './api';
import {
    CatalogPage,
    CategoryPage,
    GameDetail,
    GameSessionState,
    HubFeed,
    HubSearchResult,
    RunReport,
    StartSessionPayload,
} from '../types/hub';

async function unwrap<T>(res: Awaited<ReturnType<typeof request<T>>>): Promise<T> {
    if (!res.ok || !res.data) {
        const err = new Error(res.error?.message ?? 'Request failed') as Error & {
            code: string;
            status: number;
        };
        err.code = res.error?.code ?? 'error';
        err.status = res.status;
        throw err;
    }
    return res.data;
}

export async function fetchHub(): Promise<HubFeed> {
    return unwrap<HubFeed>(await request<HubFeed>('/hub/', { skipCsrf: true }));
}

export async function fetchHubCategories(): Promise<HubFeed['categories']> {
    const body = await unwrap<{ categories: HubFeed['categories'] }>(
        await request('/hub/categories/', { skipCsrf: true })
    );
    return body.categories;
}

export async function fetchHubCategory(ident: string, page = 1): Promise<CategoryPage> {
    const params = new URLSearchParams({ page: String(page) });
    return unwrap<CategoryPage>(
        await request(`/hub/categories/${encodeURIComponent(ident)}/?${params}`, { skipCsrf: true })
    );
}

export interface CatalogParams {
    q?: string;
    category?: string;
    difficulty?: string;
    game_type?: string;
    min_duration?: string;
    max_duration?: string;
    featured?: boolean;
    new?: boolean;
    sort?: 'release' | 'title' | 'difficulty' | 'duration';
    page?: number;
    page_size?: number;
}

export async function fetchCatalog(params: CatalogParams = {}): Promise<CatalogPage> {
    const query = new URLSearchParams();
    const pairs: Array<[string, string | number | undefined | boolean]> = [
        ['q', params.q],
        ['category', params.category],
        ['difficulty', params.difficulty],
        ['game_type', params.game_type],
        ['min_duration', params.min_duration],
        ['max_duration', params.max_duration],
        ['featured', params.featured ? '1' : undefined],
        ['new', params.new ? '1' : undefined],
        ['sort', params.sort],
        ['page', params.page],
        ['page_size', params.page_size],
    ];
    for (const [key, value] of pairs) {
        if (value !== undefined && value !== '' && value !== false) {
            query.set(key, String(value));
        }
    }
    const qs = query.toString();
    return unwrap<CatalogPage>(
        await request(`/hub/games/${qs ? `?${qs}` : ''}`, { skipCsrf: true })
    );
}

export async function fetchGameDetail(slug: string): Promise<GameDetail> {
    return unwrap<GameDetail>(
        await request(`/hub/games/${encodeURIComponent(slug)}/`, { skipCsrf: true })
    );
}

export async function startSession(slug: string): Promise<StartSessionPayload> {
    return unwrap<StartSessionPayload>(
        await request(`/hub/games/${encodeURIComponent(slug)}/sessions/`, {
            method: 'POST',
            skipCsrf: true,
        })
    );
}

export async function completeSession(id: string, report: RunReport): Promise<GameSessionState> {
    return unwrap<GameSessionState>(
        await request(`/hub/sessions/${encodeURIComponent(id)}/complete/`, {
            method: 'POST',
            body: report,
            skipCsrf: true,
        })
    );
}

export async function searchHub(q: string): Promise<HubSearchResult> {
    const params = new URLSearchParams({ q });
    return unwrap<HubSearchResult>(
        await request(`/hub/search/?${params}`, { skipCsrf: true })
    );
}