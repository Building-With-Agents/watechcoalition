import "dotenv/config";
import { AzureOpenAI } from "openai";

// Loads .env.local by default when DOTENV_CONFIG_PATH is set.
// We intentionally do NOT print keys/secrets.

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

async function main() {
  const chatEndpoint = requireEnv("AZURE_OPENAI_ENDPOINT");
  const chatApiKey = requireEnv("AZURE_OPENAI_API_KEY");
  const chatApiVersion = requireEnv("AZURE_OPENAI_API_VERSION");
  const chatDeployment = requireEnv("AZURE_OPENAI_DEPLOYMENT_NAME");

  const embEndpoint = requireEnv("AZURE_OPENAI_EMBEDDING_ENDPOINT");
  const embApiKey = requireEnv("AZURE_OPENAI_EMBEDDING_API_KEY");
  const embApiVersion = requireEnv("AZURE_OPENAI_EMBEDDING_API_VERSION");
  const embDeployment = requireEnv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME");

  const emb = new AzureOpenAI({
    endpoint: embEndpoint,
    apiKey: embApiKey,
    apiVersion: embApiVersion,
    deployment: embDeployment,
  });

  const embResp = await emb.embeddings.create({
    model: embDeployment,
    input: "hello world",
    dimensions: 1536,
  });

  console.log("embeddings_ok", embResp.data?.[0]?.embedding?.length);

  const chat = new AzureOpenAI({
    endpoint: chatEndpoint,
    apiKey: chatApiKey,
    apiVersion: chatApiVersion,
    deployment: chatDeployment,
  });

  const chatResp = await chat.chat.completions.create({
    model: chatDeployment,
    messages: [{ role: "user", content: "Say OK" }],
    max_completion_tokens: 20,
  });

  console.log("chat_ok", chatResp.choices?.[0]?.message?.content?.trim());
}

await main();

