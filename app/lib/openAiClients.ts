import { AzureOpenAI } from "openai";

let _completionsClient: AzureOpenAI | null = null;
let _embeddingsClient: AzureOpenAI | null = null;

/**
 * Get the singleton AzureOpenAI client configured for completions.
 */
export function getCompletionsClient(): AzureOpenAI {
  if (_completionsClient) return _completionsClient;

  const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
  const apiKey = process.env.AZURE_OPENAI_API_KEY;
  const apiVersion = process.env.AZURE_OPENAI_API_VERSION;
  const deploymentName = process.env.AZURE_OPENAI_DEPLOYMENT_NAME;

  if (!endpoint || !apiKey || !apiVersion || !deploymentName) {
    throw new Error(
      "Missing Azure OpenAI completions config. " +
        "Ensure AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, " +
        "AZURE_OPENAI_API_VERSION and " +
        "AZURE_OPENAI_DEPLOYMENT_NAME are set.",
    );
  }

  _completionsClient = new AzureOpenAI({
    endpoint,
    apiKey,
    apiVersion,
    deployment: deploymentName,
  });

  return _completionsClient;
}

/**
 * Get the singleton AzureOpenAI client configured for embeddings.
 */
export function getEmbeddingsClient(): AzureOpenAI {
  if (_embeddingsClient) return _embeddingsClient;

  const endpoint = process.env.AZURE_OPENAI_EMBEDDING_ENDPOINT;
  const apiKey = process.env.AZURE_OPENAI_EMBEDDING_API_KEY;
  const apiVersion = process.env.AZURE_OPENAI_EMBEDDING_API_VERSION;
  const deploymentName = process.env.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME;

  if (!endpoint || !apiKey || !apiVersion || !deploymentName) {
    throw new Error(
      "Missing Azure OpenAI embeddings config. " +
        "Ensure AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, " +
        "AZURE_OPENAI_EMBEDDING_API_VERSION and " +
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME are set.",
    );
  }

  _embeddingsClient = new AzureOpenAI({
    endpoint,
    apiKey,
    apiVersion,
    deployment: deploymentName,
  });

  return _embeddingsClient;
}
