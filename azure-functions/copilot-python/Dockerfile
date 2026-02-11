FROM python:3.11-slim-bookworm

# Install Azure Functions Core Tools v4
# This image is intended for LOCAL DEVELOPMENT only.
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates gnupg apt-transport-https libicu72 \
  && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg \
  && echo "deb [arch=amd64] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/microsoft-prod.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends azure-functions-core-tools-4 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Safety net: if ICU is still unavailable for some reason, allow invariant globalization
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=0

WORKDIR /app

# Python dependencies for the function app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Function app code
COPY . .

EXPOSE 7071

CMD ["func", "start", "--host", "0.0.0.0", "--port", "7071", "--verbose"]

