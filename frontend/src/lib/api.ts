import { UserProfile, ResumeData, MatchRecommendation, Job } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getProfile: () => request<UserProfile>("/api/profile"),
  
  getJobs: () => request<Job[]>("/api/jobs"),
  
  updateCategory: (category: string) => 
    request<UserProfile>("/api/profile/category", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category }),
    }),
    
  uploadResume: async (file: File): Promise<ResumeData> => {
    const formData = new FormData();
    formData.append("file", file);
    return request<ResumeData>("/api/resume/upload", {
      method: "POST",
      body: formData,
    });
  },
  
  discoverJobs: () => 
    request<{ new_jobs_found: number }>("/api/jobs/discover", {
      method: "POST",
    }),
    
  getRecommendations: () => 
    request<MatchRecommendation[]>("/api/jobs/recommendations"),
};
