export interface UserProfile {
  id: string;
  email: string;
  desired_category: string | null;
  created_at: string;
}

export interface ProjectData {
  name: string;
  technologies: string[];
  description: string;
  highlights: string[];
}

export interface ExperienceData {
  company: string;
  role: string;
  start_date: string;
  end_date: string;
  duration_months: number;
  description: string;
  technologies: string[];
  highlights: string[];
}

export interface ExtractionMetrics {
  projects_detected: number;
  projects_extracted: number;
  experience_detected: number;
  experience_extracted: number;
  skills_extracted: number;
}

export interface ResumeData {
  resume_id: string;
  skills: string[];
  projects: ProjectData[];
  experience: ExperienceData[];
  education: string[];
  metrics?: ExtractionMetrics;
}


export interface MatchRecommendation {
  id: string;
  user_id: string;
  job_id: string;
  score: number;
  matching_skills: string[];
  missing_skills: string[];
  reasoning: string;
  created_at: string;
  company: string;
  role: string;
  job_url: string;
}

export interface Job {
  job_id: string;
  role: string;
  company: string;
  location: string;
  source: string;
  job_url: string;
  description: string;
  posted_at: string | null;
  discovered_at: string;
  min_requirements?: string[] | null;
  preferred_requirements?: string[] | null;
}
