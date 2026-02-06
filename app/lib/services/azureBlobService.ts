import {
  BlobSASPermissions,
  BlobServiceClient,
  BlockBlobClient,
  generateBlobSASQueryParameters,
  SASProtocol,
  StorageSharedKeyCredential,
} from "@azure/storage-blob";
import { devLog } from "@/app/lib/utils";

const connectionString = process.env.AZURE_STORAGE_CONNECTION_STRING!;
const blobServiceClient =
  BlobServiceClient.fromConnectionString(connectionString);

const imageContainerName = "image-storage";
const pdfContainerName = "resume-storage";
const docFileExtensionsAllowed = [".pdf"];
const imagFileExtensionsAllowed = [
  ".svg",
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".webp",
];

// Enum to define possible prefixes for different types of files
export enum BlobPrefix {
  Avatar = "avatar",
  Resume = "resume",
  CoverLetter = "coverLetter",
  DevPlan = "careerPrepDevPlan",
  EduProviderLogo = "eduProviderLogo",
  Project = "project",
}

// Needed to map the correct content-type property based on file extension
const contentTypeMap: { [key: string]: string } = {
  // doc content-types
  ".pdf": "application/pdf",
  ".doc": "application/msword",
  ".docx":
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ".txt": "text/plain",
  ".rtf": "application/rtf",
  // image content-types
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
};

// Upload resume method using the generalized uploadFile function with SAS token
export async function uploadResume(
  file: Buffer,
  fileName: string,
  userId: string,
): Promise<string> {
  return await uploadFile(
    file,
    fileName,
    userId,
    BlobPrefix.Resume,
    docFileExtensionsAllowed,
    pdfContainerName,
    true,
  );
}

// Upload Professional Development Plan method using the generalized uploadFile function with SAS token
export async function uploadDevPlan(
  file: Buffer,
  fileName: string,
  userId: string,
): Promise<string> {
  return await uploadFile(
    file,
    fileName,
    userId,
    BlobPrefix.DevPlan,
    docFileExtensionsAllowed,
    pdfContainerName,
    true,
  );
}

// Upload cover letter method using the generalized uploadFile function with SAS token
export async function uploadCoverLetter(
  file: Buffer,
  fileName: string,
  userId: string,
): Promise<string> {
  return await uploadFile(
    file,
    fileName,
    userId,
    BlobPrefix.CoverLetter,
    docFileExtensionsAllowed,
    pdfContainerName,
    true,
  );
}

// Method to get a link to the resume with a SAS token
export async function getResumeUrl(userId: string): Promise<string | null> {
  if (userId.length < 1) return null;
  const blobPrefix = `${userId}/${BlobPrefix.Resume}`; // Common prefix for resumes
  return await getBlobUrlWithSas(pdfContainerName, blobPrefix);
}

// Method to get a link to the cover letter  with a SAS token
export async function getCoverLetterUrl(
  userId: string,
): Promise<string | null> {
  if (userId.length < 1) return null;
  const blobPrefix = `${userId}/${BlobPrefix.CoverLetter}`; // Common prefix for cover letters
  return await getBlobUrlWithSas(pdfContainerName, blobPrefix);
}

// Method to get a link to the Career Prep professional development plan with a SAS token
export async function getDevPlan(userId: string): Promise<string | null> {
  if (userId.length < 1) return null;
  const blobPrefix = `${userId}/${BlobPrefix.DevPlan}`; // Common prefix for resumes
  return await getBlobUrlWithSas(pdfContainerName, blobPrefix);
}

// Upload project image method using the generalized uploadFile function without SAS token
export async function uploadProjectImage(
  file: Buffer,
  fileName: string,
  userId: string,
  projectId: string,
): Promise<string> {
  return await uploadFile(
    file,
    fileName,
    `${userId}/${projectId}`,
    BlobPrefix.Project,
    imagFileExtensionsAllowed,
    imageContainerName,
    false,
  );
}

// Method to get a link to the avatar image without SAS token
export async function getProjectUrl(
  userId: string,
  projectId: string,
): Promise<string | null> {
  const blobPrefix = `${userId}/${projectId}/${BlobPrefix.Project}`; // Common prefix for projects
  return await getBlobUrl(imageContainerName, blobPrefix);
}

// Upload avatar method using the generalized uploadFile function without SAS token
export async function uploadAvatar(
  file: Buffer,
  fileName: string,
  userId: string,
): Promise<string> {
  return await uploadFile(
    file,
    fileName,
    userId,
    BlobPrefix.Avatar,
    imagFileExtensionsAllowed,
    imageContainerName,
    false,
  );
}

// Method to get a link to the avatar image without SAS token
export async function getAvatarUrl(userId: string): Promise<string | null> {
  const blobPrefix = `${userId}/${BlobPrefix.Avatar}`; // Common prefix for avatars
  return await getBlobUrl(imageContainerName, blobPrefix);
}

// Upload training provider logo method using the generalized uploadFile function without SAS token
export async function uploadEduProviderLogo(
  file: Buffer,
  fileName: string,
  eduProviderId: string,
): Promise<string> {
  return await uploadFile(
    file,
    fileName,
    eduProviderId,
    BlobPrefix.EduProviderLogo,
    imagFileExtensionsAllowed,
    imageContainerName,
    false,
  );
}

// Method to get a link to the edu provider logo without SAS token
export async function getEduProviderLogo(
  trainingProviderId: string,
): Promise<string | null> {
  const blobPrefix = `${trainingProviderId}/${BlobPrefix.EduProviderLogo}`; // Common prefix for avatars
  return await getBlobUrl(imageContainerName, blobPrefix);
}

