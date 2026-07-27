import { describe, it, expect, beforeAll, afterAll } from "vitest";
import type { Server } from "http";
import { createApp } from "./main";
import { initEventStore } from "./runtime";

let server: Server;
let baseUrl: string;

beforeAll(async () => {
  await initEventStore();
  server = createApp();
  await new Promise<void>((resolve) => server.listen(3000, () => resolve()));
  baseUrl = "http://localhost:3000";
});

afterAll(() => {
  server.close();
});

describe("Story API", () => {
  let storyId: string;

  it("should create a story", async () => {
    const response = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "Test Story", description: "Test Description", genre: "novel", authorId: "user-1" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(result.storyId).toBeDefined();
    storyId = result.storyId;
  });

  it("should get the story", async () => {
    const response = await fetch(`${baseUrl}/api/stories/${storyId}`);
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(result.data.title).toBe("Test Story");
  });

  it("should list stories", async () => {
    const response = await fetch(`${baseUrl}/api/stories`);
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(Array.isArray(result.data)).toBe(true);
    expect(result.data).toContain(storyId);
  });

  it("should update the story", async () => {
    const response = await fetch(`${baseUrl}/api/stories/${storyId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "Updated Story" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
  });

  it("should delete the story", async () => {
    const response = await fetch(`${baseUrl}/api/stories/${storyId}`, { method: "DELETE" });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
  });

  it("should return 404 for deleted story", async () => {
    const response = await fetch(`${baseUrl}/api/stories/${storyId}`);
    expect(response.status).toBe(404);
  });
});

describe("User API", () => {
  let userId: string;

  it("should create a user", async () => {
    const response = await fetch(`${baseUrl}/api/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "testuser", email: "test@example.com", displayName: "Test User" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(result.userId).toBeDefined();
    userId = result.userId;
  });

  it("should get the user", async () => {
    const response = await fetch(`${baseUrl}/api/users/${userId}`);
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(result.data.username).toBe("testuser");
  });

  it("should list users", async () => {
    const response = await fetch(`${baseUrl}/api/users`);
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(Array.isArray(result.data)).toBe(true);
    expect(result.data).toContain(userId);
  });

  it("should update the user", async () => {
    const response = await fetch(`${baseUrl}/api/users/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ displayName: "Updated User" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
  });

  it("should delete the user", async () => {
    const response = await fetch(`${baseUrl}/api/users/${userId}`, { method: "DELETE" });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
  });
});

describe("Comment API", () => {
  let commentId: string;

  it("should create a comment", async () => {
    const response = await fetch(`${baseUrl}/api/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ storyId: "story-1", content: "Test comment", userId: "user-1" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(result.commentId).toBeDefined();
    commentId = result.commentId;
  });

  it("should get the comment", async () => {
    const response = await fetch(`${baseUrl}/api/comments/${commentId}`);
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(result.data.content).toBe("Test comment");
  });

  it("should list comments", async () => {
    const response = await fetch(`${baseUrl}/api/comments`);
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
    expect(Array.isArray(result.data)).toBe(true);
    expect(result.data).toContain(commentId);
  });

  it("should update the comment", async () => {
    const response = await fetch(`${baseUrl}/api/comments/${commentId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: "Updated comment" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
  });

  it("should delete the comment", async () => {
    const response = await fetch(`${baseUrl}/api/comments/${commentId}`, { method: "DELETE" });
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.success).toBe(true);
  });
});

describe("Validation", () => {
  it("should reject invalid JSON", async () => {
    const response = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "invalid json",
    });
    const result: any = await response.json();
    expect(response.status).toBe(400);
    expect(result.success).toBe(false);
    expect(result.error).toBe("Invalid JSON format");
  });

  it("should reject missing required fields", async () => {
    const response = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "Test" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(400);
    expect(result.success).toBe(false);
  });
});

describe("Authentication", () => {
  it("should return 401 without Authorization header", async () => {
    // 临时禁用测试模式来验证认证
    const response = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Test-Mode": "false" },
      body: JSON.stringify({ title: "Test", description: "Desc", genre: "novel", authorId: "user-1" }),
    });
    const result: any = await response.json();
    expect(response.status).toBe(401);
    expect(result.success).toBe(false);
  });

  it("should return 401 with invalid token", async () => {
    const response = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer invalidtoken", "X-Test-Mode": "false" },
      body: JSON.stringify({ title: "Test", description: "Desc", genre: "novel", authorId: "user-1" }),
    });
    expect(response.status).toBe(401);
  });

  it("should allow viewer to read but not write", async () => {
    // viewer 应该可以 GET
    const getResponse = await fetch(`${baseUrl}/api/stories`, {
      method: "GET",
      headers: { "X-Test-Mode": "false", "Authorization": "Bearer viewer1:viewer" },
    });
    expect(getResponse.status).toBe(200);

    // viewer 不应该可以 POST
    const postResponse = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Test-Mode": "false", "Authorization": "Bearer viewer1:viewer" },
      body: JSON.stringify({ title: "Test", description: "Desc", genre: "novel", authorId: "user-1" }),
    });
    expect(postResponse.status).toBe(403);
  });

  it("should allow editor to write but not delete", async () => {
    // editor 可以 POST
    const postResponse = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Test-Mode": "false", "Authorization": "Bearer editor1:editor" },
      body: JSON.stringify({ title: "Editor Test", description: "Desc", genre: "novel", authorId: "user-1" }),
    });
    expect(postResponse.status).toBe(200);
    const postResult: any = await postResponse.json();
    const storyId = postResult.storyId;

    // editor 不可以 DELETE
    const deleteResponse = await fetch(`${baseUrl}/api/stories/${storyId}`, {
      method: "DELETE",
      headers: { "X-Test-Mode": "false", "Authorization": "Bearer editor1:editor" },
    });
    expect(deleteResponse.status).toBe(403);
  });

  it("should allow admin to perform all operations", async () => {
    const postResponse = await fetch(`${baseUrl}/api/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Test-Mode": "false", "Authorization": "Bearer admin1:admin" },
      body: JSON.stringify({ title: "Admin Test", description: "Desc", genre: "novel", authorId: "user-1" }),
    });
    expect(postResponse.status).toBe(200);
    const postResult: any = await postResponse.json();
    const storyId = postResult.storyId;

    const deleteResponse = await fetch(`${baseUrl}/api/stories/${storyId}`, {
      method: "DELETE",
      headers: { "X-Test-Mode": "false", "Authorization": "Bearer admin1:admin" },
    });
    expect(deleteResponse.status).toBe(200);
  });
});

describe("Health Check", () => {
  it("should return ok status", async () => {
    const response = await fetch(`${baseUrl}/api/health`);
    const result: any = await response.json();
    expect(response.status).toBe(200);
    expect(result.status).toBe("ok");
  });
});
