/**
 * Data type for AI Workforce contact form submissions.
 * Flat key-value pairs to match SharePoint column names.
 */
export type AiWorkforceContactDTO = Record<string, string>;

/**
 * Submits an AI Workforce contact form to the Logic Apps endpoint.
 *
 * @param {AiWorkforceContactDTO} data - Flattened payload representing the contact form.
 * @returns {Promise<{ success: boolean; status: number; data?: any; error?: string }>}
 */
export const submitAiWorkforceContact = async (
  data: AiWorkforceContactDTO,
): Promise<{
  success: boolean;
  status: number;
  data?: any;
  error?: string;
}> => {
  const endpoint = process.env.AI_DEV_ENDPOINT;
  if (!endpoint) {
    return { success: false, status: 500, error: "Server not configured" };
  }

  try {
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(15_000),
    });

    const raw = await resp.text().catch(() => "");
    let parsed: any = null;
    try {
      parsed = raw ? JSON.parse(raw) : null;
    } catch {}

    if (!resp.ok) {
      return {
        success: false,
        status: resp.status || 502,
        error: (raw || "Upstream failed").slice(0, 500),
      };
    }

    return { success: true, status: resp.status || 200, data: parsed ?? raw };
  } catch (e: any) {
    return {
      success: false,
      status: 500,
      error: e?.message ?? "Unknown error",
    };
  }
};