// Delete existing blobs with the same prefix to avoid storing multiple files with different file extensions.
async function deleteExistingBlobs(containerName: string, prefix: string) {
  const containerClient = blobServiceClient.getContainerClient(containerName);

  // List blobs with the given prefix
  for await (const blob of containerClient.listBlobsFlat({ prefix })) {
    const blockBlobClient = containerClient.getBlockBlobClient(blob.name);
    await blockBlobClient.deleteIfExists();
  }
}

// Generalized Method to upload a file to Azure Blob Storage
async function uploadFile(
  file: Buffer,
  fileName: string,
  userId: string,
  prefix: BlobPrefix,
  allowedExtensions: string[],
  containerName: string,
  attachSasToken: boolean,
): Promise<string> {
  const fileExtension = fileName
    .substring(fileName.lastIndexOf("."))
    .toLowerCase();

  // Check if the file extension is allowed
  if (!allowedExtensions.includes(fileExtension)) {
    throw new Error(`Unsupported file type: ${fileExtension}`);
  }

  // Get the content type based on the file extension
  const contentType = contentTypeMap[fileExtension];
  const blobName = `${userId}/${prefix}${fileExtension}`; // Use a unique identifier for the filename

  // Delete any existing files with the same prefix
  await deleteExistingBlobs(containerName, `${userId}/${prefix}`);

  const blockBlobClient = getBlockBlobClient(containerName, blobName);

  try {
    // Upload the file with the appropriate content type
    await blockBlobClient.uploadData(file, {
      blobHTTPHeaders: {
        blobContentType: contentType, // Set the content type for the file
      },
    });

    // Attach SAS token for resume URLs
    if (attachSasToken) {
      const sasToken = generateBlobSasToken(containerName, blobName);
      return `${blockBlobClient.url}?${sasToken}`; // Return the URL of the uploaded file with SAS token
    } else {
      return blockBlobClient.url; // Return the URL of the uploaded file without SAS token
    }
  } catch (error) {
    console.error("Error uploading file:", error);
    throw new Error("Failed to upload file");
  }
}

// Method to get a BlockBlobClient for a specific container and blob name
function getBlockBlobClient(
  containerName: string,
  blobName: string,
): BlockBlobClient {
  const containerClient = blobServiceClient.getContainerClient(containerName);
  return containerClient.getBlockBlobClient(blobName);
}

// Generalized Method to get the URL of a blob with a SAS token
async function getBlobUrlWithSas(
  containerName: string,
  blobPrefix: string,
): Promise<string | null> {
  const containerClient = blobServiceClient.getContainerClient(containerName);

  // List blobs in the container and filter by the expected prefix
  try {
    for await (const blob of containerClient.listBlobsFlat({
      prefix: blobPrefix,
    })) {
      // If a matching blob is found, return the URL
      const blockBlobClient = containerClient.getBlockBlobClient(blob.name);
      const sasToken = generateBlobSasToken(containerName, blob.name);
      // Check if the blockBlobClient.url already contains a '?' and append accordingly
      const separator = blockBlobClient.url.includes("?") ? "&" : "?";
      return `${blockBlobClient.url}${separator}${sasToken}`; // Return the full URL of the blob with SAS token
    }

    // If no matching blob is found, return null or handle accordingly
    return null;
  } catch (error) {
    console.error("Error retrieving blob link:", error);
    throw new Error("Failed to retrieve blob link");
  }
}

// Generalized Method to get the URL of a blob without a SAS token
async function getBlobUrl(
  containerName: string,
  blobPrefix: string,
): Promise<string | null> {
  const containerClient = blobServiceClient.getContainerClient(containerName);

  // List blobs in the container and filter by the expected prefix
  try {
    for await (const blob of containerClient.listBlobsFlat({
      prefix: blobPrefix,
    })) {
      // If a matching blob is found, return the URL
      const blockBlobClient = containerClient.getBlockBlobClient(blob.name);
      return blockBlobClient.url; // Return the URL of the blob without SAS token
    }

    return null;
  } catch (error) {
    console.error("Error retrieving blob url:", error);
    throw new Error("Failed to retrieve blob url");
  }
}

function generateBlobSasToken(containerName: string, blobName: string): string {
  const accountName = process.env.AZURE_STORAGE_ACCOUNT_NAME!;
  const accountKey = process.env.AZURE_STORAGE_ACCOUNT_KEY!;
  const sharedKeyCredential = new StorageSharedKeyCredential(
    accountName,
    accountKey,
  );

  const startsOn = new Date(
    new Date(Date.now() - 15 * 60 * 1000).toISOString().split(".")[0] + "Z",
  );
  const expiresOn = new Date(
    new Date(Date.now() + 15 * 60 * 1000).toISOString().split(".")[0] + "Z",
  );

  const sasOptions = {
    containerName,
    blobName,
    permissions: BlobSASPermissions.parse("r"), // Read-only permissions for a blob
    startsOn: startsOn,
    expiresOn: expiresOn,
    protocol: SASProtocol.Https, // HTTPS only
    resource: "b",
    version: "2022-11-02", // Set the service version to match Azure
  };

  // Generate SAS token
  const sasToken = generateBlobSASQueryParameters(
    sasOptions,
    sharedKeyCredential,
  ).toString();

  devLog("Generated SAS Token:", sasToken);
  return sasToken;
}
