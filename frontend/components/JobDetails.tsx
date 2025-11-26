"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";

interface JobDetail {
  id: string;
  post_number: string;
  post_name: string;
  organization: {
    name: string;
    abbreviation: string;
  };
  location_country: string;
  location_city?: string;
  location_region?: string;
  position_level?: string;
  contract_type: string;
  contract_duration?: string;
  renewable: boolean;
  work_arrangement?: string;
  thematic_area?: string;
  application_deadline: string;
  date_posted: string;
  brief_description?: string;
  main_skills_competencies?: string;
  technical_skills?: string;
  minimum_academic_qualifications?: string;
  minimum_experience?: string;
  language_requirements: Array<{
    language: string;
    requirement_level: string;
    proficiency_level?: string;
  }>;
  tags: string[];
  source_url?: string;
  is_active: boolean;
}

interface JobDetailsProps {
  jobId: string | null;
}

export function JobDetails({ jobId }: JobDetailsProps) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }

    // TODO: Fetch job details from API
    // For now, show mock data
    setLoading(true);
    setTimeout(() => {
      setJob({
        id: jobId,
        post_number: "12345",
        post_name: "Programme Officer - Child Protection",
        organization: {
          name: "United Nations Children's Fund",
          abbreviation: "UNICEF",
        },
        location_country: "Kenya",
        location_city: "Nairobi",
        location_region: "East Africa",
        position_level: "P-3",
        contract_type: "fixed_term",
        contract_duration: "2 years",
        renewable: true,
        work_arrangement: "on-site",
        thematic_area: "Child Protection",
        application_deadline: "2025-12-31",
        date_posted: "2025-11-01",
        brief_description:
          "The Programme Officer will support UNICEF's child protection initiatives in Kenya, focusing on strengthening child protection systems and responding to emergencies.",
        main_skills_competencies:
          "Programme management, stakeholder engagement, monitoring and evaluation, policy development, capacity building",
        technical_skills:
          "Results-based management, project planning, budget management, data analysis",
        minimum_academic_qualifications:
          "Advanced university degree (Master's or equivalent) in social sciences, international development, child protection, or related field",
        minimum_experience:
          "At least 5 years of relevant professional experience in programme management and child protection",
        language_requirements: [
          {
            language: "English",
            requirement_level: "required",
            proficiency_level: "fluent",
          },
          {
            language: "Swahili",
            requirement_level: "preferred",
            proficiency_level: "intermediate",
          },
        ],
        tags: ["Child Protection", "Programme Management", "Emergency", "Kenya"],
        source_url: "https://jobs.unicef.org/12345",
        is_active: true,
      });
      setLoading(false);
    }, 300);
  }, [jobId]);

  if (!jobId) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <p className="text-gray-500 text-center">
          Select a job from the list to view details
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Loading job details...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <p className="text-gray-500">Job not found</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-start justify-between mb-2">
            <Badge variant="outline" className="mb-2">
              {job.post_number}
            </Badge>
            {job.is_active && (
              <Badge className="bg-green-500 hover:bg-green-600">Active</Badge>
            )}
          </div>
          <h1 className="text-2xl font-bold mb-2">{job.post_name}</h1>
          <p className="text-lg text-gray-700">
            {job.organization.abbreviation || job.organization.name}
          </p>
        </div>

        {/* Key Information */}
        <Card className="p-4 mb-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Location</p>
              <p className="font-medium">
                {job.location_city
                  ? `${job.location_city}, ${job.location_country}`
                  : job.location_country}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Position Level</p>
              <p className="font-medium">{job.position_level || "N/A"}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Contract Type</p>
              <p className="font-medium capitalize">
                {job.contract_type.replace("_", " ")}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Work Arrangement</p>
              <p className="font-medium capitalize">
                {job.work_arrangement || "N/A"}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Posted</p>
              <p className="font-medium">
                {new Date(job.date_posted).toLocaleDateString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Deadline</p>
              <p className="font-medium">
                {new Date(job.application_deadline).toLocaleDateString()}
              </p>
            </div>
          </div>
        </Card>

        {/* Description */}
        {job.brief_description && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Description</h2>
            <p className="text-gray-700 whitespace-pre-wrap">
              {job.brief_description}
            </p>
          </div>
        )}

        <Separator className="my-6" />

        {/* Main Skills & Competencies */}
        {job.main_skills_competencies && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">
              Main Skills & Competencies
            </h2>
            <p className="text-gray-700">{job.main_skills_competencies}</p>
          </div>
        )}

        {/* Technical Skills */}
        {job.technical_skills && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Technical Skills</h2>
            <p className="text-gray-700">{job.technical_skills}</p>
          </div>
        )}

        <Separator className="my-6" />

        {/* Qualifications */}
        {job.minimum_academic_qualifications && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">
              Academic Qualifications
            </h2>
            <p className="text-gray-700">{job.minimum_academic_qualifications}</p>
          </div>
        )}

        {/* Experience */}
        {job.minimum_experience && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Experience</h2>
            <p className="text-gray-700">{job.minimum_experience}</p>
          </div>
        )}

        <Separator className="my-6" />

        {/* Language Requirements */}
        {job.language_requirements.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">Language Requirements</h2>
            <div className="space-y-2">
              {job.language_requirements.map((lang, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Badge variant="secondary">{lang.language}</Badge>
                  <span className="text-sm text-gray-600 capitalize">
                    {lang.requirement_level}
                  </span>
                  {lang.proficiency_level && (
                    <>
                      <span className="text-gray-400">•</span>
                      <span className="text-sm text-gray-600 capitalize">
                        {lang.proficiency_level}
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {job.tags.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">Tags</h2>
            <div className="flex flex-wrap gap-2">
              {job.tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Apply Button */}
        {job.source_url && (
          <div className="mt-8">
            <Button asChild className="w-full" size="lg">
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Apply on Official Website
              </a>
            </Button>
          </div>
        )}

        {/* Contract Details */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="space-y-2 text-sm">
            {job.contract_duration && (
              <div className="flex justify-between">
                <span className="text-gray-600">Duration:</span>
                <span className="font-medium">{job.contract_duration}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-600">Renewable:</span>
              <span className="font-medium">{job.renewable ? "Yes" : "No"}</span>
            </div>
            {job.thematic_area && (
              <div className="flex justify-between">
                <span className="text-gray-600">Thematic Area:</span>
                <span className="font-medium">{job.thematic_area}</span>
              </div>
            )}
            {job.location_region && (
              <div className="flex justify-between">
                <span className="text-gray-600">Region:</span>
                <span className="font-medium">{job.location_region}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
