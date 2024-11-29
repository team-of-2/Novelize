import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

export const invokeModel = async (payload) => {
  const command = new InvokeModelCommand({
    contentType: "application/json",
    body: JSON.stringify(payload),
    modelId: "anthropic.claude-3-sonnet-20240229-v1:0", // Replace with your model ID
  });

  try {
    const apiResponse = await client.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(apiResponse.body));
    return responseBody.content[0].text;
  } catch (error) {
    console.error("Error invoking model:", error);
    throw error;
  }
};
