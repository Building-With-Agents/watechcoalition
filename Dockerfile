# Use the official Node.js 18 image as the base image
FROM node:18

# Install git
RUN apt-get update && apt-get install -y git

# Set the working directory inside the container
WORKDIR /app

# Build arguments for GitHub credentials
ARG GITHUB_USER
ARG GITHUB_TOKEN

# Clone the repository using the credentials
RUN git clone https://$GITHUB_USER:$GITHUB_TOKEN@github.com:runefather/frontend-cfa.git .

# Install dependencies
RUN npm install

# Build the Next.js application
RUN npm run build

# Expose port 3000 to the host machine
EXPOSE 3000

# Command to run the application
CMD ["npm", "start"]